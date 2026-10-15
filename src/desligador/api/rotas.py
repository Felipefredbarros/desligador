"""Rotas da API JSON. Independente do servidor HTTP: recebe bytes, devolve `Resposta`.

Para adicionar uma rota: escreva uma função `(deps, pedido) -> Resposta` e registre-a em
`ROTAS`. Exceções conhecidas viram status HTTP em `_STATUS_POR_ERRO`. O PIN só é conferido
em `/api/entrar`, que cria a sessão do cookie (docs/decisoes/0005); o resto exige a sessão.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from desligador.dominio.agendamento import MinutosInvalidos
from desligador.plataforma.energia import ErroEnergia
from desligador.servicos.autenticacao import AcessoBloqueado, PinIncorreto, ServicoAutenticacao
from desligador.servicos.desligamento import ServicoDesligamento
from desligador.servicos.sessoes import ServicoSessoes

log = logging.getLogger(__name__)

# Com prefixo: cookies não são separados por porta, e o LoL Remoto usa o mesmo host.
COOKIE = "desligador_sessao"


class RequisicaoInvalida(ValueError):
    """O corpo da requisição não é um JSON de objeto."""


class NaoAutenticado(PermissionError):
    """Sem sessão válida: a página pede o PIN."""


@dataclass(frozen=True)
class Pedido:
    corpo: dict[str, Any] = field(default_factory=dict)
    origem: str = ""  # IP de quem pediu
    sessao: str | None = None  # token do cookie


@dataclass(frozen=True)
class Resposta:
    status: int
    dados: dict[str, Any]
    cabecalhos: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Dependencias:
    desligamento: ServicoDesligamento
    autenticacao: ServicoAutenticacao
    sessoes: ServicoSessoes


Rota = Callable[[Dependencias, Pedido], Resposta]


def _exigir_sessao(deps: Dependencias, pedido: Pedido) -> None:
    if not deps.sessoes.valida(pedido.sessao):
        raise NaoAutenticado("Entre com o PIN.")


def _cookie(token: str, segundos: int) -> tuple[tuple[str, str], ...]:
    valor = f"{COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={segundos}"
    return (("Set-Cookie", valor),)


def _estado(deps: Dependencias) -> dict[str, Any]:
    agendamento = deps.desligamento.atual()
    if agendamento is None:
        return {"agendado": False, "desliga_em": None, "segundos_restantes": None}
    return {
        "agendado": True,
        "desliga_em": agendamento.desliga_em.isoformat(),
        "segundos_restantes": deps.desligamento.segundos_restantes(agendamento),
    }


def entrar(deps: Dependencias, pedido: Pedido) -> Resposta:
    deps.autenticacao.verificar(pedido.corpo.get("pin"), pedido.origem)
    log.info("Login vindo de %s", pedido.origem)
    token = deps.sessoes.criar()
    return Resposta(200, _estado(deps), _cookie(token, deps.sessoes.segundos_de_validade))


def sair(deps: Dependencias, pedido: Pedido) -> Resposta:
    deps.sessoes.encerrar(pedido.sessao)
    return Resposta(200, {"ok": True}, _cookie("", 0))


def status(deps: Dependencias, pedido: Pedido) -> Resposta:
    _exigir_sessao(deps, pedido)
    return Resposta(200, _estado(deps))


def desligar(deps: Dependencias, pedido: Pedido) -> Resposta:
    _exigir_sessao(deps, pedido)
    minutos = pedido.corpo.get("minutos")
    deps.desligamento.agendar(minutos)
    log.info("Pedido de desligamento (%s min) vindo de %s", minutos, pedido.origem)
    return Resposta(200, _estado(deps))


def cancelar(deps: Dependencias, pedido: Pedido) -> Resposta:
    _exigir_sessao(deps, pedido)
    deps.desligamento.cancelar()
    log.info("Pedido de cancelamento vindo de %s", pedido.origem)
    return Resposta(200, _estado(deps))


ROTAS: dict[tuple[str, str], Rota] = {
    ("POST", "/api/entrar"): entrar,
    ("POST", "/api/sair"): sair,
    ("GET", "/api/status"): status,
    ("POST", "/api/desligar"): desligar,
    ("POST", "/api/cancelar"): cancelar,
}

_STATUS_POR_ERRO: dict[type[Exception], int] = {
    RequisicaoInvalida: 400,
    MinutosInvalidos: 400,
    NaoAutenticado: 401,
    PinIncorreto: 401,
    AcessoBloqueado: 429,
    ErroEnergia: 500,
}


def _ler_corpo(corpo: bytes) -> dict[str, Any]:
    if not corpo:
        return {}
    try:
        dados = json.loads(corpo)
    except (json.JSONDecodeError, UnicodeDecodeError) as erro:
        raise RequisicaoInvalida("O corpo da requisição não é um JSON válido.") from erro
    if not isinstance(dados, dict):
        raise RequisicaoInvalida("O corpo da requisição deve ser um objeto JSON.")
    return dados


def tratar(metodo: str, caminho: str, corpo: bytes, pedido: Pedido, deps: Dependencias) -> Resposta:
    """`pedido` chega sem corpo; o corpo bruto é lido aqui (JSON inválido vira 400)."""
    rota = ROTAS.get((metodo, caminho))
    if rota is None:
        return Resposta(404, {"erro": "Rota não encontrada."})
    try:
        return rota(deps, Pedido(_ler_corpo(corpo), pedido.origem, pedido.sessao))
    except tuple(_STATUS_POR_ERRO) as erro:
        return Resposta(_STATUS_POR_ERRO[type(erro)], {"erro": str(erro)})
    except Exception:
        log.exception("Erro inesperado em %s %s", metodo, caminho)
        return Resposta(500, {"erro": "Erro interno no servidor."})
