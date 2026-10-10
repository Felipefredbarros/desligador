"""Descoberta do IP do PC dentro da rede Tailscale."""

from __future__ import annotations

import ipaddress
import os
import socket
import subprocess
from pathlib import Path

# Faixa de endereços que o Tailscale distribui (CGNAT).
FAIXA_TAILSCALE = ipaddress.ip_network("100.64.0.0/10")

_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def eh_ip_tailscale(texto: str) -> bool:
    try:
        return ipaddress.ip_address(texto) in FAIXA_TAILSCALE
    except ValueError:
        return False


def descobrir_ip_tailscale() -> str | None:
    """Retorna o IPv4 do Tailscale deste PC, ou None se o Tailscale não estiver ativo."""
    return _via_cli() or _via_interfaces()


def _executaveis_tailscale() -> list[str]:
    candidatos = ["tailscale"]
    programas = os.environ.get("PROGRAMFILES")
    if programas:
        candidatos.append(str(Path(programas) / "Tailscale" / "tailscale.exe"))
    return candidatos


def _via_cli() -> str | None:
    for executavel in _executaveis_tailscale():
        try:
            resultado = subprocess.run(
                [executavel, "ip", "-4"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
                creationflags=_SEM_JANELA,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        for linha in resultado.stdout.split():
            if eh_ip_tailscale(linha):
                return linha
    return None


def _via_interfaces() -> str | None:
    try:
        enderecos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        return None
    for *_, (ip, *_porta) in enderecos:
        if eh_ip_tailscale(ip):
            return ip
    return None
