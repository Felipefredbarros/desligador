"""Caso de uso: verificar o PIN e bloquear quem erra demais."""

from __future__ import annotations

import hmac
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)


class PinIncorreto(PermissionError):
    """O PIN informado não confere."""


class AcessoBloqueado(PermissionError):
    """Muitas tentativas erradas; a origem está temporariamente bloqueada."""

    def __init__(self, segundos_restantes: int) -> None:
        minutos = max(1, round(segundos_restantes / 60))
        super().__init__(f"Muitas tentativas erradas. Tente de novo em {minutos} min.")
        self.segundos_restantes = segundos_restantes


@dataclass
class _Tentativas:
    erros: int = 0
    bloqueado_ate: float = 0.0


class ServicoAutenticacao:
    """Compara PINs em tempo constante e bloqueia por origem (IP) após erros seguidos."""

    def __init__(
        self,
        pin: str,
        max_erros: int = 5,
        segundos_bloqueio: float = 5 * 60,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._pin = pin.encode()
        self._max_erros = max_erros
        self._segundos_bloqueio = segundos_bloqueio
        self._relogio = relogio
        self._por_origem: dict[str, _Tentativas] = {}
        self._trava = threading.Lock()

    def verificar(self, pin: object, origem: str) -> None:
        """Não retorna nada se o PIN estiver certo; levanta exceção caso contrário."""
        with self._trava:
            agora = self._relogio()
            tentativas = self._por_origem.setdefault(origem, _Tentativas())

            if tentativas.bloqueado_ate > agora:
                raise AcessoBloqueado(round(tentativas.bloqueado_ate - agora))

            if isinstance(pin, str) and hmac.compare_digest(pin.encode(), self._pin):
                self._por_origem.pop(origem, None)
                return

            tentativas.erros += 1
            log.warning(
                "PIN incorreto vindo de %s (%s/%s)", origem, tentativas.erros, self._max_erros
            )
            if tentativas.erros >= self._max_erros:
                tentativas.erros = 0
                tentativas.bloqueado_ate = agora + self._segundos_bloqueio
                log.warning("Origem %s bloqueada por %s s", origem, self._segundos_bloqueio)
                raise AcessoBloqueado(round(self._segundos_bloqueio))
            raise PinIncorreto("PIN incorreto.")
