"""Mercado Livre via API oficial (OAuth client_credentials).

Requer app registrado em developers.mercadolivre.com.br e os Secrets ML_CLIENT_ID e
ML_CLIENT_SECRET. Sem eles a fonte é pulada (não conta como falha). O HTML do site NÃO é
usado: ele exige verificação de conta/anti-robô.
"""
from __future__ import annotations

import os

from models import Offer
from sources.base import Skip, Source

API = "https://api.mercadolibre.com"
GOOD_LEVELS = ("4_light_green", "5_green")  # reputação boa/ótima


class MercadoLivre(Source):
    name = "mercadolivre"

    def token(self) -> str:
        cid, secret = os.environ.get("ML_CLIENT_ID"), os.environ.get("ML_CLIENT_SECRET")
        if not cid or not secret:
            raise Skip("ML_CLIENT_ID/ML_CLIENT_SECRET não configurados")
        r = self.session.post(f"{API}/oauth/token", timeout=self.http["timeout"], data={
            "grant_type": "client_credentials", "client_id": cid, "client_secret": secret})
        r.raise_for_status()
        return r.json()["access_token"]

    def parse(self, results: list[dict], reputation) -> list[Offer]:
        """`reputation(seller_id)` devolve o level_id do vendedor (injetável para testes)."""
        offers = []
        for it in results:
            if it.get("condition") != "new" or not it.get("price"):
                continue
            official = bool(it.get("official_store_id"))
            seller_id = (it.get("seller") or {}).get("id")
            warnings = []
            if not official:
                level = reputation(seller_id)
                if level not in GOOD_LEVELS:
                    continue  # exige loja oficial ou vendedor com boa reputação
                warnings.append(f"vendedor terceiro (reputação {level})")
            offers.append(Offer(
                source=self.name,
                store="Mercado Livre (loja oficial)" if official else "Mercado Livre",
                title=it.get("title", ""), url=it.get("permalink", ""),
                price_cash=float(it["price"]),
                seller="oficial" if official else str(seller_id),
                in_stock=it.get("available_quantity", 1) > 0,
                warnings=warnings,
            ))
        return offers

    def fetch(self) -> list[Offer]:
        headers = {"Authorization": f"Bearer {self.token()}"}
        r = self.get(f"{API}/sites/MLB/search", params={"q": "ps5 slim digital", "limit": 50,
                                                         "condition": "new"}, headers=headers)
        cache: dict = {}

        def reputation(seller_id):
            if seller_id not in cache:
                u = self.get(f"{API}/users/{seller_id}", headers=headers).json()
                cache[seller_id] = (u.get("seller_reputation") or {}).get("level_id")
            return cache[seller_id]

        return self.parse(r.json().get("results", []), reputation)
