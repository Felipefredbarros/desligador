"""Rotas da API JSON. Independente do servidor HTTP: recebe bytes, devolve `Resposta`.

Para adicionar uma rota: escreva uma função `(deps, corpo, origem) -> Resposta`
e registre-a em `ROTAS`. Exceções conhecidas viram status HTTP em `_STATUS_POR_ERRO`.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from desligador.dominio.agendamento import MinutosInvalidos
from desligador.plataforma.energia import ErroEnergia
from desligador.servicos.autenticacao import AcessoBloqueado, PinIncorreto, ServicoAutenticacao
from desligador.servicos.desligamento import ServicoDesligamento

log = logging.getLogger(__name__)


class RequisicaoInvalida(ValueError):
    """O corpo da requisição não é um JSON de objeto."""


@dataclass(frozen=True)
class Resposta:
    status: int
    dados: dict[str, Any]


@dataclass(frozen=True)
class Dependencias:
    desligamento: ServicoDesligamento
    autenticacao: ServicoAutenticacao


Rota = Callable[[Dependencias, dict[str, Any], str], Resposta]


def _estado(deps: Dependencias) -> Resposta:
    agendamento = deps.desligamento.atual()
    if agendamento is None:
        return Resposta(200, {"agendado": False, "desliga_em": None, "segundos_restantes": None})
    return Resposta(
        200,
        {
            "agendado": True,
            "desliga_em": agendamento.desliga_em.isoformat(),
            "segundos_restantes": deps.desligamento.segundos_restantes(agendamento),
        },
    )


def status(deps: Dependencias, corpo: dict[str, Any], origem: str) -> Resposta:
    return _estado(deps)


def desligar(deps: Dependencias, corpo: dict[str, Any], origem: str) -> Resposta:
    deps.autenticacao.verificar(corpo.get("pin"), origem)
    deps.desligamento.agendar(corpo.get("minutos"))
    log.info("Pedido de desligamento (%s min) vindo de %s", corpo.get("minutos"), origem)
    return _estado(deps)


def cancelar(deps: Dependencias, corpo: dict[str, Any], origem: str) -> Resposta:
    deps.autenticacao.verificar(corpo.get("pin"), origem)
    deps.desligamento.cancelar()
    log.info("Pedido de cancelamento vindo de %s", origem)
    return _estado(deps)


ROTAS: dict[tuple[str, str], Rota] = {
    ("GET", "/api/status"): status,
    ("POST", "/api/desligar"): desligar,
    ("POST", "/api/cancelar"): cancelar,
}

_STATUS_POR_ERRO: dict[type[Exception], int] = {
    RequisicaoInvalida: 400,
    MinutosInvalidos: 400,
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


def tratar(metodo: str, caminho: str, corpo: bytes, origem: str, deps: Dependencias) -> Resposta:
    rota = ROTAS.get((metodo, caminho))
    if rota is None:
        return Resposta(404, {"erro": "Rota não encontrada."})
    try:
        return rota(deps, _ler_corpo(corpo), origem)
    except tuple(_STATUS_POR_ERRO) as erro:
        return Resposta(_STATUS_POR_ERRO[type(erro)], {"erro": str(erro)})
    except Exception:
        log.exception("Erro inesperado em %s %s", metodo, caminho)
        return Resposta(500, {"erro": "Erro interno no servidor."})
