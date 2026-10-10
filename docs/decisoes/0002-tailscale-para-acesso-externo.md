# 0002 — Tailscale para acesso fora de casa

**Status:** aceita · **Data:** 2026-10-10

## Contexto
O PC precisa ser controlado também pelo 4G ou por outras redes. Opções consideradas: abrir porta no roteador (port forwarding + DNS dinâmico), túnel público (Cloudflare Tunnel/ngrok) ou VPN mesh (Tailscale).

## Decisão
Usar **Tailscale**. O servidor escuta apenas no IP do Tailscale (e em `127.0.0.1`), e o firewall libera a porta só para `100.64.0.0/10`.

## Consequências
- Nada fica exposto na internet pública; só aparelhos logados na conta do Tailscale enxergam o PC.
- O tráfego é criptografado (WireGuard), então HTTP simples é aceitável dentro da rede do Tailscale.
- Funciona atrás de CGNAT, sem mexer no roteador.
- É preciso instalar o Tailscale no PC e no celular. Mesmo em casa, o acesso passa pelo Tailscale.
- ACLs do Tailscale podem restringir ainda mais quem acessa a porta (exemplo no README).
