"""Testes de ponta a ponta: sobe o servidor de verdade em 127.0.0.1 com EnergiaFalsa."""

import http.client
import json
import socket
import threading
import urllib.error
import urllib.request

import pytest

from desligador.api.rotas import Dependencias
from desligador.api.servidor import criar_servidor
from desligador.plataforma.energia import EnergiaFalsa
from desligador.servicos.autenticacao import ServicoAutenticacao
from desligador.servicos.desligamento import ServicoDesligamento

PIN = "12345678"
TEMPO_LIMITE_TESTE = 1  # segundos (o padrão do servidor é maior)


@pytest.fixture
def api():
    energia = EnergiaFalsa()
    deps = Dependencias(
        desligamento=ServicoDesligamento(energia),
        autenticacao=ServicoAutenticacao(PIN, max_erros=2),
    )
    servidor = criar_servidor("127.0.0.1", 0, deps, tempo_limite=TEMPO_LIMITE_TESTE)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}", energia
    servidor.shutdown()
    servidor.server_close()


def requisitar(url, corpo=None, bruto=None, cabecalhos=None):
    dados = bruto if bruto is not None else (None if corpo is None else json.dumps(corpo).encode())
    pedido = urllib.request.Request(
        url, data=dados, headers={"Content-Type": "application/json", **(cabecalhos or {})}
    )
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            return resposta.status, resposta.headers, resposta.read()
    except urllib.error.HTTPError as erro:
        return erro.code, erro.headers, erro.read()


def test_pagina_inicial_e_servida(api):
    url, _ = api
    status, cabecalhos, corpo = requisitar(url + "/")
    assert status == 200
    assert cabecalhos["Content-Type"].startswith("text/html")
    assert b"Desligador" in corpo


@pytest.mark.parametrize("caminho", ["/../config.py", "/..%2f__main__.py", "/nada.html"])
def test_nao_serve_arquivos_fora_da_pasta_web(api, caminho):
    url, _ = api
    status, _, _ = requisitar(url + caminho)
    assert status == 404


def test_status_inicial_sem_agendamento(api):
    url, _ = api
    status, _, corpo = requisitar(url + "/api/status")
    assert status == 200
    assert json.loads(corpo) == {"agendado": False, "desliga_em": None, "segundos_restantes": None}


def test_agendar_e_cancelar(api):
    url, energia = api
    status, _, corpo = requisitar(url + "/api/desligar", {"pin": PIN, "minutos": 30})
    assert status == 200
    dados = json.loads(corpo)
    assert dados["agendado"] is True
    assert 1790 <= dados["segundos_restantes"] <= 1800
    assert ("agendar", 1800) in energia.chamadas

    status, _, corpo = requisitar(url + "/api/cancelar", {"pin": PIN})
    assert status == 200
    assert json.loads(corpo)["agendado"] is False


def test_pin_errado_retorna_401_e_depois_429(api):
    url, energia = api
    status, _, corpo = requisitar(url + "/api/desligar", {"pin": "0", "minutos": 0})
    assert status == 401
    assert "erro" in json.loads(corpo)
    status, _, _ = requisitar(url + "/api/desligar", {"pin": "0", "minutos": 0})
    assert status == 429
    assert energia.chamadas == []


def test_minutos_invalidos_retorna_400(api):
    url, _ = api
    status, _, _ = requisitar(url + "/api/desligar", {"pin": PIN, "minutos": 99999})
    assert status == 400


def test_json_invalido_retorna_400(api):
    url, _ = api
    status, _, _ = requisitar(url + "/api/desligar", bruto=b"{nao e json")
    assert status == 400


@pytest.mark.parametrize("caminho", ["/", "/api/status"])
def test_host_estranho_e_recusado_dns_rebinding(api, caminho):
    url, _ = api
    status, _, _ = requisitar(url + caminho, cabecalhos={"Host": "evil.com"})
    assert status == 403


def test_origin_estranho_e_recusado_csrf(api):
    url, energia = api
    status, _, _ = requisitar(
        url + "/api/desligar", {"pin": PIN, "minutos": 0}, cabecalhos={"Origin": "http://evil.com"}
    )
    assert status == 403
    assert energia.chamadas == []


def test_post_sem_json_e_recusado_csrf(api):
    url, energia = api
    status, _, _ = requisitar(
        url + "/api/desligar",
        {"pin": PIN, "minutos": 0},
        cabecalhos={"Content-Type": "text/plain"},
    )
    assert status == 415
    assert energia.chamadas == []


def test_origin_do_proprio_pc_e_aceito(api):
    url, _ = api
    status, _, _ = requisitar(
        url + "/api/desligar", {"pin": PIN, "minutos": 30}, cabecalhos={"Origin": url}
    )
    assert status == 200


@pytest.mark.parametrize("tamanho", ["abc", "-5"])
def test_content_length_invalido_retorna_400(api, tamanho):
    url, _ = api
    porta = int(url.rsplit(":", 1)[1])
    conexao = http.client.HTTPConnection("127.0.0.1", porta, timeout=5)
    conexao.putrequest("POST", "/api/desligar")
    conexao.putheader("Content-Type", "application/json")
    conexao.putheader("Content-Length", tamanho)
    conexao.endheaders()
    assert conexao.getresponse().status == 400
    conexao.close()


def test_conexao_parada_e_encerrada_pelo_timeout(api):
    url, _ = api
    porta = int(url.rsplit(":", 1)[1])
    with socket.create_connection(("127.0.0.1", porta), timeout=TEMPO_LIMITE_TESTE + 3) as s:
        # Não envia nada: o servidor deve fechar a conexão sozinho.
        assert s.recv(1) == b""


def test_rota_desconhecida_retorna_404(api):
    url, _ = api
    status, _, _ = requisitar(url + "/api/nada")
    assert status == 404
