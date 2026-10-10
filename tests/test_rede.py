import pytest

from desligador.plataforma.rede import eh_ip_tailscale


@pytest.mark.parametrize("ip", ["100.64.0.1", "100.101.102.103", "100.127.255.254"])
def test_reconhece_ips_do_tailscale(ip):
    assert eh_ip_tailscale(ip)


@pytest.mark.parametrize("ip", ["192.168.0.10", "100.128.0.1", "100.63.255.255", "lixo", ""])
def test_ignora_outros_ips(ip):
    assert not eh_ip_tailscale(ip)
