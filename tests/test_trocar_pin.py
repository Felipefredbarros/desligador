import json

from desligador import trocar_pin
from desligador.dominio.pin import conferir


def rodar(caminho, respostas):
    entradas = iter(respostas)
    saida: list[str] = []
    codigo = trocar_pin.executar(caminho, ler=lambda _: next(entradas), escrever=saida.append)
    return codigo, "\n".join(saida)


def hash_salvo(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))["pin_hash"]


def test_define_pin_digitado(tmp_path):
    caminho = tmp_path / "config.json"
    codigo, _ = rodar(caminho, ["654321", "654321"])
    assert codigo == 0
    assert conferir("654321", hash_salvo(caminho))


def test_vazio_gera_pin_e_mostra_uma_vez(tmp_path):
    caminho = tmp_path / "config.json"
    codigo, saida = rodar(caminho, [""])
    assert codigo == 0
    pin = saida.split("PIN gerado: ")[1].split()[0]
    assert conferir(pin, hash_salvo(caminho))


def test_confirmacao_diferente_nao_altera_nada(tmp_path):
    caminho = tmp_path / "config.json"
    codigo, saida = rodar(caminho, ["654321", "000000"])
    assert codigo == 1
    assert "não conferem" in saida
    assert not caminho.exists()


def test_pin_invalido_nao_altera_nada(tmp_path):
    caminho = tmp_path / "config.json"
    codigo, _ = rodar(caminho, ["12ab"])
    assert codigo == 1
    assert not caminho.exists()


def test_trocar_pin_encerra_todas_as_sessoes(tmp_path):
    caminho = tmp_path / "config.json"
    sessoes = tmp_path / "sessoes.json"
    sessoes.write_text('{"sessoes": []}', encoding="utf-8")
    codigo, saida = rodar(caminho, ["654321", "654321"])
    assert codigo == 0
    assert not sessoes.exists()
    assert "sessões foram encerradas" in saida
