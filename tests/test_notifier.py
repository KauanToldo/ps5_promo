import pytest

import notifier
from notifier.console import ConsoleNotifier
from notifier.resend_email import ResendEmail


def test_dry_run_usa_console():
    assert isinstance(notifier.build_notifier(True), ConsoleNotifier)


def test_padrao_email(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "k")
    monkeypatch.setenv("EMAIL_TO", "a@b.c")
    monkeypatch.delenv("NOTIFIER", raising=False)
    assert isinstance(notifier.build_notifier(False), ResendEmail)


def test_email_sem_segredos(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ResendEmail.from_env()


def test_envio_monta_requisicao(monkeypatch):
    sent = {}

    class R:
        status_code = 200

    monkeypatch.setattr("notifier.resend_email.requests.post",
                        lambda url, **kw: sent.update(url=url, **kw) or R())
    ResendEmail("k", "a@b.c").send("Assunto\ncorpo")
    assert sent["json"]["subject"] == "Assunto" and sent["json"]["to"] == ["a@b.c"]
    assert sent["headers"]["Authorization"] == "Bearer k"
