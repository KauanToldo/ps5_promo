"""Renderização com Playwright (Chromium headless), só para lojas que bloqueiam requests."""
from __future__ import annotations

_pw = _browser = _ctx = None


def render(url: str, timeout_ms: int = 40000, wait_ms: int = 4000) -> str:
    """Abre a URL num navegador real e devolve o HTML renderizado."""
    global _pw, _browser, _ctx
    from playwright.sync_api import sync_playwright  # import tardio: dependência opcional

    if _browser is None:
        _pw = sync_playwright().start()
        _browser = _pw.chromium.launch(headless=True)
        _ctx = _browser.new_context(locale="pt-BR")
    page = _ctx.new_page()
    try:
        resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(wait_ms)
        if resp is not None and resp.status in (403, 429):
            raise RuntimeError(f"bloqueado ({resp.status})")
        return page.content()
    finally:
        page.close()


def close() -> None:
    global _pw, _browser, _ctx
    if _browser:
        _browser.close()
        _pw.stop()
    _pw = _browser = _ctx = None
