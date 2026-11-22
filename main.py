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
from emailhtml import alert_html, physical_html, status_html
from messages import alert_text, brl, heartbeat_text, physical_text
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


def run(cfg: dict, dry_run: bool, state_path: str, force_status: bool = False) -> int:
    notifier = build_notifier(dry_run)
    store = Storage(state_path)
    limit = cfg["limite_preco"]
    valid, consulted, failed, report = [], 0, [], []

    for name, enabled in cfg["fontes"].items():
        if not enabled or name not in REGISTRY:
            continue
        src = REGISTRY[name](cfg)
        try:
            try:
                raw = src.fetch()
            except Skip as why:
                log.info("%s: pulada (%s)", name, why)
                report.append((name, "info", f"pulada: {why}"))
                continue
            consulted += 1
            kept = [o for o in (apply_rules(o, cfg) for o in raw) if o]
            log.info("%s: %d anúncios, %d válidos", name, len(raw), len(kept))
            report.append((name, "ok", f"{len(raw)} anúncios, {len(kept)} válidos"))
            valid += kept
            store.source_result(name, ok=True)
        except Exception as e:  # uma fonte NUNCA derruba as outras
            consulted += 1
            failed.append(name)
            log.warning("%s: FALHOU (%s)", name, e)
            report.append((name, "falha", str(e)[:60]))
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
                notifier.send(alert_text(o, limit), alert_html(o, limit))
                store.mark_alerted(o)
                sent += 1
            except Exception as e:
                log.error("falha ao enviar alerta: %s", e)

    if force_status or store.heartbeat_due(cfg["heartbeat_dias"]):
        try:
            notifier.send(heartbeat_text(store.week_min(cfg["heartbeat_dias"]), consulted, len(failed)),
                          status_html(valid, limit, report, "✅ Monitor ativo (resumo semanal)"))
            if not force_status:
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


def run_locais(cfg: dict, dry_run: bool, state_path: str) -> int:
    """Fase 2: promoções de PS5 em lojas físicas (Concórdia, Chapecó, Erechim)."""
    from sources.locais import LocalSocial

    notifier = build_notifier(dry_run)
    store = Storage(state_path)
    limit = cfg["limite_preco"]
    src = LocalSocial(cfg)
    ativas = [s for s in src.stores if s.get("ativa", True) and (s.get("instagram") or s.get("facebook"))]
    try:
        offers = src.fetch()
    except Exception as e:
        log.error("lojas_locais: FALHOU (%s)", e)
        if store.source_result("lojas_locais", ok=False, warn_days=cfg["falhas_para_avisar_dias"]):
            notifier.send(f"⚠️ Monitor PS5: a coleta de lojas físicas falha há vários dias. Último erro: {e}")
        if not dry_run:
            store.save()
        return 1
    store.source_result("lojas_locais", ok=True)
    offers.sort(key=lambda o: (o.priority != "alta", o.price_cash or 1e9))
    sent = 0
    for o in offers:
        # cada post é avisado uma vez (7 dias); preço novo/menor reenvia
        if store.should_alert(o, hours=24 * cfg.get("locais", {}).get("dias_recentes", 7)):
            try:
                notifier.send(physical_text(o, limit), physical_html(o, limit))
                store.mark_alerted(o)
                sent += 1
            except Exception as e:
                log.error("falha ao enviar alerta: %s", e)
    log.info("LOJAS FÍSICAS: %d lojas com perfil, %d achados (%d alta, %d verificar), %d alertas, "
             "%d créditos Serper", len(ativas), len(offers),
             sum(o.priority == "alta" for o in offers), sum(o.priority != "alta" for o in offers),
             sent, src.serper.credits)
    for o in offers[:10]:
        log.info("  [%s] %s (%s) | %s | %s", o.priority, o.store, o.city,
                 brl(o.price_cash) if o.price_cash else "sem preço", o.url)
    if not dry_run:
        store.save()
    return 0


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test-notify", action="store_true")
    ap.add_argument("--status", action="store_true", help="envia e-mail de status agora")
    ap.add_argument("--refresh-stores", action="store_true", help="Fase 2: regera lojas_locais.yaml")
    ap.add_argument("--lojas", action="store_true", help="Fase 2: busca promoções em lojas físicas")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--state", default="data/state.json")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if a.refresh_stores:
        from localstores import refresh
        from serper import Serper
        sp = Serper()
        stores = refresh(sp)
        print(f"{len(stores)} lojas gravadas em lojas_locais.yaml ({sp.credits} créditos Serper)")
        return 0
    if a.lojas:
        return run_locais(load_config(a.config), a.dry_run, a.state if a.state != "data/state.json" else "data/state_lojas.json")
    if a.test_notify:
        build_notifier(a.dry_run).send("🎮 Teste do monitor PS5: se você recebeu isto, o WhatsApp está ok.")
        return 0
    return run(load_config(a.config), a.dry_run, a.state, a.status)


if __name__ == "__main__":
    sys.exit(main())
