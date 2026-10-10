# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento [SemVer](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-10-10

### Adicionado
- Servidor HTTP (só biblioteca padrão) com API para desligar agora, agendar e cancelar.
- Autenticação por PIN com bloqueio após 5 tentativas erradas.
- Servidor escuta apenas em `127.0.0.1` e no IP do Tailscale.
- Interface web para celular, instalável na tela inicial.
- Scripts para iniciar com o Windows (Agendador de Tarefas) e regra de firewall.
- Testes automatizados e CI no GitHub Actions.
