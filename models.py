"""Modelos de dados compartilhados."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Offer:
    source: str                 # nome da fonte (ex.: "kabum")
    store: str                  # loja vendedora (ex.: "KaBuM!")
    title: str
    url: str
    price_cash: float | None    # menor preço à vista (Pix/boleto), se conhecido
    price_installment: float | None = None  # preço parcelado, se conhecido
    shipping: float | None = None           # None = frete não calculado
    seller: str | None = None   # vendedor (marketplace)
    in_stock: bool = True
    warnings: list[str] = field(default_factory=list)
    # --- loja física (Fase 2) ---
    physical: bool = False
    city: str | None = None         # ex.: "Chapecó - SC"
    posted: str | None = None       # data do post, se conhecida
    payment: str | None = None      # "à vista", "Pix", "parcelado"
    validity: str | None = None
    priority: str = "alta"          # "alta" (preço <= limite) ou "verificar"
    distance_km: float | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def trigger_price(self) -> float | None:
        """Preço usado no gatilho: menor preço à vista real."""
        return self.price_cash if self.price_cash is not None else self.price_installment

    @property
    def total(self) -> float | None:
        p = self.trigger_price
        if p is None:
            return None
        return p + (self.shipping or 0.0)

    @property
    def offer_id(self) -> str:
        return f"{self.source}|{self.store}|{self.url}"
