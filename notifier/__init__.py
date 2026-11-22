import os

from notifier.base import Notifier
from notifier.callmebot import CallMeBot
from notifier.console import ConsoleNotifier
from notifier.resend_email import ResendEmail


def build_notifier(dry_run: bool) -> Notifier:
    """Escolhe o provedor pela variável NOTIFIER (email | whatsapp). Padrão: email.

    Para adicionar outro (Telegram...), crie uma subclasse de Notifier e registre aqui.
    """
    if dry_run:
        return ConsoleNotifier()
    provider = os.environ.get("NOTIFIER", "email").lower()
    if provider == "whatsapp":
        return CallMeBot.from_env()
    return ResendEmail.from_env()
