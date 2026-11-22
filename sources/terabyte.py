"""Terabyte Shop: HTML da busca (requests funciona). Marca esgotado/indisponível."""
from __future__ import annotations

import re
from urllib.parse import quote_plus

from lxml import html

from models import Offer
from sources.base import Source

BASE = "https://www.terabyteshop.com.br"


class Terabyte(Source):
    name = "terabyte"

    def parse(self, page: str) -> list[Offer]:
        doc = html.fromstring(page)
        boxes = doc.xpath('//div[@class="product-item__box"]')
        if not boxes:
            raise ValueError("nenhum produto (layout mudou ou página bloqueada)")
        offers = []
        for b in boxes:
            a = b.xpath('.//a[contains(@class,"product-item__name")]')
            if not a:
                continue
            title = (a[0].get("title") or " ".join(a[0].text_content().split())).strip()
            href = a[0].get("href", "")
            price_txt = " ".join(b.xpath('.//div[contains(@class,"product-item__new-price")]//text()'))
            m = re.search(r"R\$\s?([\d\.]+),(\d\d)", price_txt)
            sold_out = bool(b.xpath('.//*[contains(@class,"esgotadoL")]')) or "Indispon" in price_txt
            price = float(m.group(1).replace(".", "") + "." + m.group(2)) if m else None
            if price is None:
                continue
            offers.append(Offer(
                source=self.name, store="Terabyte Shop", title=title, url=BASE + href,
                price_cash=price, in_stock=not sold_out,
            ))
        return offers

    def fetch(self) -> list[Offer]:
        return self.parse(self.get(f"{BASE}/busca?str={quote_plus('ps5 slim digital')}").text)
