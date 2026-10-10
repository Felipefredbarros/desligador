# 0004 — PIN com hash e proteção contra CSRF / DNS rebinding

**Status:** aceita · **Data:** 2026-10-10

## Contexto
Uma revisão de segurança da v0.1.0 encontrou:
1. **CSRF / DNS rebinding.** O servidor aceitava POST com qualquer `Content-Type` e qualquer `Host`. Uma página maliciosa aberta no navegador do PC (ou do celular conectado ao Tailscale) podia enviar pedidos ao servidor, tentar adivinhar o PIN ou errar de propósito até bloquear o dono.
2. **PIN em texto puro** no `config.json`.
3. **Sem tempo limite** de conexão e `Content-Length` inválido sem tratamento.

## Decisão
- `api/protecao.py`: o servidor só aceita `Host` igual a `localhost`, `127.0.0.1`, o IP em que escuta, o nome do PC ou um nome `*.ts.net` (MagicDNS). Em POST, o `Origin` (se existir) precisa passar pela mesma regra e o corpo precisa ser `application/json`. Isso força o preflight CORS, que o servidor não atende.
- O PIN passa a ser guardado como **PBKDF2-HMAC-SHA256** com sal aleatório de 16 bytes e 600 mil iterações (recomendação da OWASP), no formato `pbkdf2_sha256$<iteracoes>$<sal>$<hash>`. As iterações ficam no próprio texto, então dá para aumentá-las no futuro sem quebrar configs antigos.
- Configs da v0.1.0 (`"pin"` em texto) são **migrados automaticamente** na inicialização, mantendo o mesmo PIN.
- Novo comando `python -m desligador --trocar-pin`. O instalador o executa na primeira instalação.
- Timeout de 10 s por conexão; `Content-Length` inválido → 400.

## Consequências
- Não é mais possível "ver" o PIN abrindo o arquivo. Quem esquecer o PIN define outro com `--trocar-pin`.
- Cada conferência de PIN leva cerca de meio segundo. É imperceptível para o usuário e torna inviável a força bruta, inclusive offline, se o arquivo vazar.
- Quem acessar por um nome que não seja o do PC no Windows nem `*.ts.net` (ex.: um apelido renomeado no painel do Tailscale) recebe 403 e deve usar o IP ou o nome completo do MagicDNS.
- A conferência do PIN roda dentro da trava do serviço de autenticação. Assim, tentativas em paralelo não conseguem passar do limite de erros.
