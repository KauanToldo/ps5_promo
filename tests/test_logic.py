from datetime import datetime, timedelta, timezone

from messages import alert_text, brl
from models import Offer
from storage import Storage

T0 = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def mk(price, shipping=None, url="https://x/p"):
    return Offer(source="s", store="Loja", title="PS5 Slim Digital", url=url,
                 price_cash=price, shipping=shipping)


def test_total_soma_frete():
    assert mk(3700, 99.9).total == 3799.9
    assert mk(3700).total == 3700  # frete não calculado


def test_gatilho_usa_menor_preco_a_vista():
    o = Offer(source="s", store="L", title="t", url="u", price_cash=3700, price_installment=4000)
    assert o.trigger_price == 3700


def test_dedup_24h(tmp_path):
    s = Storage(tmp_path / "s.json")
    o = mk(3700)
    assert s.should_alert(o, now=T0)
    s.mark_alerted(o, now=T0)
    assert not s.should_alert(o, now=T0 + timedelta(hours=23))
    assert s.should_alert(o, now=T0 + timedelta(hours=24))


def test_preco_menor_reenvia_imediatamente(tmp_path):
    s = Storage(tmp_path / "s.json")
    s.mark_alerted(mk(3700), now=T0)
    assert s.should_alert(mk(3650), now=T0 + timedelta(minutes=30))
    assert not s.should_alert(mk(3700), now=T0 + timedelta(minutes=30))


def test_anuncio_diferente_nao_deduplica(tmp_path):
    s = Storage(tmp_path / "s.json")
    s.mark_alerted(mk(3700, url="a"), now=T0)
    assert s.should_alert(mk(3700, url="b"), now=T0)


def test_estado_persiste(tmp_path):
    p = tmp_path / "s.json"
    s = Storage(p)
    s.mark_alerted(mk(3700), now=T0)
    s.save()
    assert not Storage(p).should_alert(mk(3700), now=T0 + timedelta(hours=1))


def test_falha_avisa_uma_vez(tmp_path):
    s = Storage(tmp_path / "s.json")
    assert not s.source_result("x", False, 3, now=T0)
    assert not s.source_result("x", False, 3, now=T0 + timedelta(days=2))
    assert s.source_result("x", False, 3, now=T0 + timedelta(days=3))
    assert not s.source_result("x", False, 3, now=T0 + timedelta(days=4))
    s.source_result("x", True)
    assert "x" not in s.data["failures"]


def test_heartbeat_semanal(tmp_path):
    s = Storage(tmp_path / "s.json")
    assert s.heartbeat_due(now=T0)
    s.mark_heartbeat(now=T0)
    assert not s.heartbeat_due(now=T0 + timedelta(days=6))
    assert s.heartbeat_due(now=T0 + timedelta(days=7))


def test_mensagem_alerta():
    o = mk(3700)
    o.warnings.append("frete não calculado")
    txt = alert_text(o, 3800)
    assert "TOTAL: R$ 3.700,00" in txt and "frete não calculado" in txt
    assert brl(1234.5) == "R$ 1.234,50"
