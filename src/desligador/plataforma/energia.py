"""Executores de energia: quem de fato manda o Windows desligar.

`EnergiaWindows` é a única classe do projeto que pode desligar o PC.
Testes e o modo `--simular` usam `EnergiaFalsa`.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from typing import Protocol

log = logging.getLogger(__name__)

# Evita abrir uma janela de console quando o servidor roda com pythonw.exe.
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class ErroEnergia(RuntimeError):
    """O sistema operacional recusou o comando de energia."""


class Energia(Protocol):
    def agendar_desligamento(self, segundos: int) -> None: ...

    def cancelar_desligamento(self) -> None: ...


class EnergiaWindows:
    """Usa o `shutdown.exe` do Windows.

    `executar` existe para os testes conferirem o comando sem rodá-lo de verdade.
    """

    def __init__(self, executar: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self._rodar = executar

    def agendar_desligamento(self, segundos: int) -> None:
        # /f fecha os programas sem esperar: um arquivo não salvo não trava o desligamento.
        self._executar(["shutdown", "/s", "/f", "/t", str(segundos)])

    def cancelar_desligamento(self) -> None:
        # Retorna erro quando não há desligamento pendente; isso não é um problema.
        self._executar(["shutdown", "/a"], ignorar_erro=True)

    def _executar(self, comando: list[str], ignorar_erro: bool = False) -> None:
        log.debug("Executando %s", comando)
        resultado = self._rodar(
            comando,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            creationflags=_SEM_JANELA,
        )
        if resultado.returncode != 0 and not ignorar_erro:
            detalhe = resultado.stderr.strip() or f"código {resultado.returncode}"
            raise ErroEnergia(f"O Windows recusou o comando: {detalhe}")


class EnergiaFalsa:
    """Registra os comandos em vez de executá-los. Nunca desliga nada."""

    def __init__(self) -> None:
        self.chamadas: list[tuple[str, int | None]] = []

    def agendar_desligamento(self, segundos: int) -> None:
        log.info("[simulação] desligaria em %s s", segundos)
        self.chamadas.append(("agendar", segundos))

    def cancelar_desligamento(self) -> None:
        log.info("[simulação] cancelaria o desligamento")
        self.chamadas.append(("cancelar", None))
