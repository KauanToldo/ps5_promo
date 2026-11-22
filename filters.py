"""Filtros de título e regras de elegibilidade das ofertas."""
from __future__ import annotations

import re
import unicodedata

from models import Offer


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def _has(term: str, text: str) -> bool:
    """Termo como palavra inteira (evita 'pro' casar com 'protecao')."""
    term = normalize(term).strip()
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def title_ok(title: str, cfg: dict) -> bool:
    """True se o título é PS5 Slim Digital, sem termos excluídos."""
    t = normalize(title)
    inicios = cfg.get("titulo_inicia_com")
    if inicios and not any(t.startswith(normalize(i)) for i in inicios):
        return False
    for group in cfg["incluir_todas"]:
        if not any(_has(opt, t) for opt in group.split("|")):
            return False
    return not any(_has(term, t) for term in cfg["excluir_qualquer"])


def seller_ok(offer: Offer, cfg: dict) -> bool:
    if not cfg.get("exigir_vendedor_confiavel", True):
        return True
    name = normalize(offer.seller or offer.store)
    return any(normalize(v) in name for v in cfg["vendedores_confiaveis"])


def apply_rules(offer: Offer, cfg: dict) -> Offer | None:
    """Devolve a oferta com avisos, ou None se deve ser descartada."""
    if not title_ok(offer.title, cfg["filtros"]):
        return None
    # pré-venda/reserva às vezes só aparece no link
    url = normalize(offer.url)
    if any(t in url for t in ("pre-venda", "pre venda", "reserva")):
        return None
    if not offer.in_stock or offer.trigger_price is None:
        return None
    if not seller_ok(offer, cfg):
        return None
    if offer.trigger_price < cfg["preco_suspeito_abaixo_de"]:
        offer.warnings.append("SUSPEITO, verifique se não é golpe ou erro de preço")
    if offer.shipping is None:
        offer.warnings.append("frete não calculado")
    return offer
