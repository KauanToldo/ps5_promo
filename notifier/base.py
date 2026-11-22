from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, text: str) -> None:
        """Envia uma mensagem. Deve levantar exceção em caso de falha."""
