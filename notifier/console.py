from notifier.base import Notifier


class ConsoleNotifier(Notifier):
    """Usado no --dry-run: só mostra o que seria enviado."""

    def send(self, text: str) -> None:
        print("\n----- [DRY-RUN] mensagem que seria enviada -----")
        print(text)
        print("------------------------------------------------")
