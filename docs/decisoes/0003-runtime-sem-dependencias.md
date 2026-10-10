# 0003 — Runtime só com a biblioteca padrão do Python

**Status:** aceita · **Data:** 2026-10-10

## Contexto
O servidor inicia sozinho no logon via `pythonw.exe`. Frameworks como Flask ou FastAPI exigiriam um ambiente virtual com pacotes instalados e mantidos atualizados.

## Decisão
Usar só a biblioteca padrão (`http.server`, `json`, `hmac`, `subprocess`, `logging`). Ferramentas de desenvolvimento (pytest, ruff) ficam em `[project.optional-dependencies].dev`.

## Consequências
- Basta ter o Python instalado para rodar, sem `pip install` e sem risco de um pacote quebrar a inicialização.
- Menos superfície de ataque e nenhuma dependência para atualizar.
- O roteamento é manual (`api/rotas.py`), o que é aceitável para poucas rotas. Se a API crescer muito, rever esta decisão com um novo ADR.
