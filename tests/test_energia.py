"""Testa os comandos montados por EnergiaWindows com um executor falso (nada é executado)."""

import subprocess

import pytest

from desligador.plataforma.energia import EnergiaWindows, ErroEnergia


class ExecutorFalso:
    def __init__(self, codigo: int = 0, erro: str = "") -> None:
        self.comandos: list[list[str]] = []
        self._codigo = codigo
        self._erro = erro

    def __call__(self, comando, **_opcoes):
        self.comandos.append(comando)
        return subprocess.CompletedProcess(comando, self._codigo, stdout="", stderr=self._erro)


def test_agendar_forca_o_desligamento():
    executor = ExecutorFalso()
    EnergiaWindows(executor).agendar_desligamento(900)
    assert executor.comandos == [["shutdown", "/s", "/f", "/t", "900"]]


def test_cancelar_usa_shutdown_a_e_ignora_erro():
    executor = ExecutorFalso(codigo=1116, erro="nenhum desligamento em andamento")
    EnergiaWindows(executor).cancelar_desligamento()
    assert executor.comandos == [["shutdown", "/a"]]


def test_erro_ao_agendar_vira_erro_energia():
    executor = ExecutorFalso(codigo=5, erro="Acesso negado.")
    with pytest.raises(ErroEnergia, match="Acesso negado"):
        EnergiaWindows(executor).agendar_desligamento(60)
