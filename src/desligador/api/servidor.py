"""Servidor HTTP (biblioteca padrão): serve a interface web e repassa /api/* para `rotas`."""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from desligador.api import rotas
from desligador.api.rotas import Dependencias, Resposta

log = logging.getLogger(__name__)

PASTA_WEB = Path(__file__).resolve().parent.parent / "web"
TAMANHO_MAXIMO_CORPO = 4096

_TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/manifest+json; charset=utf-8",
    ".svg": "image/svg+xml",
}

_CABECALHOS_SEGURANCA = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


def _arquivo_web(caminho: str) -> Path | None:
    """Resolve um caminho de URL para um arquivo de `web/`, sem permitir sair da pasta."""
    nome = "index.html" if caminho == "/" else caminho.lstrip("/")
    permitidos = {p.name: p for p in PASTA_WEB.iterdir() if p.is_file()}
    return permitidos.get(nome)


def criar_servidor(host: str, porta: int, deps: Dependencias) -> ThreadingHTTPServer:
    class Manipulador(BaseHTTPRequestHandler):
        server_version = "Desligador"
        sys_version = ""

        def do_GET(self) -> None:
            self._atender("GET")

        def do_POST(self) -> None:
            self._atender("POST")

        def _atender(self, metodo: str) -> None:
            caminho = urlsplit(self.path).path
            if metodo == "GET" and not caminho.startswith("/api/"):
                self._enviar_arquivo(caminho)
                return

            tamanho = int(self.headers.get("Content-Length") or 0)
            if tamanho > TAMANHO_MAXIMO_CORPO:
                self._enviar_json(Resposta(413, {"erro": "Requisição grande demais."}))
                return
            corpo = self.rfile.read(tamanho) if tamanho > 0 else b""
            self._enviar_json(rotas.tratar(metodo, caminho, corpo, self.client_address[0], deps))

        def _enviar_arquivo(self, caminho: str) -> None:
            arquivo = _arquivo_web(caminho)
            if arquivo is None:
                self._enviar_json(Resposta(404, {"erro": "Página não encontrada."}))
                return
            tipo = _TIPOS.get(arquivo.suffix, "application/octet-stream")
            self._enviar(200, tipo, arquivo.read_bytes())

        def _enviar_json(self, resposta: Resposta) -> None:
            conteudo = json.dumps(resposta.dados, ensure_ascii=False).encode()
            self._enviar(resposta.status, "application/json; charset=utf-8", conteudo)

        def _enviar(self, status: int, tipo: str, conteudo: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(conteudo)))
            for nome, valor in _CABECALHOS_SEGURANCA.items():
                self.send_header(nome, valor)
            self.end_headers()
            self.wfile.write(conteudo)

        def log_message(self, formato: str, *args: object) -> None:
            log.debug("%s - %s", self.client_address[0], formato % args)

    return ThreadingHTTPServer((host, porta), Manipulador)
