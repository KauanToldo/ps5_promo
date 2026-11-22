"""Monitor de preços do PS5 Slim Digital.

Uso:
  python main.py --dry-run        # roda tudo, mostra mensagens, não envia nem grava estado
  python main.py                  # execução real (Actions)
  python main.py --test-notify    # envia uma mensagem de exemplo
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import yaml

from filters import apply_rules
from messages import alert_text, brl, heartbeat_text
from notifier import build_notifier
from sources import REGISTRY, browser
from sources.base import Skip
from storage import Storage

log = logging.getLogger("monitor")


def load_config(path: str = "config.yaml") -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf8"))
    if os.environ.get("LIMITE_PRECO"):  # permite ajustar via variável do Actions
        cfg["limite_preco"] = float(os.environ["LIMITE_PRECO"])
    return cfg


def run(cfg: dict, dry_run: bool, state_path: str) -> int:
    notifier = build_notifier(dry_run)
    store = Storage(state_path)
    limit = cfg["limite_preco"]
    valid, consulted, failed = [], 0, []

    for name, enabled in cfg["fontes"].items():
        if not enabled or name not in REGISTRY:
            continue
        src = REGISTRY[name](cfg)
        try:
            try:
                raw = src.fetch()
            except Skip as why:
                log.info("%s: pulada (%s)", name, why)
                continue
            consulted += 1
            kept = [o for o in (apply_rules(o, cfg) for o in raw) if o]
            log.info("%s: %d anúncios, %d válidos", name, len(raw), len(kept))
            valid += kept
            store.source_result(name, ok=True)
        except Exception as e:  # uma fonte NUNCA derruba as outras
            consulted += 1
            failed.append(name)
            log.warning("%s: FALHOU (%s)", name, e)
            if store.source_result(name, ok=False, warn_days=cfg["falhas_para_avisar_dias"]):
                notifier.send(f"⚠️ Monitor PS5: a fonte '{name}' está falhando há "
                              f"{cfg['falhas_para_avisar_dias']}+ dias. Último erro: {e}")
        time.sleep(cfg["http"]["pausa_entre_fontes"])

    browser.close()
    # Zoom e Buscapé repetem anúncios: mantém um por (loja, título, total)
    unique = {}
    for o in sorted(valid, key=lambda o: o.total):
        unique.setdefault((o.store, o.title.lower(), o.total), o)
    valid = list(unique.values())
    store.record_prices(valid)
    sent = 0
    for o in valid:
        if o.total <= limit and store.should_alert(o, cfg["alerta_duplicado_horas"]):
            try:
                notifier.send(alert_text(o, limit))
                store.mark_alerted(o)
                sent += 1
            except Exception as e:
                log.error("falha ao enviar alerta: %s", e)

    if store.heartbeat_due(cfg["heartbeat_dias"]):
        try:
            notifier.send(heartbeat_text(store.week_min(cfg["heartbeat_dias"]), consulted, len(failed)))
            store.mark_heartbeat()
        except Exception as e:
            log.error("falha no heartbeat: %s", e)

    best = valid[0] if valid else None
    log.info("RESUMO: %d fontes consultadas, %d falharam %s, %d ofertas válidas, %d alertas, menor: %s",
             consulted, len(failed), failed, len(valid), sent,
             f"{brl(best.total)} em {best.store}" if best else "nenhuma")
    for o in valid[:10]:
        log.info("  %s | %s | %s | %s", brl(o.total), o.store, o.title[:60], o.url)
    if not dry_run:
        store.save()
    return 0 if len(failed) < consulted else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test-notify", action="store_true")
    ap.add_argument("--refresh-stores", action="store_true")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--state", default="data/state.json")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if a.refresh_stores:
        print("Fase 2 (lojas físicas) ainda não implementada.")
        return 0
    if a.test_notify:
        build_notifier(a.dry_run).send("🎮 Teste do monitor PS5: se você recebeu isto, o WhatsApp está ok.")
        return 0
    return run(load_config(a.config), a.dry_run, a.state)


if __name__ == "__main__":
    sys.exit(main())
