"""Configuração do usuário (hash do PIN e porta), guardada fora do repositório.

Local padrão: %APPDATA%\\Desligador\\config.json
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from desligador.dominio.pin import PinInvalido, gerar_hash, gerar_pin, hash_valido, validar_pin

log = logging.getLogger(__name__)

PORTA_PADRAO = 8765


class ConfigInvalida(ValueError):
    """O arquivo de configuração tem valores que não podem ser usados."""


@dataclass(frozen=True)
class Config:
    pin_hash: str
    porta: int = PORTA_PADRAO


def pasta_config() -> Path:
    return Path(os.environ.get("APPDATA") or Path.home()) / "Desligador"


def pasta_logs() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Desligador"


def _validar_porta(porta: object) -> int:
    if isinstance(porta, bool) or not isinstance(porta, int) or not 1024 <= porta <= 65535:
        raise ConfigInvalida("A porta deve ser um número entre 1024 e 65535.")
    return porta


def validar(dados: object) -> Config:
    if not isinstance(dados, dict):
        raise ConfigInvalida("O arquivo de configuração deve conter um objeto JSON.")
    pin_hash = dados.get("pin_hash")
    if not hash_valido(pin_hash):
        raise ConfigInvalida("PIN ausente ou inválido. Rode `py -m desligador --trocar-pin`.")
    return Config(pin_hash=pin_hash, porta=_validar_porta(dados.get("porta", PORTA_PADRAO)))


def salvar(config: Config, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(asdict(config), indent=2) + "\n", encoding="utf-8")


def _ler_json(caminho: Path) -> object:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ConfigInvalida(f"{caminho} não é um JSON válido: {erro}") from erro


def _migrar_pin_em_texto(dados: dict, caminho: Path) -> Config:
    """Converte o config da v0.1.0 (`"pin"` em texto puro) para `"pin_hash"`. O PIN não muda."""
    try:
        pin = validar_pin(dados["pin"])
    except PinInvalido as erro:
        raise ConfigInvalida(str(erro)) from erro
    config = Config(
        pin_hash=gerar_hash(pin), porta=_validar_porta(dados.get("porta", PORTA_PADRAO))
    )
    salvar(config, caminho)
    log.info("PIN migrado para hash em %s", caminho)
    return config


def carregar_ou_criar(caminho: Path) -> tuple[Config, str | None]:
    """Lê a configuração; se não existir, cria uma com PIN aleatório.

    Retorna (config, pin_gerado). `pin_gerado` só vem preenchido quando o arquivo
    acabou de ser criado, para ser mostrado uma única vez.
    """
    if not caminho.exists():
        pin = gerar_pin()
        config = Config(pin_hash=gerar_hash(pin))
        salvar(config, caminho)
        return config, pin

    dados = _ler_json(caminho)
    if isinstance(dados, dict) and "pin" in dados and "pin_hash" not in dados:
        return _migrar_pin_em_texto(dados, caminho), None
    return validar(dados), None


def _porta_atual(caminho: Path) -> int:
    """Porta do config existente; se ele não existir ou estiver quebrado, a padrão."""
    try:
        dados = _ler_json(caminho)
        return _validar_porta(dados.get("porta", PORTA_PADRAO))  # type: ignore[union-attr]
    except (OSError, ConfigInvalida, AttributeError):
        return PORTA_PADRAO


def trocar_pin(caminho: Path, novo_pin: str) -> Config:
    """Grava o hash de `novo_pin`, mantendo a porta. Cria o arquivo se não existir."""
    config = Config(pin_hash=gerar_hash(validar_pin(novo_pin)), porta=_porta_atual(caminho))
    salvar(config, caminho)
    return config
