import pytest

from desligador.dominio.pin import gerar_hash
from desligador.servicos.autenticacao import AcessoBloqueado, PinIncorreto, ServicoAutenticacao

PIN = "12345678"
PIN_HASH = gerar_hash(PIN, iteracoes=1_000)


class Relogio:
    def __init__(self) -> None:
        self.agora = 1000.0

    def __call__(self) -> float:
        return self.agora


@pytest.fixture
def relogio():
    return Relogio()


@pytest.fixture
def auth(relogio):
    return ServicoAutenticacao(PIN_HASH, max_erros=3, segundos_bloqueio=60, relogio=relogio)


def test_pin_correto_passa(auth):
    auth.verificar(PIN, "1.1.1.1")


@pytest.mark.parametrize("pin", ["00000000", "", None, 12345678, "1234567"])
def test_pin_errado_ou_invalido_falha(auth, pin):
    with pytest.raises(PinIncorreto):
        auth.verificar(pin, "1.1.1.1")


def test_bloqueia_apos_erros_seguidos_mesmo_com_pin_certo(auth):
    for _ in range(2):
        with pytest.raises(PinIncorreto):
            auth.verificar("errado", "1.1.1.1")
    with pytest.raises(AcessoBloqueado):
        auth.verificar("errado", "1.1.1.1")
    with pytest.raises(AcessoBloqueado):
        auth.verificar(PIN, "1.1.1.1")


def test_bloqueio_e_por_origem(auth):
    for _ in range(3):
        with pytest.raises((PinIncorreto, AcessoBloqueado)):
            auth.verificar("errado", "1.1.1.1")
    auth.verificar(PIN, "2.2.2.2")


def test_bloqueio_expira(auth, relogio):
    for _ in range(3):
        with pytest.raises((PinIncorreto, AcessoBloqueado)):
            auth.verificar("errado", "1.1.1.1")
    relogio.agora += 61
    auth.verificar(PIN, "1.1.1.1")


def test_acerto_zera_contagem_de_erros(auth):
    for _ in range(2):
        with pytest.raises(PinIncorreto):
            auth.verificar("errado", "1.1.1.1")
    auth.verificar(PIN, "1.1.1.1")
    for _ in range(2):
        with pytest.raises(PinIncorreto):
            auth.verificar("errado", "1.1.1.1")
