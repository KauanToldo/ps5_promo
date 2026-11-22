from abc import ABC, abstractmethod


class Notifier(ABC):
    @abstractmethod
    def send(self, text: str, html: str | None = None) -> None:
        """Envia uma mensagem (`html` é opcional e usado só por provedores que suportam). Deve levantar exceção em caso de falha."""
