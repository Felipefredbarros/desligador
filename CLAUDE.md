# CLAUDE.md

Guia para assistentes de IA (e humanos) trabalharem neste repositório.

## O que é
Servidor Python que roda no PC com Windows e permite **desligar, agendar ou cancelar o desligamento pelo celular**, acessando uma página web pela VPN do **Tailscale**. Detalhes em [docs/arquitetura.md](docs/arquitetura.md); o “porquê” de cada escolha está em [docs/decisoes/](docs/decisoes/).

## Mapa do código (`src/desligador/`)
| Camada | Módulo | Responsabilidade |
|---|---|---|
| entrada | `__main__.py` | Lê argumentos, configura log, monta dependências, sobe servidores |
| entrada | `trocar_pin.py` | Comando `--trocar-pin` (console, `getpass`) |
| config | `config.py` | Lê/cria/migra `%APPDATA%\Desligador\config.json` (`pin_hash`, porta) |
| api | `api/rotas.py` | Rotas JSON (login, sessão), `Dependencias`, mapeamento exceção → status HTTP |
| api | `api/servidor.py` | Transporte HTTP (stdlib), arquivos estáticos, timeout, cabeçalhos de segurança |
| api | `api/protecao.py` | Validação de `Host`/`Origin` (CSRF e DNS rebinding) |
| serviços | `servicos/desligamento.py` | Agendar / cancelar / consultar (usa `Energia` injetada) |
| serviços | `servicos/autenticacao.py` | Confere o PIN contra o hash + bloqueio por IP |
| serviços | `servicos/sessoes.py` | Sessões do cookie de login (só o SHA-256 do token fica salvo) |
| domínio | `dominio/agendamento.py` | `Agendamento`, validação de minutos (regras puras) |
| domínio | `dominio/pin.py` | Formato do PIN, geração e hash PBKDF2-SHA256 |
| plataforma | `plataforma/energia.py` | `Energia` (Protocol), `EnergiaWindows` (`shutdown /s /f`), `EnergiaFalsa` |
| plataforma | `plataforma/rede.py` | Descobre o IP do Tailscale |
| web | `web/` | Interface do celular (HTML/CSS/JS puro, sem build) |

**Regra de dependência:** `__main__` → `api` → `servicos` → `dominio` / `plataforma`. Nunca o contrário. `dominio` não importa nada do projeto. Só `__main__.py` escolhe implementações concretas.

## Comandos
```powershell
py -m venv .venv
.venv\Scripts\pip install -e ".[dev]"

.venv\Scripts\python -m pytest            # testes
.venv\Scripts\ruff check . ; .venv\Scripts\ruff format .   # lint + formatação

cd src; py -m desligador --simular       # roda sem desligar de verdade (http://localhost:8765)
cd src; py -m desligador --simular --config $env:TEMP\teste.json   # sem mexer no config real
cd src; py -m desligador --trocar-pin    # define um novo PIN
```

## Regras
1. **Nunca execute comandos de energia de verdade em testes.** Use `EnergiaFalsa`, ou `EnergiaWindows(executar=<falso>)` para conferir o comando montado. Ao rodar o servidor para testar, use `--simular`.
2. **Runtime só com biblioteca padrão.** Dependências novas só em `[project.optional-dependencies].dev`.
3. **Segredos fora do repo.** O config fica em `%APPDATA%` e guarda só o hash do PIN; nunca grave nem registre em log o PIN em texto.
4. **Não afrouxe as proteções da API** (`api/protecao.py`, exigência de JSON no POST, timeout) sem um ADR explicando o motivo.
5. **Toda mudança de comportamento vem com teste** em `tests/`. Antes de commitar: `ruff check .`, `ruff format --check .` e `pytest` passando. Nos testes, gere hashes com `gerar_hash(pin, iteracoes=1_000)` para ficarem rápidos.
6. **Decisão de arquitetura nova → ADR novo** em `docs/decisoes/NNNN-titulo.md`. Atualize o `CHANGELOG.md`.
7. **Commits** em português, [Conventional Commits](https://www.conventionalcommits.org/pt-br/): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`.
8. **Código e mensagens em português**, nomes descritivos; arquivos pequenos (~150 linhas) e com uma responsabilidade.
9. **Scripts `.ps1` só com caracteres ASCII** (o Windows PowerShell 5.1 lê arquivos sem BOM como ANSI e quebra acentos).

## Como adicionar uma nova ação (ex.: reiniciar)
1. `plataforma/energia.py`: método novo no `Protocol Energia`, em `EnergiaWindows` (`shutdown /r /f /t N`) e em `EnergiaFalsa`.
2. `servicos/desligamento.py`: método no serviço (ou um serviço novo, se a regra for diferente).
3. `api/rotas.py`: função de rota + registro em `ROTAS` (exceções novas em `_STATUS_POR_ERRO`).
4. `web/index.html` + `web/app.js`: botão chamando a rota.
5. Testes em `tests/test_energia.py`, `tests/test_desligamento.py` e `tests/test_api.py`; atualizar `README.md` e `CHANGELOG.md`.
