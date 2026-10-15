# 0005 — Login por PIN que gera um cookie de sessão

**Status:** aceita · **Data:** 2026-10-15 · Substitui o "Lembrar neste aparelho" da [ADR 0001](0001-navegador-em-vez-de-apk.md)

## Contexto
Até a v0.2.0 o PIN ia no corpo de cada `POST`, e a opção "Lembrar neste aparelho" o guardava **em texto puro** no `localStorage` do navegador. Qualquer pessoa com o celular desbloqueado, ou uma falha que rodasse JavaScript na página, lia o PIN. Numa revisão antes de divulgar o projeto, este foi o ponto mais fraco. O [LoL Remoto](https://github.com/Felipefredbarros/lol-remoto) já resolve o mesmo problema com um cookie de sessão (ADR 0006 de lá), e o código foi trazido de lá.

## Decisão
- `POST /api/entrar {"pin": "..."}` confere o PIN, com o mesmo bloqueio por IP, e devolve `Set-Cookie: desligador_sessao=<token>; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000` (30 dias).
- O token tem 32 bytes de `secrets.token_urlsafe`. O servidor guarda só o **SHA-256** dele, com a validade, em `%APPDATA%\Desligador\sessoes.json` (`servicos/sessoes.py`). Limite de 10 sessões; ao passar disso, a mais antiga cai.
- `GET /api/status`, `POST /api/desligar` e `POST /api/cancelar` exigem a sessão (401 sem ela). O PIN no corpo deixa de valer.
- `POST /api/sair` apaga a sessão. `--trocar-pin` apaga todas.
- A página não guarda nada: a opção "Lembrar neste aparelho" saiu, e a página **apaga** o PIN que versões antigas deixaram no `localStorage`.
- O cookie tem prefixo (`desligador_sessao`) porque cookies não são separados por porta, e o LoL Remoto usa o mesmo host com `lolremoto_sessao`. Sem o atributo `Secure`, porque o servidor é HTTP; o transporte é protegido pelo WireGuard do Tailscale.

## Consequências
- O PIN é digitado uma vez a cada 30 dias por aparelho e não fica em lugar nenhum do celular. O cookie `HttpOnly` não é lido por JavaScript.
- `SameSite=Strict`, junto com a checagem de `Origin` e a exigência de JSON ([ADR 0004](0004-pin-com-hash-e-protecao-csrf.md)), mantém a proteção contra CSRF.
- Cada ação deixa de rodar o PBKDF2 (~0,5 s): só o login confere o PIN.
- Se o arquivo de sessões vazar, os hashes não servem para entrar.
