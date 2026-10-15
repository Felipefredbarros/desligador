# Desligador

[![CI](https://github.com/Felipefredbarros/desligador/actions/workflows/ci.yml/badge.svg)](https://github.com/Felipefredbarros/desligador/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Windows](https://img.shields.io/badge/plataforma-Windows-0078D6)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

Desligue seu PC com Windows **pelo celular**, de casa ou de qualquer lugar, de forma segura.

- **Desligar agora** ou **agendar** (15 min, 30 min, 1 h, 2 h ou quantos minutos quiser)
- Contagem regressiva e botão de **cancelar**
- Acesso só pela sua rede privada do **Tailscale** + **PIN** (guardado como hash) com bloqueio contra tentativas
- Página web que vira “app” na tela inicial do celular (Android e iPhone)
- Servidor em Python **sem dependências**, inicia sozinho e invisível com o Windows

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
Abra http://localhost:8765. Na primeira execução um PIN aleatório aparece no terminal; anote-o, porque só o hash dele fica salvo. Para sair, use `Ctrl+C`.

**4. Instale para iniciar com o Windows** (PowerShell **como Administrador**, na pasta do projeto):
```powershell
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
```
Na primeira instalação o script pede para você **definir o PIN** (ou deixar vazio para gerar um). No final, mostra o endereço para usar no celular.

**5. No celular:** com o Tailscale ligado, abra `http://NOME-DO-PC:8765` (ou `http://100.x.y.z:8765`, o IP que aparece no app do Tailscale). Depois use **“Adicionar à tela inicial”** no menu do navegador.

## Segurança

| Camada | O que faz |
|---|---|
| Tailscale | Só os seus aparelhos enxergam o PC; o tráfego é criptografado (WireGuard). Nada fica exposto na internet. |
| Endereço de escuta | O servidor ouve só em `127.0.0.1` e no IP do Tailscale, nunca no Wi-Fi comum. |
| Firewall | A porta 8765 só aceita a faixa do Tailscale (`100.64.0.0/10`). |
| PIN | Mínimo de 6 dígitos, comparação em tempo constante, bloqueio de 5 min após 5 erros. |
| Hash do PIN | O `config.json` guarda só o hash (PBKDF2-SHA256, 600 mil iterações), nunca o PIN. Ele fica em `%APPDATA%\Desligador`, fora do repositório. |
| Sessão | O PIN é digitado uma vez por aparelho e vira um cookie `HttpOnly` e `SameSite=Strict`, válido por 30 dias; o celular não guarda o PIN, e no disco fica só o SHA-256 do token. Trocar o PIN encerra todas as sessões. |
| Sites maliciosos | O servidor só aceita pedidos endereçados a este PC (`Host`/`Origin`) e em JSON, o que bloqueia ataques de CSRF e DNS rebinding vindos de outras páginas abertas no navegador. |
| Conexões | Tempo limite de 10 s por conexão e corpo limitado a 4 KB. |

**Trocar o PIN:**
```powershell
cd src
py -m desligador --trocar-pin
Stop-ScheduledTask Desligador; Start-ScheduledTask Desligador
```

**Atenção:** "Desligar agora" e os agendamentos **fecham os programas abertos sem salvar**, para que nada trave o desligamento.

**Recomendações:**
- Ative a **verificação em duas etapas** na conta que você usa para entrar no Tailscale (Google, GitHub, Microsoft...). Quem entra nessa conta entra na sua rede.
- No [painel do Tailscale](https://login.tailscale.com/admin/machines), abra o PC e use **Disable key expiry**. Sem isso, o PC sai da rede depois de alguns meses e o app para de funcionar.
- Mantenha o celular com bloqueio de tela: quem pega o celular desbloqueado usa a sessão aberta. Use **Sair** na página se for emprestar o aparelho.

**Mais restrição (opcional):** se outras pessoas usam a sua rede do Tailscale, crie uma regra em *Access Controls* no [painel do Tailscale](https://login.tailscale.com/admin/acls) permitindo a porta `8765` do PC só para os seus aparelhos. Veja a [documentação de ACLs](https://tailscale.com/kb/1018/acls).

## Solução de problemas

| Problema | O que fazer |
|---|---|
| Celular mostra “Sem conexão com o PC” | Confira se o Tailscale está ligado no celular e no PC e se o PC aparece como *online*. |
| Funciona em `localhost` mas não no celular | Veja o log: se aparecer “Tailscale não encontrado”, o servidor ainda está esperando o Tailscale. Confira também se o Windows não criou regras de **bloqueio** para o Python (*Firewall do Windows → Configurações avançadas → Regras de entrada*); regras de bloqueio vencem as de liberação. |
| Script não executa | Rode com `powershell -ExecutionPolicy Bypass -File ...` e como Administrador. |
| Página mostra “Host não permitido” | Você acessou por um nome diferente do nome do PC no Windows. Use o IP do Tailscale (`http://100.x.y.z:8765`) ou o nome completo do MagicDNS (`http://nome.tailXXXX.ts.net:8765`). |
| Esqueci o PIN | O PIN não fica salvo (só o hash). Defina outro com `py -m desligador --trocar-pin` (dentro de `src`) e reinicie a tarefa. |

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
- [SECURITY.md](SECURITY.md): como avisar uma falha de segurança (em privado)

## Licença

[MIT](LICENSE)
