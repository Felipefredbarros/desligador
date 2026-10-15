"""Sessões de login (cookie): o PIN é digitado uma vez e vira um token aleatório.

Ver docs/decisoes/0005. Só o SHA-256 de cada token fica salvo (em `sessoes.json`, ao lado
do config), então o arquivo vazado não serve para entrar.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import threading
import time
from collections.abc import Callable
from pathlib import Path

log = logging.getLogger(__name__)

DURACAO_PADRAO = 30 * 24 * 60 * 60  # 30 dias, em segundos
MAXIMO_PADRAO = 10


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class ServicoSessoes:
    def __init__(
        self,
        arquivo: Path | None,
        duracao: float = DURACAO_PADRAO,
        maximo: int = MAXIMO_PADRAO,
        relogio: Callable[[], float] = time.time,
    ) -> None:
        """`arquivo` None guarda só em memória (testes e simulação)."""
        self._arquivo = arquivo
        self._duracao = duracao
        self._maximo = maximo
        self._relogio = relogio
        self._trava = threading.Lock()
        self._expira_em: dict[str, float] = self._carregar()  # hash → instante (epoch)

    def _carregar(self) -> dict[str, float]:
        if self._arquivo is None or not self._arquivo.exists():
            return {}
        try:
            dados = json.loads(self._arquivo.read_text(encoding="utf-8"))
            return {
                str(item["hash"]): float(item["expira_em"]) for item in dados.get("sessoes", [])
            }
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as erro:
            log.warning("Sessões descartadas (arquivo inválido): %s", erro)
            return {}

    def _salvar(self) -> None:
        if self._arquivo is None:
            return
        self._arquivo.parent.mkdir(parents=True, exist_ok=True)
        dados = {"sessoes": [{"hash": h, "expira_em": e} for h, e in self._expira_em.items()]}
        temporario = self._arquivo.with_suffix(".tmp")
        temporario.write_text(json.dumps(dados, indent=2) + "\n", encoding="utf-8")
        temporario.replace(self._arquivo)

    def _limpar_expiradas(self) -> None:
        agora = self._relogio()
        self._expira_em = {h: e for h, e in self._expira_em.items() if e > agora}

    def criar(self) -> str:
        """Nova sessão. Devolve o token (vai só para o cookie; aqui fica o hash)."""
        token = secrets.token_urlsafe(32)
        with self._trava:
            self._limpar_expiradas()
            self._expira_em[_hash(token)] = self._relogio() + self._duracao
            while len(self._expira_em) > self._maximo:  # derruba a que expira primeiro
                del self._expira_em[min(self._expira_em, key=self._expira_em.__getitem__)]
            self._salvar()
        return token

    def valida(self, token: str | None) -> bool:
        if not token:
            return False
        with self._trava:
            expira_em = self._expira_em.get(_hash(token))
            return expira_em is not None and expira_em > self._relogio()

    def encerrar(self, token: str | None) -> None:
        if not token:
            return
        with self._trava:
            if self._expira_em.pop(_hash(token), None) is not None:
                self._salvar()

    @property
    def segundos_de_validade(self) -> int:
        return int(self._duracao)
