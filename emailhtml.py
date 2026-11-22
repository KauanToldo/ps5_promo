"""Templates HTML dos e-mails (CSS inline, compatível com Gmail/Outlook)."""
from __future__ import annotations

from html import escape
from zoneinfo import ZoneInfo

from messages import brl
from models import Offer

BLUE, GREEN, AMBER, RED = "#0070d1", "#16a34a", "#d97706", "#dc2626"


def _shell(title: str, body: str, accent: str = BLUE) -> str:
    return f"""<!doctype html><html><body style="margin:0;background:#f3f4f6;font-family:Segoe UI,Arial,sans-serif;color:#111827">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:24px 12px"><tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">
<tr><td style="background:{accent};padding:22px 28px;color:#fff">
<div style="font-size:12px;letter-spacing:1.5px;opacity:.85">MONITOR PS5 SLIM DIGITAL</div>
<div style="font-size:22px;font-weight:700;margin-top:4px">{escape(title)}</div></td></tr>
<tr><td style="padding:24px 28px">{body}</td></tr>
<tr><td style="padding:14px 28px;background:#f9fafb;color:#6b7280;font-size:12px">Gerado automaticamente pelo ps5_promo · confirme preço e estoque no site da loja antes de comprar.</td></tr>
</table></td></tr></table></body></html>"""


def _badge(text: str, color: str) -> str:
    return (f'<span style="display:inline-block;background:{color}1a;color:{color};border:1px solid {color}55;'
            f'border-radius:999px;padding:3px 10px;font-size:12px;margin:2px 4px 2px 0">{escape(text)}</span>')


def alert_html(o: Offer, limit: float) -> str:
    when = o.collected_at.astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    frete = brl(o.shipping) if o.shipping is not None else "não calculado"
    badges = "".join(_badge(w, RED if "SUSPEITO" in w else AMBER) for w in o.warnings)
    parcel = (f'<div style="color:#6b7280;font-size:13px">Parcelado: {brl(o.price_installment)}</div>'
              if o.price_installment is not None else "")
    body = f"""
<div style="font-size:15px;color:#6b7280">{escape(o.store)}</div>
<div style="font-size:17px;font-weight:600;margin:2px 0 16px">{escape(o.title)}</div>
<div style="background:#ecfdf5;border:1px solid #a7f3d0;border-radius:12px;padding:16px 18px;margin-bottom:14px">
<div style="font-size:12px;color:#047857;letter-spacing:1px">TOTAL (limite {brl(limit)})</div>
<div style="font-size:34px;font-weight:800;color:{GREEN}">{brl(o.total)}</div>
<div style="font-size:13px;color:#374151">À vista: {brl(o.price_cash) if o.price_cash is not None else 'n/d'} · Frete: {frete}</div>{parcel}</div>
<div style="margin-bottom:18px">{badges}</div>
<a href="{escape(o.url)}" style="display:inline-block;background:{BLUE};color:#fff;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px">Ver oferta na loja</a>
<div style="color:#9ca3af;font-size:12px;margin-top:16px">Coletado em {when}</div>"""
    return _shell("🎮 Preço abaixo do limite!", body, GREEN)


def status_html(offers: list[Offer], limit: float, sources: list[tuple[str, str, str]],
                title: str = "Status do monitor") -> str:
    """sources: (nome, estado 'ok'|'falha'|'info', detalhe)."""
    colors = {"ok": GREEN, "falha": RED, "info": "#6b7280"}
    icon = {"ok": "●", "falha": "●", "info": "○"}
    rows = "".join(
        f'<tr><td style="padding:6px 0;font-size:14px"><span style="color:{colors[s]}">{icon[s]}</span> '
        f'<b>{escape(n)}</b></td><td style="padding:6px 0;font-size:13px;color:#6b7280;text-align:right">'
        f'{escape(d)}</td></tr>' for n, s, d in sources)
    if offers:
        best = offers[0]
        diff = best.total - limit
        verdict = (f'<div style="font-size:12px;color:#6b7280;letter-spacing:1px">MENOR PREÇO ENCONTRADO</div>'
                   f'<div style="font-size:32px;font-weight:800">{brl(best.total)}</div>'
                   f'<div style="font-size:13px;color:#6b7280">{escape(best.store)} · '
                   f'{brl(abs(diff))} {"acima" if diff > 0 else "abaixo"} do limite de {brl(limit)}</div>')
        lines = "".join(
            f'<tr><td style="padding:8px 0;border-top:1px solid #f3f4f6;font-size:13px">'
            f'<a href="{escape(o.url)}" style="color:{BLUE};text-decoration:none">{escape(o.title[:60])}</a>'
            f'<div style="color:#9ca3af;font-size:12px">{escape(o.store)}</div></td>'
            f'<td style="padding:8px 0;border-top:1px solid #f3f4f6;text-align:right;font-weight:700;font-size:14px;'
            f'white-space:nowrap">{brl(o.total)}</td></tr>' for o in offers[:8])
        listing = f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:6px">{lines}</table>'
    else:
        verdict = '<div style="font-size:16px">Nenhuma oferta válida no momento.</div>'
        listing = ""
    body = f"""
<div style="background:#f9fafb;border-radius:12px;padding:16px 18px;margin-bottom:18px">{verdict}</div>
{listing}
<div style="font-size:12px;color:#6b7280;letter-spacing:1px;margin:20px 0 4px">FONTES</div>
<table width="100%" cellpadding="0" cellspacing="0">{rows}</table>"""
    return _shell(title, body)


def physical_html(o: Offer, limit: float) -> str:
    verify = o.priority != "alta"
    accent = AMBER if verify else GREEN
    dist = (f" · ~{o.distance_km:.0f} km de Concórdia (linha reta)"
            if o.distance_km and not str(o.city).startswith("Concórdia") else "")
    price = (f'<div style="font-size:34px;font-weight:800;color:{accent}">{brl(o.price_cash)}</div>'
             f'<div style="font-size:13px;color:#374151">{escape(o.payment or "pagamento não informado")}</div>'
             if o.price_cash is not None else
             f'<div style="font-size:18px;font-weight:700;color:{accent}">Preço não identificado no post</div>'
             f'<div style="font-size:13px;color:#374151">Limite: {brl(limit)}</div>')
    badges = "".join(_badge(w, RED if "VERIFICAR" in w else AMBER) for w in o.warnings)
    rows = "".join(
        f'<tr><td style="padding:4px 0;color:#6b7280;font-size:13px">{k}</td>'
        f'<td style="padding:4px 0;font-size:13px;text-align:right">{escape(str(v))}</td></tr>'
        for k, v in (("Postado em", o.posted), ("Validade", o.validity or "não informada")))
    body = f"""
<div style="font-size:18px;font-weight:700">{escape(o.store)}</div>
<div style="font-size:13px;color:#6b7280;margin-bottom:14px">{escape(str(o.city))}{dist}</div>
<div style="background:{accent}14;border:1px solid {accent}55;border-radius:12px;padding:16px 18px;margin-bottom:14px">{price}</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px">{rows}</table>
<div style="margin-bottom:16px">{badges}</div>
<a href="{escape(o.url)}" style="display:inline-block;background:{BLUE};color:#fff;text-decoration:none;font-weight:600;padding:12px 22px;border-radius:10px">Ver post</a>
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:10px 14px;margin-top:18px;font-size:13px;color:#92400e">
Confirme preço e estoque com a loja antes de ir.</div>"""
    return _shell("PROMOÇÃO EM LOJA FÍSICA" + (" · verificar" if verify else ""), body, accent)
