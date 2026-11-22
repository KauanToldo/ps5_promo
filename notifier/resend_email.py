"""E-mail via Resend (https://resend.com), pela API HTTP. Plano free: 100 e-mails/dia.

Variáveis: RESEND_API_KEY, EMAIL_TO e (opcional) EMAIL_FROM.
Sem domínio próprio verificado, use o remetente padrão `onboarding@resend.dev`, que só
consegue enviar para o e-mail da sua própria conta Resend (serve para este projeto).
"""
from __future__ import annotations

import os

import requests

from notifier.base import Notifier

API = "https://api.resend.com/emails"


class ResendEmail(Notifier):
    def __init__(self, api_key: str, to: str, sender: str = "PS5 Monitor <onboarding@resend.dev>"):
        self.api_key, self.to, self.sender = api_key, to, sender

    @classmethod
    def from_env(cls) -> "ResendEmail":
        key, to = os.environ.get("RESEND_API_KEY"), os.environ.get("EMAIL_TO")
        if not key or not to:
            raise RuntimeError("Defina RESEND_API_KEY e EMAIL_TO (veja o README).")
        return cls(key, to, os.environ.get("EMAIL_FROM") or cls.__init__.__defaults__[0])

    def send(self, text: str, html: str | None = None) -> None:
        subject = text.strip().splitlines()[0][:150]
        r = requests.post(API, timeout=30,
                          headers={"Authorization": f"Bearer {self.api_key}"},
                          json={"from": self.sender, "to": [self.to], "subject": subject,
                                "text": text, **({"html": html} if html else {})})
        if r.status_code >= 300:
            raise RuntimeError(f"Resend falhou: {r.status_code} {r.text[:200]}")
