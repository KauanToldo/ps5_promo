"""Zoom e Buscapé (mesma plataforma): lista produtos com o menor preço entre lojas."""
from __future__ import annotations

from urllib.parse import quote_plus

from models import Offer
from sources._nextdata import next_data
from sources.base import Source


class _Aggregator(Source):
    base = ""

    def parse(self, html: str) -> list[Offer]:
        data = next_data(html)
        hits = data["props"]["initialReduxState"]["hits"]["hits"]
        offers = []
        for h in hits:
            price = h.get("price")
            if not price:
                continue
            store = (h.get("bestOffer") or {}).get("merchantName") or "?"
            url = h.get("url", "")
            if url.startswith("/"):
                url = self.base + url
            offers.append(Offer(
                source=self.name, store=store,
                title=(h.get("name") or "").strip(),
                url=url,
                # O agregador não diz se o preço é Pix ou parcelado: tratamos como
                # preço de vitrine e avisamos no alerta.
                price_cash=float(price),
                warnings=["preço de agregador, confirme Pix/parcelado na loja"],
            ))
        return offers

    def fetch(self) -> list[Offer]:
        q = quote_plus("ps5 slim digital")
        return self.parse(self.get(f"{self.base}/search?q={q}").text)


class Zoom(_Aggregator):
    name = "zoom"
    base = "https://www.zoom.com.br"


class Buscape(_Aggregator):
    name = "buscape"
    base = "https://www.buscape.com.br"
