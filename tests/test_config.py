import json

import pytest

from desligador import config


def test_cria_config_com_pin_aleatorio_de_8_digitos(tmp_path):
    caminho = tmp_path / "sub" / "config.json"
    cfg, criada = config.carregar_ou_criar(caminho)
    assert criada
    assert len(cfg.pin) == 8 and cfg.pin.isdigit()
    assert cfg.porta == config.PORTA_PADRAO
    assert json.loads(caminho.read_text(encoding="utf-8"))["pin"] == cfg.pin


def test_le_config_existente(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text('{"pin": "987654", "porta": 9000}', encoding="utf-8")
    cfg, criada = config.carregar_ou_criar(caminho)
    assert not criada
    assert cfg == config.Config(pin="987654", porta=9000)


@pytest.mark.parametrize(
    "dados",
    [
        {"pin": "12345"},  # curto demais
        {"pin": "abcdef"},  # não numérico
        {"pin": 123456},  # não é texto
        {"pin": "123456", "porta": 80},  # porta privilegiada
        {"pin": "123456", "porta": "8765"},
        [],
    ],
)
def test_rejeita_config_invalida(dados):
    with pytest.raises(config.ConfigInvalida):
        config.validar(dados)


def test_json_quebrado_vira_config_invalida(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text("{pin: ", encoding="utf-8")
    with pytest.raises(config.ConfigInvalida):
        config.carregar_ou_criar(caminho)
