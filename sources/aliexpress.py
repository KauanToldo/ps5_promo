"""AliExpress: busca renderizada via Playwright. Anúncios são de terceiros e importados."""
from __future__ import annotations

import re
from urllib.parse import quote_plus

from lxml import html

from models import Offer
from sources import browser
from sources.base import Source


def parse_price(text: str) -> float | None:
    m = re.search(r"R\$\s?(\d[\d\.]*(?:,\d{1,2})?)", text)
    return float(m.group(1).replace(".", "").replace(",", ".")) if m else None


class AliExpress(Source):
    name = "aliexpress"

    def parse(self, page: str) -> list[Offer]:
        doc = html.fromstring(page)
        cards = doc.xpath('//a[contains(@href,"/item/")]')
        if not cards:
            raise ValueError("nenhum resultado (bloqueio/captcha ou layout mudou)")
        offers, seen = [], set()
        for a in cards:
            href = a.get("href", "")
            m = re.search(r"/item/(\d+)", href)
            if not m or m.group(1) in seen:
                continue
            text = " ".join(a.text_content().split())
            price = parse_price(text)
            title = re.split(r"R\$", text, maxsplit=1)[0].strip()
            if price is None or not title:
                continue
            seen.add(m.group(1))
            offers.append(Offer(
                source=self.name, store="AliExpress", title=title,
                url=f"https://pt.aliexpress.com/item/{m.group(1)}.html",
                price_cash=price,
                warnings=["IMPORTAÇÃO: pode ter imposto de importação e prazo longo",
                          "vendedor terceiro não verificado, cheque a reputação"],
            ))
        return offers

    def fetch(self) -> list[Offer]:
        q = quote_plus("ps5 slim digital")
        return self.parse(browser.render(
            f"https://pt.aliexpress.com/w/wholesale-ps5-slim-digital.html?SearchText={q}",
            wait_ms=6000))
