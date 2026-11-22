"""KaBuM!: busca com dados embutidos em __NEXT_DATA__."""
from __future__ import annotations

from models import Offer
from sources._nextdata import next_data
from sources.base import Source

BASE = "https://www.kabum.com.br"


class Kabum(Source):
    name = "kabum"

    def parse(self, html: str) -> list[Offer]:
        items = next_data(html)["props"]["pageProps"]["data"]["catalogServer"]["data"]
        offers = []
        for p in items:
            seller = p.get("sellerName") or "KaBuM!"
            cash = p.get("priceWithDiscount") or p.get("price")  # desconto = Pix/à vista
            installment = p.get("price")
            if not cash:
                continue
            offers.append(Offer(
                source=self.name, store="KaBuM!" if seller == "KaBuM!" else f"KaBuM! (vendedor {seller})",
                title=p.get("name", ""),
                url=f"{BASE}/produto/{p['code']}/{p.get('friendlyName', '')}",
                price_cash=float(cash),
                price_installment=float(installment) if installment else None,
                seller=seller,
                in_stock=bool(p.get("available")) and not p.get("preOrderDate"),
            ))
        return offers

    def fetch(self) -> list[Offer]:
        return self.parse(self.get(f"{BASE}/busca/ps5-slim-digital").text)
