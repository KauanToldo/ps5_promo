"""Formatação das mensagens de WhatsApp."""
from __future__ import annotations

from zoneinfo import ZoneInfo

from models import Offer


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def alert_text(o: Offer, limit: float) -> str:
    when = o.collected_at.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    frete = brl(o.shipping) if o.shipping is not None else "não calculado"
    lines = [
        "🎮 PS5 SLIM DIGITAL ABAIXO DO LIMITE",
        f"Loja: {o.store}",
        f"Produto: {o.title}",
        f"Preço à vista: {brl(o.price_cash)}" if o.price_cash is not None else "Preço à vista: n/d",
    ]
    if o.price_installment is not None:
        lines.append(f"Preço parcelado: {brl(o.price_installment)}")
    lines += [
        f"Frete: {frete}",
        f"TOTAL: {brl(o.total)} (limite {brl(limit)})",
        f"Link: {o.url}",
        f"Coletado em: {when}",
    ]
    if o.warnings:
        lines.append("⚠️ " + "; ".join(o.warnings))
    return "\n".join(lines)


def heartbeat_text(week_min: dict | None, total_sources: int, failed: int) -> str:
    base = f"✅ Monitor PS5 ativo ({total_sources - failed}/{total_sources} fontes ok)."
    if week_min:
        return f"{base}\nMenor preço da semana: {brl(week_min['total'])} em {week_min['store']}"
    return base + "\nSem preços válidos na semana."


def physical_text(o: Offer, limit: float) -> str:
    when = o.collected_at.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    tag = "PROMOÇÃO EM LOJA FÍSICA" + ("" if o.priority == "alta" else " (VERIFICAR NA LOJA)")
    dist = (f" (~{o.distance_km:.0f} km de Concórdia, em linha reta)"
            if o.distance_km and not str(o.city).startswith("Concórdia") else "")
    lines = [tag, f"Loja: {o.store}", f"Cidade: {o.city}{dist}"]
    if o.price_cash is not None:
        lines.append(f"Preço: {brl(o.price_cash)} ({o.payment or 'pagamento não informado'})")
    else:
        lines.append(f"Preço: não identificado no post (limite {brl(limit)})")
    if o.validity:
        lines.append(f"Validade: {o.validity}")
    lines += [f"Post: {o.url}", f"Data da postagem: {o.posted}", f"Coletado em: {when}",
              "Confirme preço e estoque com a loja antes de ir."]
    if o.warnings:
        lines.append("Avisos: " + "; ".join(o.warnings))
    return "\n".join(lines)
