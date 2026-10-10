"""Configuração do usuário (PIN e porta), guardada fora do repositório.

Local padrão: %APPDATA%\\Desligador\\config.json
"""

from __future__ import annotations

import json
import os
import secrets
import string
from dataclasses import asdict, dataclass
from pathlib import Path

PIN_MINIMO = 6
DIGITOS_PIN_GERADO = 8
PORTA_PADRAO = 8765


class ConfigInvalida(ValueError):
    """O arquivo de configuração tem valores que não podem ser usados."""


@dataclass(frozen=True)
class Config:
    pin: str
    porta: int = PORTA_PADRAO


def pasta_config() -> Path:
    return Path(os.environ.get("APPDATA") or Path.home()) / "Desligador"


def pasta_logs() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "Desligador"


def gerar_pin(digitos: int = DIGITOS_PIN_GERADO) -> str:
    return "".join(secrets.choice(string.digits) for _ in range(digitos))


def validar(dados: object) -> Config:
    if not isinstance(dados, dict):
        raise ConfigInvalida("O arquivo de configuração deve conter um objeto JSON.")

    pin = dados.get("pin")
    if not (isinstance(pin, str) and pin.isascii() and pin.isdigit() and len(pin) >= PIN_MINIMO):
        raise ConfigInvalida(f"O PIN deve ter pelo menos {PIN_MINIMO} dígitos (só números).")

    porta = dados.get("porta", PORTA_PADRAO)
    if isinstance(porta, bool) or not isinstance(porta, int) or not 1024 <= porta <= 65535:
        raise ConfigInvalida("A porta deve ser um número entre 1024 e 65535.")

    return Config(pin=pin, porta=porta)


def salvar(config: Config, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(asdict(config), indent=2) + "\n", encoding="utf-8")


def carregar_ou_criar(caminho: Path) -> tuple[Config, bool]:
    """Lê a configuração; se não existir, cria uma com PIN aleatório.

    Retorna (config, criada_agora).
    """
    if not caminho.exists():
        config = Config(pin=gerar_pin())
        salvar(config, caminho)
        return config, True

    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ConfigInvalida(f"{caminho} não é um JSON válido: {erro}") from erro
    return validar(dados), False
