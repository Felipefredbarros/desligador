"""Agendamento de desligamento: quando o PC vai desligar e quanto falta."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

MINUTOS_MAXIMO = 24 * 60


class MinutosInvalidos(ValueError):
    """Quantidade de minutos ausente ou fora do intervalo permitido."""


def validar_minutos(minutos: object) -> int:
    """Garante que `minutos` é um inteiro entre 0 (agora) e 24 horas."""
    # bool é subclasse de int em Python; `true` no JSON não deve virar 1 minuto.
    if isinstance(minutos, bool) or not isinstance(minutos, int):
        raise MinutosInvalidos("Informe os minutos como um número inteiro.")
    if not 0 <= minutos <= MINUTOS_MAXIMO:
        raise MinutosInvalidos(f"Os minutos devem estar entre 0 e {MINUTOS_MAXIMO}.")
    return minutos


@dataclass(frozen=True)
class Agendamento:
    """Um desligamento marcado para um instante específico."""

    desliga_em: datetime

    @classmethod
    def daqui_a(cls, minutos: object, agora: datetime) -> Agendamento:
        return cls(desliga_em=agora + timedelta(minutes=validar_minutos(minutos)))

    def segundos_restantes(self, agora: datetime) -> int:
        return max(0, round((self.desliga_em - agora).total_seconds()))

    def expirou(self, agora: datetime) -> bool:
        return self.segundos_restantes(agora) == 0
