# Desligador

[![CI](https://github.com/Felipefredbarros/desligador/actions/workflows/ci.yml/badge.svg)](https://github.com/Felipefredbarros/desligador/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Windows](https://img.shields.io/badge/plataforma-Windows-0078D6)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

Desligue seu PC com Windows **pelo celular**, de casa ou de qualquer lugar, de forma segura.

- ⏻ **Desligar agora** ou **agendar** (15 min, 30 min, 1 h, 2 h ou quantos minutos quiser)
- ⏱️ Contagem regressiva e botão de **cancelar**
- 🔒 Acesso só pela sua rede privada do **Tailscale** + **PIN** com bloqueio contra tentativas
- 📱 Página web que vira “app” na tela inicial do celular (Android e iPhone)
- 🪶 Servidor em Python **sem dependências**, inicia sozinho e invisível com o Windows

## Como funciona

```
Celular ──(Tailscale, criptografado)──▶ PC: servidor Python ──▶ shutdown.exe
```

O PC roda um pequeno servidor HTTP que só aceita conexões vindas da sua rede do [Tailscale](https://tailscale.com). O celular abre a página, você digita o PIN e escolhe a ação. Detalhes em [docs/arquitetura.md](docs/arquitetura.md).

## Requisitos

- Windows 10 ou 11
- [Python 3.11+](https://www.python.org/downloads/)
- [Tailscale](https://tailscale.com/download) no PC **e** no celular, logado na mesma conta (gratuito)

## Instalação

**1. Tailscale:** instale no PC e no celular e entre com a mesma conta. No app do celular, confira se o PC aparece na lista.

**2. Baixe o projeto:**
```powershell
git clone https://github.com/Felipefredbarros/desligador.git
cd desligador
```

**3. (Opcional) Teste sem desligar nada:**
```powershell
cd src
py -m desligador --simular
```
Abra http://localhost:8765. O PIN aparece no terminal na primeira execução. Para sair, use `Ctrl+C`.

**4. Instale para iniciar com o Windows** (PowerShell **como Administrador**, na pasta do projeto):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
```
O script mostra o **PIN** e o endereço para usar no celular.

**5. No celular:** com o Tailscale ligado, abra `http://NOME-DO-PC:8765` (ou `http://100.x.y.z:8765`, o IP que aparece no app do Tailscale). Depois use **“Adicionar à tela inicial”** no menu do navegador.

## Segurança

| Camada | O que faz |
|---|---|
| Tailscale | Só os seus aparelhos enxergam o PC; o tráfego é criptografado (WireGuard). Nada fica exposto na internet. |
| Endereço de escuta | O servidor ouve só em `127.0.0.1` e no IP do Tailscale, nunca no Wi-Fi comum. |
| Firewall | A porta 8765 só aceita a faixa do Tailscale (`100.64.0.0/10`). |
| PIN | 8 dígitos aleatórios, comparação em tempo constante, bloqueio de 5 min após 5 erros. |
| Segredos | O PIN fica em `%APPDATA%\Desligador\config.json`, fora do repositório. |

**Trocar o PIN:** edite `%APPDATA%\Desligador\config.json` (mínimo de 6 dígitos) e reinicie a tarefa:
```powershell
Stop-ScheduledTask Desligador; Start-ScheduledTask Desligador
```

**Mais restrição (opcional):** se outras pessoas usam a sua rede do Tailscale, crie uma regra em *Access Controls* no [painel do Tailscale](https://login.tailscale.com/admin/acls) permitindo a porta `8765` do PC só para os seus aparelhos. Veja a [documentação de ACLs](https://tailscale.com/kb/1018/acls).

## Solução de problemas

| Problema | O que fazer |
|---|---|
| Celular mostra “Sem conexão com o PC” | Confira se o Tailscale está ligado no celular e no PC e se o PC aparece como *online*. |
| Funciona em `localhost` mas não no celular | Veja o log: se aparecer “Tailscale não encontrado”, o servidor ainda está esperando o Tailscale. Confira também se o Windows não criou regras de **bloqueio** para o Python (*Firewall do Windows → Configurações avançadas → Regras de entrada*); regras de bloqueio vencem as de liberação. |
| Script não executa | Rode com `powershell -ExecutionPolicy Bypass -File ...` e como Administrador. |
| Esqueci o PIN | Ele está em `%APPDATA%\Desligador\config.json`. |

Log: `%LOCALAPPDATA%\Desligador\desligador.log`

## Desinstalar

```powershell
powershell -ExecutionPolicy Bypass -File scripts\desinstalar.ps1
```
Depois, se quiser, apague as pastas `%APPDATA%\Desligador` e `%LOCALAPPDATA%\Desligador`.

## Desenvolvimento

```powershell
py -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\python -m pytest
.venv\Scripts\ruff check .
```

- [CLAUDE.md](CLAUDE.md): mapa do código, regras do projeto e como adicionar novas ações (útil para pessoas e para assistentes de IA)
- [docs/arquitetura.md](docs/arquitetura.md): camadas e fluxo de uma requisição
- [docs/decisoes/](docs/decisoes/): registro das decisões de arquitetura (ADRs)
- [CHANGELOG.md](CHANGELOG.md)

## Licença

[MIT](LICENSE)
