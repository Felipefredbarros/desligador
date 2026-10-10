import json

import pytest

from desligador import config
from desligador.dominio.pin import PinInvalido, conferir, gerar_hash


def ler(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


def test_cria_config_com_hash_e_devolve_o_pin_gerado(tmp_path):
    caminho = tmp_path / "sub" / "config.json"
    cfg, pin_gerado = config.carregar_ou_criar(caminho)
    assert len(pin_gerado) == 8 and pin_gerado.isdigit()
    assert cfg.porta == config.PORTA_PADRAO
    salvo = ler(caminho)
    assert set(salvo) == {"pin_hash", "porta"}
    assert pin_gerado not in caminho.read_text(encoding="utf-8")
    assert conferir(pin_gerado, salvo["pin_hash"])


def test_le_config_existente_sem_gerar_pin(tmp_path):
    caminho = tmp_path / "config.json"
    hash_salvo = gerar_hash("987654", 1_000)
    caminho.write_text(json.dumps({"pin_hash": hash_salvo, "porta": 9000}), encoding="utf-8")
    cfg, pin_gerado = config.carregar_ou_criar(caminho)
    assert pin_gerado is None
    assert cfg == config.Config(pin_hash=hash_salvo, porta=9000)


def test_migra_pin_em_texto_da_v010_mantendo_o_mesmo_pin(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text('{"pin": "11223344", "porta": 9000}', encoding="utf-8")
    cfg, pin_gerado = config.carregar_ou_criar(caminho)
    assert pin_gerado is None
    salvo = ler(caminho)
    assert "pin" not in salvo
    assert salvo["porta"] == 9000
    assert conferir("11223344", cfg.pin_hash)


def test_migracao_recusa_pin_antigo_invalido(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text('{"pin": "123"}', encoding="utf-8")
    with pytest.raises(config.ConfigInvalida):
        config.carregar_ou_criar(caminho)


@pytest.mark.parametrize(
    "dados",
    [
        {},
        {"pin_hash": "texto-qualquer"},
        {"pin_hash": gerar_hash("123456", 1_000), "porta": 80},
        {"pin_hash": gerar_hash("123456", 1_000), "porta": "8765"},
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


def test_trocar_pin_mantem_a_porta(tmp_path):
    caminho = tmp_path / "config.json"
    config.salvar(config.Config(pin_hash=gerar_hash("111111", 1_000), porta=9000), caminho)
    cfg = config.trocar_pin(caminho, "222222")
    assert cfg.porta == 9000
    assert conferir("222222", ler(caminho)["pin_hash"])


def test_trocar_pin_cria_config_e_recupera_config_quebrado(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text("{quebrado", encoding="utf-8")
    cfg = config.trocar_pin(caminho, "333333")
    assert cfg.porta == config.PORTA_PADRAO
    assert conferir("333333", cfg.pin_hash)


def test_trocar_pin_recusa_pin_curto(tmp_path):
    with pytest.raises(PinInvalido):
        config.trocar_pin(tmp_path / "config.json", "123")
