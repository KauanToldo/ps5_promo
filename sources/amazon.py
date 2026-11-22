"""Amazon Brasil: HTML da busca via Playwright (sem login). Pode ser barrada em IP de datacenter."""
from __future__ import annotations

import re
from urllib.parse import quote_plus

from lxml import html

from models import Offer
from sources import browser
from sources.base import Source

BASE = "https://www.amazon.com.br"


def _price(text: str) -> float | None:
    m = re.search(r"([\d\.]+),(\d\d)", text or "")
    return float(m.group(1).replace(".", "") + "." + m.group(2)) if m else None


class Amazon(Source):
    name = "amazon"

    def parse(self, page: str) -> list[Offer]:
        doc = html.fromstring(page)
        tiles = doc.xpath('//div[@data-component-type="s-search-result"]')
        if not tiles:
            raise ValueError("nenhum resultado (captcha ou layout mudou)")
        offers = []
        for t in tiles:
            asin = t.get("data-asin")
            title = " ".join(t.xpath(".//h2//text()")).strip()
            price = _price(" ".join(t.xpath('.//span[@class="a-price"]/span[@class="a-offscreen"]/text()')[:1]))
            if not asin or not title or price is None:
                continue
            offers.append(Offer(
                source=self.name, store="Amazon", title=title,
                url=f"{BASE}/dp/{asin}", price_cash=price,
                warnings=["vendedor não verificado (Amazon ou terceiro), confira na página"],
            ))
        return offers

    def fetch(self) -> list[Offer]:
        # requests é barrado por bot-check; navegador real (autorizado pelo usuário), sem burlar captcha
        return self.parse(browser.render(f"{BASE}/s?k={quote_plus('ps5 slim digital')}"))
