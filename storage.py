"""Persistência em JSON: histórico de preços, alertas enviados e falhas por fonte.

O arquivo fica em data/state.json e, no Actions, é versionado na branch `state`
(ver README). Se o estado for perdido, o pior caso é repetir um alerta.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from models import Offer

ISO = "%Y-%m-%dT%H:%M:%S%z"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Storage:
    def __init__(self, path: str | Path = "data/state.json"):
        self.path = Path(path)
        self.data = {"alerts": {}, "history": [], "failures": {}, "last_heartbeat": None}
        if self.path.exists():
            self.data.update(json.loads(self.path.read_text(encoding="utf8")))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=1), encoding="utf8")

    # --- alertas / deduplicação ---------------------------------------------
    def should_alert(self, offer: Offer, hours: int = 24, now: datetime | None = None) -> bool:
        """Mesma loja+anúncio+preço só 1x por `hours`; preço menor reenvia na hora."""
        now = now or _now()
        last = self.data["alerts"].get(offer.offer_id)
        if not last:
            return True
        if offer.total is not None and (last["total"] is None or offer.total < last["total"] - 0.005):
            return True
        sent = datetime.strptime(last["ts"], ISO)
        return now - sent >= timedelta(hours=hours)

    def mark_alerted(self, offer: Offer, now: datetime | None = None) -> None:
        now = now or _now()
        self.data["alerts"][offer.offer_id] = {"total": offer.total, "ts": now.strftime(ISO)}

    # --- histórico ----------------------------------------------------------
    def record_prices(self, offers: list[Offer], now: datetime | None = None) -> None:
        now = now or _now()
        best = min(offers, key=lambda o: o.total, default=None)
        if best is not None:
            self.data["history"].append({
                "ts": now.strftime(ISO), "total": best.total,
                "store": best.store, "url": best.url,
            })
        cutoff = now - timedelta(days=60)
        self.data["history"] = [h for h in self.data["history"]
                                if datetime.strptime(h["ts"], ISO) >= cutoff]

    def week_min(self, days: int = 7, now: datetime | None = None) -> dict | None:
        now = now or _now()
        rows = [h for h in self.data["history"]
                if datetime.strptime(h["ts"], ISO) >= now - timedelta(days=days)]
        return min(rows, key=lambda h: h["total"], default=None)

    # --- heartbeat ----------------------------------------------------------
    def heartbeat_due(self, days: int = 7, now: datetime | None = None) -> bool:
        now = now or _now()
        last = self.data["last_heartbeat"]
        return last is None or now - datetime.strptime(last, ISO) >= timedelta(days=days)

    def mark_heartbeat(self, now: datetime | None = None) -> None:
        self.data["last_heartbeat"] = (now or _now()).strftime(ISO)

    # --- falhas por fonte ---------------------------------------------------
    def source_result(self, name: str, ok: bool, warn_days: int = 3,
                      now: datetime | None = None) -> bool:
        """Registra sucesso/falha. Devolve True UMA vez quando a falha passar de warn_days."""
        now = now or _now()
        f = self.data["failures"]
        if ok:
            f.pop(name, None)
            return False
        entry = f.setdefault(name, {"since": now.strftime(ISO), "warned": False})
        long_enough = now - datetime.strptime(entry["since"], ISO) >= timedelta(days=warn_days)
        if long_enough and not entry["warned"]:
            entry["warned"] = True
            return True
        return False
