# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Corrigido
- Logo depois do logon, se o IP do Tailscale já aparecia mas ainda não aceitava conexões, o servidor desistia de ouvir nele e o celular não alcançava o PC. Agora ele tenta de novo a cada 15 s.

## [0.2.0] - 2026-10-10

### Segurança
- Proteção contra CSRF e DNS rebinding: o servidor só aceita `Host`/`Origin` deste PC e POST em `application/json`.
- O PIN passa a ser guardado como hash PBKDF2-SHA256 (600 mil iterações). Configs antigos são migrados automaticamente, mantendo o PIN.
- Tempo limite de 10 s por conexão; `Content-Length` inválido retorna 400.

### Adicionado
- Comando `python -m desligador --trocar-pin`. O instalador pede o PIN na primeira instalação.

### Alterado
- O desligamento usa `shutdown /f`: programas abertos são fechados sem salvar, para nada travar o desligamento.
- README sem emojis, com recomendações de segurança (2FA no Tailscale, expiração de chave, bloqueio de tela).

## [0.1.0] - 2026-10-10

### Adicionado
- Servidor HTTP (só biblioteca padrão) com API para desligar agora, agendar e cancelar.
- Autenticação por PIN com bloqueio após 5 tentativas erradas.
- Servidor escuta apenas em `127.0.0.1` e no IP do Tailscale.
- Interface web para celular, instalável na tela inicial.
- Scripts para iniciar com o Windows (Agendador de Tarefas) e regra de firewall.
- Testes automatizados e CI no GitHub Actions.
