"""Espera pelo Tailscale no começo do app (`esperar_tailscale`), sem tocar na rede."""

import logging
import threading

from desligador.__main__ import esperar_tailscale

IP = "100.64.0.7"


def _servidor(falhas):
    """Abre a porta só depois de `falhas` tentativas (o IP ainda não aceita conexões)."""
    tentativas = []

    def servir(ip):
        tentativas.append(ip)
        if len(tentativas) <= falhas:
            raise OSError(10049, "O endereço solicitado não é válido no contexto")

    return servir, tentativas


def test_ip_que_ainda_nao_aceita_conexoes_tenta_de_novo(caplog):
    """Boot de 15/10/2026: o desligador achou o IP, falhou ao ouvir e desistiu."""
    servir, tentativas = _servidor(falhas=2)
    with caplog.at_level(logging.WARNING):
        ip = esperar_tailscale(lambda: IP, servir, threading.Event(), intervalo=0)
    assert ip == IP
    assert tentativas == [IP, IP, IP]
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1 and "ainda não dá para ouvir" in avisos[0]  # avisa uma vez só


def test_espera_o_tailscale_aparecer():
    respostas = iter([None, None, IP])
    servir, tentativas = _servidor(falhas=0)
    assert esperar_tailscale(lambda: next(respostas), servir, threading.Event(), 0) == IP
    assert tentativas == [IP]


def test_para_quando_o_app_encerra():
    parar = threading.Event()
    parar.set()
    servir, tentativas = _servidor(falhas=0)
    assert esperar_tailscale(lambda: IP, servir, parar, intervalo=0) is None
    assert tentativas == []
