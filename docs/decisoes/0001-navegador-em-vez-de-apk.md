# 0001 — Interface no navegador em vez de app Android (APK)

**Status:** aceita · **Data:** 2026-10-10

## Contexto
O controle é feito pelo celular. As opções eram um app nativo (APK) ou uma página web servida pelo próprio PC.

## Decisão
Usar uma **página web** (HTML/CSS/JS puro), com `manifest.json` para poder ser adicionada à tela inicial e abrir em tela cheia, como um app.

## Consequências
- A segurança é a mesma do APK: o que protege o PC é o Tailscale (rede privada criptografada) e o PIN. O cliente seria só outra forma de chamar a mesma API.
- Não exige Android Studio/Flutter, assinatura de APK nem instalar de “fontes desconhecidas”. Funciona também no iPhone.
- Atualizar a interface é só editar arquivos em `src/desligador/web/`.
- ~~Se o PIN for lembrado, fica no `localStorage` do navegador.~~ Desde a [ADR 0005](0005-sessao-com-cookie.md) o PIN não fica no celular: o login gera um cookie de sessão `HttpOnly`.
