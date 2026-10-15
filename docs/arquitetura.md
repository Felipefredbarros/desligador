# Arquitetura

## Visão geral

```
Celular (navegador)
   │  http://<pc>:8765  — dentro da VPN do Tailscale (WireGuard)
   ▼
Firewall do Windows (porta 8765 liberada só para 100.64.0.0/10)
   ▼
api/servidor.py ............ HTTP, arquivos de web/, timeout, cabeçalhos de segurança
   │   └── api/protecao.py ........ só aceita Host/Origin deste PC (CSRF, DNS rebinding)
   ▼
api/rotas.py ............... JSON ⇄ serviços, exceção → status HTTP
   ├──▶ servicos/autenticacao.py ..... PIN × hash (dominio/pin.py) + bloqueio por IP
   └──▶ servicos/desligamento.py ..... agendar / cancelar / status
           ├──▶ dominio/agendamento.py ..... regras puras (minutos, horário)
           └──▶ plataforma/energia.py ...... EnergiaWindows → shutdown.exe
```

## Camadas

| Camada | Conhece | Não conhece |
|---|---|---|
| `dominio` | só Python | HTTP, Windows, arquivos |
| `plataforma` | Windows, rede | HTTP, regras de negócio |
| `servicos` | `dominio`, interface `Energia` | HTTP, implementação concreta de `Energia` |
| `api` | `servicos` | Windows |
| `__main__` | tudo: é quem monta as peças (composição) | — |

A troca de `EnergiaWindows` por `EnergiaFalsa` acontece só em `__main__.py` (flag `--simular`) e nos testes. Por isso dá para testar tudo sem desligar o PC.

## Fluxo de uma requisição: “desligar em 30 min”

0. Uma vez por aparelho, a página faz `POST /api/entrar` com `{"pin": "..."}`: o PIN é conferido (passo 5) e a resposta traz o cookie de sessão `desligador_sessao` (`HttpOnly`, `SameSite=Strict`, 30 dias). O servidor guarda só o SHA-256 do token. Ver [ADR 0005](decisoes/0005-sessao-com-cookie.md).
1. O celular envia `POST /api/desligar` com `{"minutos": 30}` e o cookie de sessão.
2. `servidor.py` confere se o `Host` é deste PC (403 se não for). Por ser POST, confere também o `Origin` (403) e se o corpo é `application/json` (415).
3. `servidor.py` valida o `Content-Length`, limita o corpo a 4 KB e repassa os bytes para `rotas.tratar`.
4. `rotas.py` decodifica o JSON e chama a rota `desligar`.
5. A rota confere a sessão do cookie (401 sem ela). No login, `ServicoAutenticacao.verificar` calcula o PBKDF2 do PIN e compara com o hash salvo em tempo constante; erros seguidos bloqueiam o IP.
6. `ServicoDesligamento.agendar` cria um `Agendamento`, que valida os minutos, cancela qualquer agendamento pendente e chama `Energia.agendar_desligamento(1800)`.
7. `EnergiaWindows` executa `shutdown /s /f /t 1800`.
8. A resposta traz o estado atual: `{"agendado": true, "desliga_em": "...", "segundos_restantes": 1800}`.

Erros conhecidos viram status HTTP em `rotas._STATUS_POR_ERRO`: 400 (entrada inválida), 401 (sem sessão ou PIN errado), 429 (bloqueio), 500 (Windows recusou).

### Por que validar Host, Origin e Content-Type
O navegador obedece a qualquer página aberta. Sem essas checagens, um site malicioso poderia:
- **CSRF:** enviar um POST "simples" (`text/plain`, sem preflight) para `http://127.0.0.1:8765` e tentar o PIN, ou errar de propósito até bloquear você;
- **DNS rebinding:** fazer o próprio domínio apontar para `127.0.0.1` e conversar com o servidor como se fosse a mesma origem.

Exigir JSON força o preflight CORS, que o servidor não atende. O `Origin` denuncia a página de origem, e o `Host` denuncia o domínio do atacante. Detalhes no [ADR 0004](decisoes/0004-pin-com-hash-e-protecao-csrf.md).

## Rede e inicialização

- O servidor escuta em `127.0.0.1` e no IP do Tailscale, **nunca em `0.0.0.0`**. Quem estiver no Wi-Fi sem Tailscale não alcança o servidor.
- Se o Tailscale ainda não estiver ativo quando o Windows inicia, `__main__` tenta de novo a cada 15 s.
- `scripts/instalar.ps1` registra uma tarefa no Agendador (logon do usuário → `pythonw -m desligador`, sem janela) e libera a porta no firewall só para `100.64.0.0/10`.

## Onde ficam os arquivos do usuário

| O quê | Onde |
|---|---|
| Configuração (hash do PIN, porta) | `%APPDATA%\Desligador\config.json` |
| Log (rotativo, 3 × 1 MB) | `%LOCALAPPDATA%\Desligador\desligador.log` |

## Limitações conhecidas

- O estado do agendamento fica em memória. Se alguém cancelar pelo próprio Windows (`shutdown /a`) ou o servidor reiniciar, a página pode mostrar um status desatualizado até a próxima ação.
- Só desliga um PC que já está ligado. Para ligar remotamente seria preciso Wake-on-LAN, a partir de outro aparelho que fique ligado na rede.
