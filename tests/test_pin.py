import pytest

from desligador.dominio.pin import (
    PinInvalido,
    conferir,
    gerar_hash,
    gerar_pin,
    hash_valido,
    validar_pin,
)

ITERACOES_TESTE = 1_000  # rápido nos testes; o padrão real é 600.000


def test_hash_confere_com_o_pin_certo():
    hash_salvo = gerar_hash("12345678", ITERACOES_TESTE)
    assert conferir("12345678", hash_salvo)


@pytest.mark.parametrize("tentativa", ["12345679", "", "1234567", None, 12345678])
def test_hash_nao_confere_com_outro_pin(tentativa):
    assert not conferir(tentativa, gerar_hash("12345678", ITERACOES_TESTE))


def test_hash_nao_contem_o_pin_e_usa_sal_aleatorio():
    a = gerar_hash("12345678", ITERACOES_TESTE)
    b = gerar_hash("12345678", ITERACOES_TESTE)
    assert "12345678" not in a
    assert a != b
    assert a.startswith(f"pbkdf2_sha256${ITERACOES_TESTE}$")


@pytest.mark.parametrize(
    "hash_salvo",
    [
        None,
        "",
        "12345678",
        "md5$1000$abc$def",
        "pbkdf2_sha256$0$AAAA$AAAA",
        "pbkdf2_sha256$mil$AAAA$AAAA",
        "pbkdf2_sha256$1000$nao-e-base64!$AAAA",
    ],
)
def test_hash_malformado_e_invalido_e_nunca_confere(hash_salvo):
    assert not hash_valido(hash_salvo)
    assert not conferir("12345678", hash_salvo)


def test_pin_gerado_tem_8_digitos_e_e_valido():
    pin = gerar_pin()
    assert len(pin) == 8 and pin.isdigit()
    assert validar_pin(pin) == pin


@pytest.mark.parametrize("pin", ["12345", "abcdef", "12 345", "１２３４５６", 123456, None])
def test_validar_pin_recusa_formatos_invalidos(pin):
    with pytest.raises(PinInvalido):
        validar_pin(pin)
