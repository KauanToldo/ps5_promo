"""Interface das fontes + utilitários HTTP com retry/backoff."""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod

import requests

from models import Offer

log = logging.getLogger("monitor")


class Source(ABC):
    name = "base"

    def __init__(self, cfg: dict, session: requests.Session | None = None):
        self.cfg = cfg
        self.http = cfg["http"]
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": self.http["user_agent"],
            "Accept-Language": "pt-BR,pt;q=0.9",
        })

    def get(self, url: str, **kw) -> requests.Response:
        """GET com timeout e retry com backoff exponencial."""
        last: Exception | None = None
        for i in range(self.http["tentativas"]):
            try:
                r = self.session.get(url, timeout=self.http["timeout"], **kw)
                if r.status_code in (403, 429):
                    raise requests.HTTPError(f"bloqueado ({r.status_code})", response=r)
                r.raise_for_status()
                r.encoding = "utf-8"
                return r
            except requests.RequestException as e:
                last = e
                if isinstance(e, requests.HTTPError) and e.response is not None \
                        and e.response.status_code in (403, 404):
                    break  # não adianta insistir
                time.sleep(self.http["espera_base"] * (2 ** i))
        raise last  # type: ignore[misc]

    @abstractmethod
    def fetch(self) -> list[Offer]:
        """Devolve ofertas brutas (ainda sem filtro)."""
