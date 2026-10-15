# Segurança

## Como avisar uma falha

**Não abra uma issue pública.** Use o relato privado do GitHub: aba **Security** → **Report a vulnerability** ([link direto](https://github.com/Felipefredbarros/desligador/security/advisories/new)). Só o mantenedor vê o relato.

Ajuda incluir: o que dá para fazer, os passos para reproduzir e a versão (ou commit). Projeto pessoal, sem prazo garantido, mas a ideia é responder em poucos dias e corrigir com prioridade o que permitir desligar ou cancelar o desligamento sem o PIN.

## Versões

Só a versão mais recente (branch `main`) recebe correções.

## O que conta como falha

- Desligar, agendar ou cancelar **sem sessão válida**.
- Contornar o PIN, o bloqueio por tentativas ou a sessão do cookie.
- CSRF, DNS rebinding ou outra forma de uma página aberta no navegador falar com o servidor.
- Vazamento do PIN ou do token de sessão (em arquivo, log ou resposta).
- Ler arquivos fora da pasta `web/`.

## O que não conta

- Ataques que exigem acesso à sua conta do Tailscale ou ao PC já desbloqueado: o modelo de ameaça parte desses dois estarem seguros (ver o README).
- Falta do atributo `Secure` no cookie: o servidor é HTTP de propósito, e o transporte é criptografado pelo WireGuard do Tailscale ([ADR 0005](docs/decisoes/0005-sessao-com-cookie.md)).
- "Desligar agora" fechar programas sem salvar: é o comportamento escolhido, avisado na página.

As decisões de segurança estão em [docs/decisoes/](docs/decisoes/).
