"""WhatsApp via CallMeBot (gratuito, envia para o seu próprio número).

Ativação: README, seção "WhatsApp". Variáveis: CALLMEBOT_PHONE e CALLMEBOT_APIKEY.
"""
from __future__ import annotations

import os

import requests

from notifier.base import Notifier

API = "https://api.callmebot.com/whatsapp.php"


class CallMeBot(Notifier):
    def __init__(self, phone: str, apikey: str):
        self.phone, self.apikey = phone, apikey

    @classmethod
    def from_env(cls) -> "CallMeBot":
        phone, key = os.environ.get("CALLMEBOT_PHONE"), os.environ.get("CALLMEBOT_APIKEY")
        if not phone or not key:
            raise RuntimeError("Defina CALLMEBOT_PHONE e CALLMEBOT_APIKEY (veja o README).")
        return cls(phone, key)

    def send(self, text: str, html: str | None = None) -> None:
        r = requests.get(API, params={"phone": self.phone, "text": text, "apikey": self.apikey},
                         timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"CallMeBot falhou: {r.status_code} {r.text[:200]}")
