import socket

import pytest

from desligador.api.protecao import host_permitido, hosts_permitidos, origem_permitida

PERMITIDOS = hosts_permitidos("100.101.102.103")


@pytest.mark.parametrize(
    "host",
    [
        "localhost",
        "localhost:8765",
        "127.0.0.1:8765",
        "100.101.102.103:8765",
        "LOCALHOST:8765",
        f"{socket.gethostname()}:8765",
        "meu-pc.tail1234.ts.net:8765",
    ],
)
def test_aceita_hosts_deste_pc(host):
    assert host_permitido(host, PERMITIDOS)


@pytest.mark.parametrize(
    "host",
    [None, "", "evil.com", "evil.com:8765", "127.0.0.1.evil.com", "ts.net.evil.com", "[::1"],
)
def test_recusa_outros_hosts(host):
    assert not host_permitido(host, PERMITIDOS)


def test_origin_ausente_e_aceito():
    assert origem_permitida(None, PERMITIDOS)


@pytest.mark.parametrize("origin", ["http://localhost:8765", "http://100.101.102.103:8765"])
def test_origin_deste_pc_e_aceito(origin):
    assert origem_permitida(origin, PERMITIDOS)


@pytest.mark.parametrize("origin", ["http://evil.com", "null", "https://127.0.0.1.evil.com"])
def test_origin_estranho_e_recusado(origin):
    assert not origem_permitida(origin, PERMITIDOS)
