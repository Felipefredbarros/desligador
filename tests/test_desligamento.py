from datetime import UTC, datetime, timedelta

import pytest

from desligador.dominio.agendamento import MinutosInvalidos
from desligador.plataforma.energia import EnergiaFalsa
from desligador.servicos.desligamento import ServicoDesligamento


class Relogio:
    def __init__(self) -> None:
        self.agora = datetime(2026, 1, 1, 22, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.agora


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def energia():
    return EnergiaFalsa()


@pytest.fixture
def servico(energia, relogio):
    return ServicoDesligamento(energia, relogio)


def test_agendar_cancela_pendente_e_agenda_em_segundos(servico, energia):
    servico.agendar(15)
    assert energia.chamadas == [("cancelar", None), ("agendar", 900)]


def test_reagendar_substitui_o_anterior(servico, energia, relogio):
    servico.agendar(15)
    servico.agendar(60)
    assert energia.chamadas[-2:] == [("cancelar", None), ("agendar", 3600)]
    assert servico.atual().desliga_em == relogio.agora + timedelta(minutes=60)


def test_cancelar_limpa_o_agendamento(servico, energia):
    servico.agendar(15)
    servico.cancelar()
    assert servico.atual() is None
    assert energia.chamadas[-1] == ("cancelar", None)


def test_agendamento_expirado_some_do_status(servico, relogio):
    servico.agendar(1)
    relogio.agora += timedelta(minutes=5)
    assert servico.atual() is None


def test_minutos_invalidos_nao_chamam_o_windows(servico, energia):
    with pytest.raises(MinutosInvalidos):
        servico.agendar(-5)
    assert energia.chamadas == []
