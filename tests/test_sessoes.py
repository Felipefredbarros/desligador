import json

from desligador.servicos.sessoes import ServicoSessoes


class _Relogio:
    def __init__(self):
        self.agora = 1_000_000.0

    def __call__(self):
        return self.agora


def test_criar_e_validar(tmp_path):
    sessoes = ServicoSessoes(tmp_path / "sessoes.json")
    token = sessoes.criar()
    assert sessoes.valida(token)
    assert not sessoes.valida("outro")
    assert not sessoes.valida(None)
    assert not sessoes.valida("")


def test_arquivo_guarda_so_o_hash_e_sobrevive_a_reinicio(tmp_path):
    arquivo = tmp_path / "sessoes.json"
    token = ServicoSessoes(arquivo).criar()
    assert token not in arquivo.read_text(encoding="utf-8")
    assert ServicoSessoes(arquivo).valida(token)


def test_expira(tmp_path):
    relogio = _Relogio()
    sessoes = ServicoSessoes(tmp_path / "s.json", duracao=60, relogio=relogio)
    token = sessoes.criar()
    relogio.agora += 59
    assert sessoes.valida(token)
    relogio.agora += 2
    assert not sessoes.valida(token)


def test_limite_derruba_a_mais_antiga(tmp_path):
    relogio = _Relogio()
    sessoes = ServicoSessoes(tmp_path / "s.json", maximo=2, relogio=relogio)
    primeira = sessoes.criar()
    relogio.agora += 1
    segunda = sessoes.criar()
    relogio.agora += 1
    terceira = sessoes.criar()
    assert not sessoes.valida(primeira)
    assert sessoes.valida(segunda) and sessoes.valida(terceira)


def test_encerrar(tmp_path):
    arquivo = tmp_path / "s.json"
    sessoes = ServicoSessoes(arquivo)
    token = sessoes.criar()
    sessoes.encerrar(token)
    sessoes.encerrar(token)  # de novo não quebra
    sessoes.encerrar(None)
    assert not sessoes.valida(token)
    assert json.loads(arquivo.read_text(encoding="utf-8")) == {"sessoes": []}


def test_arquivo_quebrado_comeca_vazio(tmp_path):
    arquivo = tmp_path / "s.json"
    arquivo.write_text("{lixo", encoding="utf-8")
    sessoes = ServicoSessoes(arquivo)
    assert sessoes.valida(sessoes.criar())
    arquivo.write_text('{"sessoes": [{"hash": 1}]}', encoding="utf-8")
    assert not ServicoSessoes(arquivo).valida("x")


def test_so_em_memoria():
    sessoes = ServicoSessoes(None)
    assert sessoes.valida(sessoes.criar())
