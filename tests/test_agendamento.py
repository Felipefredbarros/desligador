from datetime import UTC, datetime, timedelta

import pytest

from desligador.dominio.agendamento import MINUTOS_MAXIMO, Agendamento, MinutosInvalidos

AGORA = datetime(2026, 1, 1, 22, 0, tzinfo=UTC)


def test_daqui_a_calcula_horario_de_desligamento():
    agendamento = Agendamento.daqui_a(30, AGORA)
    assert agendamento.desliga_em == AGORA + timedelta(minutes=30)
    assert agendamento.segundos_restantes(AGORA) == 30 * 60


def test_zero_minutos_significa_agora():
    assert Agendamento.daqui_a(0, AGORA).segundos_restantes(AGORA) == 0


@pytest.mark.parametrize("minutos", [-1, MINUTOS_MAXIMO + 1, None, "10", 1.5, True])
def test_rejeita_minutos_invalidos(minutos):
    with pytest.raises(MinutosInvalidos):
        Agendamento.daqui_a(minutos, AGORA)


def test_expira_quando_o_horario_passa():
    agendamento = Agendamento.daqui_a(1, AGORA)
    assert not agendamento.expirou(AGORA)
    assert agendamento.expirou(AGORA + timedelta(minutes=2))
    assert agendamento.segundos_restantes(AGORA + timedelta(minutes=2)) == 0
