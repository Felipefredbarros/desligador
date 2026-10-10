# CLAUDE.md

Guia para assistentes de IA (e humanos) trabalharem neste repositório.

## O que é
Servidor Python que roda no PC com Windows e permite **desligar, agendar ou cancelar o desligamento pelo celular**, acessando uma página web pela VPN do **Tailscale**. Detalhes em [docs/arquitetura.md](docs/arquitetura.md); o “porquê” de cada escolha está em [docs/decisoes/](docs/decisoes/).

## Mapa do código (`src/desligador/`)
| Camada | Módulo | Responsabilidade |
|---|---|---|
| entrada | `__main__.py` | Lê argumentos, configura log, monta dependências, sobe servidores |
| config | `config.py` | Lê/cria `%APPDATA%\Desligador\config.json` (PIN, porta) |
| api | `api/rotas.py` | Rotas JSON, `Dependencias`, mapeamento exceção → status HTTP |
| api | `api/servidor.py` | Transporte HTTP (stdlib), arquivos estáticos, cabeçalhos de segurança |
| serviços | `servicos/desligamento.py` | Agendar / cancelar / consultar (usa `Energia` injetada) |
| serviços | `servicos/autenticacao.py` | PIN em tempo constante + bloqueio por IP |
| domínio | `dominio/agendamento.py` | `Agendamento`, validação de minutos (regras puras) |
| plataforma | `plataforma/energia.py` | `Energia` (Protocol), `EnergiaWindows` (shutdown.exe), `EnergiaFalsa` |
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
```

## Regras
1. **Nunca use `EnergiaWindows` em testes** nem rode o servidor sem `--simular` ao testar. Use `EnergiaFalsa`.
2. **Runtime só com biblioteca padrão.** Dependências novas só em `[project.optional-dependencies].dev`.
3. **Segredos fora do repo.** O PIN fica em `%APPDATA%`; nunca crie `config.json` dentro do projeto, nunca registre o PIN em log.
4. **Toda mudança de comportamento vem com teste** em `tests/`. Antes de commitar: `ruff check .`, `ruff format --check .` e `pytest` passando.
5. **Decisão de arquitetura nova → ADR novo** em `docs/decisoes/NNNN-titulo.md`. Atualize o `CHANGELOG.md`.
6. **Commits** em português, [Conventional Commits](https://www.conventionalcommits.org/pt-br/): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`.
7. **Código e mensagens em português**, nomes descritivos; arquivos pequenos (~150 linhas) e com uma responsabilidade.
8. **Scripts `.ps1` só com caracteres ASCII** (o Windows PowerShell 5.1 lê arquivos sem BOM como ANSI e quebra acentos).

## Como adicionar uma nova ação (ex.: reiniciar)
1. `plataforma/energia.py`: método novo no `Protocol Energia`, em `EnergiaWindows` (`shutdown /r /t N`) e em `EnergiaFalsa`.
2. `servicos/desligamento.py`: método no serviço (ou um serviço novo, se a regra for diferente).
3. `api/rotas.py`: função de rota + registro em `ROTAS` (exceções novas em `_STATUS_POR_ERRO`).
4. `web/index.html` + `web/app.js`: botão chamando a rota.
5. Testes em `tests/test_desligamento.py` e `tests/test_api.py`; atualizar `README.md` e `CHANGELOG.md`.
