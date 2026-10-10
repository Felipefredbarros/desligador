"""Caso de uso: agendar, cancelar e consultar o desligamento."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime

from desligador.dominio.agendamento import Agendamento
from desligador.plataforma.energia import Energia

log = logging.getLogger(__name__)


def _agora() -> datetime:
    return datetime.now().astimezone()


class ServicoDesligamento:
    """Mantém o agendamento atual e repassa os comandos para a `Energia` injetada."""

    def __init__(self, energia: Energia, relogio: Callable[[], datetime] = _agora) -> None:
        self._energia = energia
        self._relogio = relogio
        self._agendamento: Agendamento | None = None
        self._trava = threading.Lock()

    def agendar(self, minutos: object) -> Agendamento:
        """Agenda o desligamento daqui a `minutos` (0 = agora), substituindo o anterior."""
        with self._trava:
            agora = self._relogio()
            agendamento = Agendamento.daqui_a(minutos, agora)
            # O Windows recusa um novo agendamento se já existir outro pendente.
            self._energia.cancelar_desligamento()
            self._energia.agendar_desligamento(agendamento.segundos_restantes(agora))
            self._agendamento = agendamento
            log.info("Desligamento agendado para %s", agendamento.desliga_em.isoformat())
            return agendamento

    def cancelar(self) -> None:
        with self._trava:
            self._energia.cancelar_desligamento()
            self._agendamento = None
            log.info("Desligamento cancelado")

    def atual(self) -> Agendamento | None:
        """Agendamento pendente, ou None se não houver (ou se o horário já passou)."""
        with self._trava:
            if self._agendamento and self._agendamento.expirou(self._relogio()):
                self._agendamento = None
            return self._agendamento

    def segundos_restantes(self, agendamento: Agendamento) -> int:
        return agendamento.segundos_restantes(self._relogio())
