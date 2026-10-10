"""Ponto de entrada: `python -m desligador`. Monta as dependências e inicia os servidores."""

from __future__ import annotations

import argparse
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from desligador import __version__, config
from desligador.api.rotas import Dependencias
from desligador.api.servidor import criar_servidor
from desligador.plataforma.energia import EnergiaFalsa, EnergiaWindows
from desligador.plataforma.rede import descobrir_ip_tailscale
from desligador.servicos.autenticacao import ServicoAutenticacao
from desligador.servicos.desligamento import ServicoDesligamento

log = logging.getLogger("desligador")

INTERVALO_BUSCA_TAILSCALE = 15  # segundos


def _ler_argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="desligador", description=__doc__)
    parser.add_argument(
        "--simular", action="store_true", help="não desliga de verdade (para testes)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=config.pasta_config() / "config.json",
        help="caminho do config.json (padrão: %%APPDATA%%\\Desligador\\config.json)",
    )
    parser.add_argument("--verbose", action="store_true", help="log detalhado")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def _configurar_log(verbose: bool) -> Path:
    pasta = config.pasta_logs()
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / "desligador.log"

    handlers: list[logging.Handler] = [
        RotatingFileHandler(arquivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    ]
    # Com pythonw.exe não existe console (sys.stderr é None).
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )
    return arquivo


def _iniciar_em_segundo_plano(host: str, porta: int, deps: Dependencias) -> None:
    servidor = criar_servidor(host, porta, deps)
    threading.Thread(target=servidor.serve_forever, name=f"http-{host}", daemon=True).start()
    log.info("Ouvindo em http://%s:%s", host, porta)


def _aguardar_tailscale(porta: int, deps: Dependencias, parar: threading.Event) -> None:
    """Fica tentando achar o IP do Tailscale (ele pode subir depois do Windows)."""
    avisou = False
    while not parar.is_set():
        ip = descobrir_ip_tailscale()
        if ip:
            try:
                _iniciar_em_segundo_plano(ip, porta, deps)
            except OSError as erro:
                log.error("Não foi possível ouvir em %s:%s: %s", ip, porta, erro)
            return
        if not avisou:
            log.warning("Tailscale não encontrado; tentando a cada %ss", INTERVALO_BUSCA_TAILSCALE)
            avisou = True
        parar.wait(INTERVALO_BUSCA_TAILSCALE)


def main(argv: list[str] | None = None) -> int:
    args = _ler_argumentos(argv)
    arquivo_log = _configurar_log(args.verbose)
    log.info("Desligador %s iniciando (log em %s)", __version__, arquivo_log)

    try:
        cfg, criada = config.carregar_ou_criar(args.config)
    except config.ConfigInvalida as erro:
        log.error("Configuração inválida: %s", erro)
        return 1
    if criada:
        log.info("Configuração criada em %s", args.config)
        if sys.stdout is not None:
            print(f"\nSeu PIN: {cfg.pin}  (guardado em {args.config})\n")

    energia = EnergiaFalsa() if args.simular else EnergiaWindows()
    if args.simular:
        log.warning("Modo simulação: o PC NÃO será desligado")

    deps = Dependencias(
        desligamento=ServicoDesligamento(energia),
        autenticacao=ServicoAutenticacao(cfg.pin),
    )

    try:
        _iniciar_em_segundo_plano("127.0.0.1", cfg.porta, deps)
    except OSError as erro:
        log.error("Não foi possível usar a porta %s (já está rodando?): %s", cfg.porta, erro)
        return 1

    parar = threading.Event()
    try:
        _aguardar_tailscale(cfg.porta, deps, parar)
        # Espera com timeout para o Ctrl+C funcionar no Windows.
        while not parar.wait(1):
            pass
    except KeyboardInterrupt:
        log.info("Encerrando")
    return 0


if __name__ == "__main__":
    sys.exit(main())
