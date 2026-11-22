"""Havan: a busca por texto é JavaScript e o requests leva 403 (usa Playwright), mas a página de categoria com ?q= traz JSON-LD
com os produtos; o preço vem da meta `product:price:amount` da página do produto."""
from __future__ import annotations

import json
import re

from filters import title_ok
from models import Offer
from sources import browser
from sources.base import Source

LIST_URL = "https://www.havan.com.br/eletronicos/games/video-games/?q=ps5"


class Havan(Source):
    name = "havan"

    def parse_list(self, page: str) -> list[tuple[str, str]]:
        found = {}
        for m in re.finditer(r'ld\+json">(.*?)</script>', page, re.S):
            try:
                data = json.loads(m.group(1))
            except ValueError:
                continue
            els = data.get("itemListElement", []) if isinstance(data, dict) else []
            for el in els if isinstance(els, list) else []:
                item = el.get("item", {}) if isinstance(el, dict) else {}
                if isinstance(item, dict) and item.get("@type") == "Product" and item.get("url"):
                    found[item["url"]] = item.get("name", "")
        return [(n, u) for u, n in found.items()]

    def parse_price(self, page: str) -> float | None:
        m = re.search(r'product:price:amount"\s+content="([\d\.]+)"', page)
        return float(m.group(1)) if m else None

    def fetch(self) -> list[Offer]:
        offers = []
        for name, url in self.parse_list(browser.render(LIST_URL, wait_ms=2000)):
            if not title_ok(name, self.cfg["filtros"]):
                continue  # evita baixar páginas de produtos que seriam descartados
            price = self.parse_price(browser.render(url, wait_ms=1000))
            if price:
                offers.append(Offer(source=self.name, store="Havan", title=name,
                                    url=url, price_cash=price))
        return offers
