"""Detecção de PS5 Slim Digital e extração de preço em textos de posts (Fase 2)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from filters import normalize

CONSOLE = re.compile(r"\b(ps5|ps 5|playstation ?5)\b")
PROMO = re.compile(r"\b(oferta|promocao|promo|queima|imperdivel|aproveite|apenas|so r|por r|r\$)")
NOT_CONSOLE = re.compile(
    r"\b(jogo|jogos|controle|dualsense|headset|capa|suporte|assinatura|psn|gift|cartao|"
    r"portal|volante|cooler|skin|midia)\b")
DISC = re.compile(r"\b(disco|leitor|bluray|blu-ray|midia fisica|com drive)\b")
USED = re.compile(r"\b(usado|usada|seminovo|seminova|recondicionado)\b")
PRO = re.compile(r"\b(pro)\b")
CASH = re.compile(r"\b(a vista|avista|pix|dinheiro|boleto)\b")
INSTALL = re.compile(r"(\d{1,2}\s?x\b|parcel|cartao|credito)")

# 3.799 | 3799,00 | 3.799,90 | 3799  (com ou sem R$)
PRICE = re.compile(r"(?:r\$\s*)?(\d{1,2}\.\d{3}(?:,\d{1,2})?|\d{4,5}(?:,\d{1,2})?)(?!\d)")


@dataclass
class Price:
    value: float
    payment: str  # "à vista", "Pix", "parcelado", "não informado"


def extract_prices(text: str) -> list[Price]:
    """Devolve preços plausíveis de console (R$ 2.000 a R$ 20.000), ignorando parcelas."""
    t = normalize(text)
    out = []
    for m in PRICE.finditer(t):
        raw = m.group(1)
        value = float(raw.replace(".", "").replace(",", "."))
        if not 2000 <= value <= 20000:
            continue
        before = t[max(0, m.start() - 14):m.start()]
        after = t[m.end():m.end() + 22]
        near = t[max(0, m.start() - 25):m.end() + 25]
        if re.search(r"\d\s?x\s*(de)?\s*(r\$)?\s*$", before):  # "12x de 399" já filtrado por faixa
            continue
        if re.match(r"\s*(em|ou)?\s*\d{1,2}\s?x", after):  # "3.799 em 12x" = total parcelado
            pay = "parcelado"
        elif "pix" in near:
            pay = "Pix"
        elif CASH.search(near):
            pay = "à vista"
        elif INSTALL.search(near):
            pay = "parcelado"
        else:
            pay = "não informado"
        out.append(Price(value, pay))
    return out


def classify(text: str, limit: float) -> tuple[str, Price | None, list[str]] | None:
    """Classifica um texto de post.

    Devolve (prioridade, preço, avisos) ou None para ignorar:
      - "alta": PS5 digital, novo, preço <= limite
      - "verificar": cita PS5 em tom promocional, sem preço legível ou sem deixar claro digital/disco
    """
    t = normalize(text)
    if not CONSOLE.search(t) or USED.search(t) or PRO.search(t):
        return None
    if NOT_CONSOLE.search(t) and not re.search(r"\bconsole\b", t):
        return None
    prices = extract_prices(text)
    cash_like = [p for p in prices if p.payment != "parcelado"] or prices
    best = min(cash_like, key=lambda p: p.value) if cash_like else None
    digital = "digital" in t and not DISC.search(t)
    warnings: list[str] = []
    if best and digital:
        if best.value <= limit:
            if "slim" not in t:
                warnings.append("o post não diz 'Slim', confirme o modelo")
            if best.payment in ("não informado", "parcelado"):
                warnings.append("condição de pagamento não clara no post")
            return "alta", best, warnings
        return None  # digital acima do limite: sem alerta
    if not PROMO.search(t):
        return None
    if best and not digital and DISC.search(t):
        return None  # versão com disco
    warnings.append("VERIFICAR NA LOJA: preço ilegível ou digital/disco não claro")
    return "verificar", best if best and best.value <= limit else None, warnings


_MONTHS = {"jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6, "jul": 7, "ago": 8,
           "set": 9, "out": 10, "nov": 11, "dez": 12}


def parse_post_date(s: str | None, now: datetime | None = None) -> datetime | None:
    """Datas do Google: '29 de out. de 2026', 'há 3 dias', '3 days ago'."""
    if not s:
        return None
    now = now or datetime.now(timezone.utc)
    t = normalize(s)
    m = re.search(r"(\d+)\s*(hora|dia|semana|minuto|hour|day|week|minute)", t)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"hora": "hours", "hour": "hours", "dia": "days", "day": "days", "semana": "weeks",
                 "week": "weeks", "minuto": "minutes", "minute": "minutes"}[unit]
        return now - timedelta(**{delta: n})
    m = re.search(r"(\d{1,2}) de ([a-z]{3})\w*\.? de (\d{4})", t)
    if m and m.group(2) in _MONTHS:
        return datetime(int(m.group(3)), _MONTHS[m.group(2)], int(m.group(1)), tzinfo=timezone.utc)
    return None
