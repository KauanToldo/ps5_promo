from notifier.base import Notifier
from notifier.callmebot import CallMeBot
from notifier.console import ConsoleNotifier


def build_notifier(dry_run: bool) -> Notifier:
    """Escolhe o provedor. Para trocar/adicionar (Telegram, e-mail), crie uma subclasse de Notifier."""
    return ConsoleNotifier() if dry_run else CallMeBot.from_env()
