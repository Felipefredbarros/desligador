"""Proteção contra CSRF e DNS rebinding: só aceita pedidos endereçados a este PC.

- DNS rebinding: um site malicioso faz o próprio domínio apontar para 127.0.0.1.
  O navegador continua mandando `Host: site-malicioso.com`, então validar o Host bloqueia.
- CSRF: um site malicioso envia um POST "simples" (sem preflight) para o servidor.
  Exigir `Content-Type: application/json` força o preflight CORS, que este servidor
  não atende, e o cabeçalho `Origin` denuncia a página de origem.
"""

from __future__ import annotations

import socket
from urllib.parse import urlsplit

# Nomes do MagicDNS do Tailscale (ex.: meu-pc.tail1234.ts.net). Só o Tailscale controla esse DNS.
SUFIXO_MAGICDNS = ".ts.net"


def hosts_permitidos(host_escuta: str) -> frozenset[str]:
    """Nomes pelos quais este servidor pode ser chamado legitimamente."""
    return frozenset({"localhost", "127.0.0.1", host_escuta.lower(), socket.gethostname().lower()})


def _nome(endereco: str) -> str | None:
    """Extrai o nome (sem porta, em minúsculas) de 'host', 'host:porta' ou uma URL."""
    try:
        nome = urlsplit(endereco if "//" in endereco else f"//{endereco}").hostname
    except ValueError:
        return None
    return nome or None


def host_permitido(cabecalho_host: str | None, permitidos: frozenset[str]) -> bool:
    if not cabecalho_host:
        return False
    nome = _nome(cabecalho_host)
    return nome is not None and (nome in permitidos or nome.endswith(SUFIXO_MAGICDNS))


def origem_permitida(cabecalho_origin: str | None, permitidos: frozenset[str]) -> bool:
    """Sem `Origin` (ex.: curl) é aceito; com `Origin`, ele precisa ser deste PC."""
    if cabecalho_origin is None:
        return True
    return host_permitido(cabecalho_origin, permitidos)
