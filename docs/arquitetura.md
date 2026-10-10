# Arquitetura

## Visão geral

```
Celular (navegador)
   │  http://<pc>:8765  — dentro da VPN do Tailscale (WireGuard)
   ▼
Firewall do Windows (porta 8765 liberada só para 100.64.0.0/10)
   ▼
api/servidor.py ............ HTTP, arquivos de web/, cabeçalhos de segurança
   ▼
api/rotas.py ............... JSON ⇄ serviços, exceção → status HTTP
   ├──▶ servicos/autenticacao.py ..... PIN + bloqueio por IP
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

1. O celular envia `POST /api/desligar` com `{"pin": "12345678", "minutos": 30}`.
2. `servidor.py` limita o tamanho do corpo e repassa os bytes para `rotas.tratar`.
3. `rotas.py` decodifica o JSON e chama a rota `desligar`.
4. `ServicoAutenticacao.verificar` compara o PIN em tempo constante; erros seguidos bloqueiam o IP.
5. `ServicoDesligamento.agendar` cria um `Agendamento`, que valida os minutos, cancela qualquer agendamento pendente e chama `Energia.agendar_desligamento(1800)`.
6. `EnergiaWindows` executa `shutdown /s /t 1800`.
7. A resposta traz o estado atual: `{"agendado": true, "desliga_em": "...", "segundos_restantes": 1800}`.

Erros conhecidos viram status HTTP em `rotas._STATUS_POR_ERRO`: 400 (entrada inválida), 401 (PIN), 429 (bloqueio), 500 (Windows recusou).

## Rede e inicialização

- O servidor escuta em `127.0.0.1` e no IP do Tailscale, **nunca em `0.0.0.0`**. Quem estiver no Wi-Fi sem Tailscale não alcança o servidor.
- Se o Tailscale ainda não estiver ativo quando o Windows inicia, `__main__` tenta de novo a cada 15 s.
- `scripts/instalar.ps1` registra uma tarefa no Agendador (logon do usuário → `pythonw -m desligador`, sem janela) e libera a porta no firewall só para `100.64.0.0/10`.

## Onde ficam os arquivos do usuário

| O quê | Onde |
|---|---|
| Configuração (PIN, porta) | `%APPDATA%\Desligador\config.json` |
| Log (rotativo, 3 × 1 MB) | `%LOCALAPPDATA%\Desligador\desligador.log` |

## Limitações conhecidas

- O estado do agendamento fica em memória. Se alguém cancelar pelo próprio Windows (`shutdown /a`) ou o servidor reiniciar, a página pode mostrar um status desatualizado até a próxima ação.
- Só desliga um PC que já está ligado. Para ligar remotamente seria preciso Wake-on-LAN, a partir de outro aparelho que fique ligado na rede.
