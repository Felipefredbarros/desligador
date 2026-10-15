"""Comando `python -m desligador --trocar-pin`: define um novo PIN pelo console."""

from __future__ import annotations

import getpass
from collections.abc import Callable
from pathlib import Path

from desligador import config
from desligador.dominio.pin import PIN_MINIMO, PinInvalido, gerar_pin, validar_pin

ARQUIVO_SESSOES = "sessoes.json"  # ao lado do config (docs/decisoes/0005)
DICA_REINICIAR = (
    "Se o Desligador já estiver rodando, reinicie-o para usar o novo PIN:\n"
    "  Stop-ScheduledTask Desligador; Start-ScheduledTask Desligador"
)


def executar(
    caminho: Path,
    ler: Callable[[str], str] = getpass.getpass,
    escrever: Callable[[str], None] = print,
) -> int:
    """Pede o PIN (sem mostrar na tela), confirma e grava só o hash. Retorna o código de saída."""
    escrever(f"Novo PIN: só números, mínimo {PIN_MINIMO} dígitos. Deixe vazio para gerar um.")
    novo = ler("Novo PIN: ").strip()

    if not novo:
        novo = gerar_pin()
        escrever(f"\nPIN gerado: {novo}\nAnote agora: ele não fica salvo em texto em lugar nenhum.")
    else:
        try:
            validar_pin(novo)
        except PinInvalido as erro:
            escrever(str(erro))
            return 1
        if ler("Repita o PIN: ").strip() != novo:
            escrever("Os PINs não conferem. Nada foi alterado.")
            return 1

    config.trocar_pin(caminho, novo)
    sessoes = caminho.with_name(ARQUIVO_SESSOES)
    if sessoes.exists():
        sessoes.unlink()
        escrever("Todas as sessões foram encerradas: entre de novo nos aparelhos.")
    escrever(f"\nPIN salvo em {caminho} (só o hash fica guardado).")
    escrever(DICA_REINICIAR)
    return 0
