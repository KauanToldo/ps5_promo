"""Cliente mínimo da API Serper.dev (resultados do Google e Google Maps).

Usado só na Fase 2. Chave em SERPER_API_KEY. Plano free: ~2.500 créditos (search=1, maps=3).
"""
from __future__ import annotations

import os
import time

import requests

BASE = "https://google.serper.dev"


class Serper:
    def __init__(self, key: str | None = None):
        self.key = key or os.environ.get("SERPER_API_KEY")
        if not self.key:
            raise RuntimeError("Defina SERPER_API_KEY (veja o README).")
        self.credits = 0

    def _post(self, path: str, payload: dict) -> dict:
        last: Exception | None = None
        for i in range(3):
            try:
                r = requests.post(f"{BASE}/{path}", json={"gl": "br", "hl": "pt-br", **payload},
                                  headers={"X-API-KEY": self.key}, timeout=30)
                r.raise_for_status()
                data = r.json()
                self.credits += data.get("credits", 1)
                return data
            except requests.RequestException as e:
                last = e
                time.sleep(2 * (2 ** i))
        raise last  # type: ignore[misc]

    def search(self, q: str, period: str | None = None, num: int = 10) -> list[dict]:
        """`period`: 'd' dia, 'w' semana, 'm' mês (filtro de data do Google)."""
        p = {"q": q, "num": num}
        if period:
            p["tbs"] = f"qdr:{period}"
        return self._post("search", p).get("organic", [])

    def maps(self, q: str, lat: float, lng: float, zoom: int = 13) -> list[dict]:
        return self._post("maps", {"q": q, "ll": f"@{lat},{lng},{zoom}z"}).get("places", [])
