"""Fase 2: lojas físicas via posts públicos indexados no Google (Instagram/Facebook).

Melhor esforço: o Google indexa só parte dos posts e com atraso. Não usa login nem contas.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from localprices import classify, parse_post_date
from localstores import load
from models import Offer
from serper import Serper

log = logging.getLogger("monitor")

# Lojas com chance real de vender console (jogos, eletro, redes). Informática/celular puros ficam de fora
# para economizar créditos do Serper (1 consulta por loja por rodada).
RELEVANT = re.compile(r"game|gamer|play|joe|eletro|eletr|magazine|magalu|havan|colombo|benoit|berlanda|"
                      r"volpato|schumann|serpal|marafim|casa nova|lojas|store|geek|world|palace|maximus|"
                      r"multiverso|mania|level|tche|mega|tecno|smart|info-?games|max ", re.I)
CITY_QUERIES = {"Concórdia - SC": "Concórdia", "Chapecó - SC": "Chapecó", "Erechim - RS": "Erechim"}


class LocalSocial:
    name = "lojas_locais"

    def __init__(self, cfg: dict, serper: Serper | None = None, stores: list[dict] | None = None):
        self.cfg = cfg
        self.serper = serper or Serper()
        self.stores = stores if stores is not None else load()

    def _to_offers(self, results, store: dict | None, city: str, net: str, now, limit, days) -> list[Offer]:
        offers = []
        for r in results:
            link = r.get("link", "")
            if "google.com/goto" in link or net.lower() not in link:
                continue  # redirecionamentos do Google / fora da rede social
            res = classify(f'{r.get("title", "")}. {r.get("snippet", "")}', limit)
            if not res:
                continue
            prio, price, warns = res
            posted = parse_post_date(r.get("date"), now)
            if posted and posted < now - timedelta(days=days):
                continue  # post antigo
            if not posted:
                # sem data o Google não garante que o post seja recente: rebaixa para "verificar"
                prio = "verificar"
                warns.append("data da postagem desconhecida: o post pode ser antigo")
            if store and store.get("rede"):
                warns.append("perfil da rede (nacional): confirme se vale na filial local")
            offers.append(Offer(
                source=self.name,
                store=store["nome"] if store else f"Perfil de {net} (veja no post)",
                title=r.get("title", "")[:120], url=link,
                price_cash=price.value if price else None,
                payment=price.payment if price else None,
                warnings=warns, physical=True, city=city,
                posted=posted.strftime("%d/%m/%Y") if posted else "data não identificada",
                priority=prio, distance_km=store.get("distancia_km") if store else None))
        return offers

    def fetch(self) -> list[Offer]:
        limit = self.cfg["limite_preco"]
        days = self.cfg.get("locais", {}).get("dias_recentes", 7)
        only_relevant = self.cfg.get("locais", {}).get("so_relevantes", True)
        now = datetime.now(timezone.utc)
        offers: list[Offer] = []
        seen: set[str] = set()

        def add(new):
            for o in new:
                if o.url not in seen:  # mesmo post por duas consultas
                    seen.add(o.url)
                    offers.append(o)

        # 1) por loja (perfil conhecido). Sem filtro de data: com ele o Google costuma devolver vazio.
        for s in self.stores:
            if not s.get("ativa", True) or (only_relevant and not RELEVANT.search(s["nome"])):
                continue
            for net, host in (("Instagram", s.get("instagram")), ("Facebook", s.get("facebook"))):
                if not host:
                    continue
                path = host.split("//")[-1].replace("www.", "")
                try:
                    results = self.serper.search(f"site:{path} ps5")
                except Exception as e:  # uma loja com erro não derruba as outras
                    log.warning("lojas_locais: %s (%s) falhou: %s", s["nome"], net, e)
                    continue
                add(self._to_offers(results, s, s["cidade"], net, now, limit, days))
        # 2) descoberta por cidade: posts que citam a cidade, de lojas que não estão na lista
        for city, short in CITY_QUERIES.items():
            for net, host in (("Instagram", "instagram.com"), ("Facebook", "facebook.com")):
                try:
                    results = self.serper.search(
                        f'site:{host} (ps5 OR "playstation 5") slim digital {short}',
                        period="m" if days > 7 else "w")
                except Exception as e:
                    log.warning("lojas_locais: busca em %s/%s falhou: %s", short, net, e)
                    continue
                add(self._to_offers(results, None, city, net, now, limit, days))
        return offers
