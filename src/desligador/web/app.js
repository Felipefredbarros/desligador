"use strict";

// O PIN é digitado uma vez: o servidor devolve um cookie de sessão HttpOnly, que o
// JavaScript não lê (docs/decisoes/0005). Nada de PIN no navegador.
const PIN_ANTIGO = "desligador.pin"; // até a 0.2.0 o PIN ficava aqui, em texto puro
const INTERVALO_STATUS_MS = 30_000;

const el = (id) => document.getElementById(id);
let fimContagem = null;
let timerContagem = null;

// ---------- API ----------

class ErroApi extends Error {
  constructor(mensagem, status) {
    super(mensagem);
    this.status = status;
  }
}

async function chamarApi(caminho, corpo) {
  const opcoes = corpo === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  };
  let resposta;
  try {
    resposta = await fetch(caminho, opcoes);
  } catch {
    // fetch lança TypeError quando não alcança o servidor (PC desligado, sem Tailscale…).
    throw new ErroApi("Sem conexão com o PC.", 0);
  }
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new ErroApi(dados.erro || `Erro ${resposta.status}`, resposta.status);
  return dados;
}

// ---------- Tela ----------

function mostrarMensagem(texto, tipo = "info") {
  const mensagem = el("mensagem");
  mensagem.textContent = texto;
  mensagem.dataset.tipo = tipo;
}

function mostrarLogin() {
  el("tela-app").hidden = true;
  el("sair").hidden = true;
  el("tela-login").hidden = false;
  el("pin").focus();
}

function mostrarApp() {
  el("tela-login").hidden = true;
  el("tela-app").hidden = false;
  el("sair").hidden = false;
}

function formatarRestante(segundos) {
  const h = Math.floor(segundos / 3600);
  const m = Math.floor((segundos % 3600) / 60);
  const s = segundos % 60;
  const dois = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${dois(m)}:${dois(s)}` : `${dois(m)}:${dois(s)}`;
}

function atualizarContagem() {
  const restante = Math.max(0, Math.round((fimContagem - Date.now()) / 1000));
  el("contagem").textContent = formatarRestante(restante);
  if (restante === 0) {
    clearInterval(timerContagem);
    el("status-texto").textContent = "Desligando…";
  }
}

function mostrarStatus(dados) {
  clearInterval(timerContagem);
  const agendado = Boolean(dados.agendado);
  el("contagem").hidden = !agendado;
  el("cancelar").hidden = !agendado;

  if (!agendado) {
    el("status-texto").textContent = "Nenhum desligamento agendado";
    return;
  }
  // Usa os segundos restantes do servidor para não depender do relógio do celular.
  fimContagem = Date.now() + dados.segundos_restantes * 1000;
  const horario = new Date(fimContagem).toLocaleTimeString("pt-BR", {
    hour: "2-digit", minute: "2-digit",
  });
  el("status-texto").textContent = `Desliga às ${horario}`;
  atualizarContagem();
  timerContagem = setInterval(atualizarContagem, 1000);
}

function definirOcupado(ocupado) {
  document.querySelectorAll("button").forEach((botao) => { botao.disabled = ocupado; });
}

async function carregarStatus() {
  try {
    mostrarStatus(await chamarApi("/api/status"));
    mostrarApp();
  } catch (erro) {
    if (erro.status === 401) {
      mostrarLogin();
      return;
    }
    mostrarApp();
    el("status-texto").textContent = "Sem conexão com o PC";
    el("contagem").hidden = true;
    el("cancelar").hidden = true;
  }
}

// ---------- Ações ----------

async function executar(caminho, corpo, textoSucesso) {
  definirOcupado(true);
  try {
    mostrarStatus(await chamarApi(caminho, corpo));
    mostrarMensagem(textoSucesso, "sucesso");
  } catch (erro) {
    if (erro.status === 401) mostrarLogin();
    mostrarMensagem(erro.message, "erro");
  } finally {
    definirOcupado(false);
  }
}

function agendar(minutos) {
  executar("/api/desligar", { minutos }, `Desligamento agendado para daqui a ${minutos} min.`);
}

// ---------- Inicialização ----------

try { localStorage.removeItem(PIN_ANTIGO); } catch { /* armazenamento indisponível */ }

el("form-login").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  definirOcupado(true);
  try {
    mostrarStatus(await chamarApi("/api/entrar", { pin: el("pin").value.trim() }));
    el("pin").value = "";
    mostrarMensagem("");
    mostrarApp();
  } catch (erro) {
    mostrarMensagem(erro.message, "erro");
  } finally {
    definirOcupado(false);
  }
});

el("sair").addEventListener("click", async () => {
  await chamarApi("/api/sair", {}).catch(() => {});
  mostrarMensagem("");
  mostrarLogin();
});

document.querySelectorAll("[data-minutos]").forEach((botao) => {
  botao.addEventListener("click", () => agendar(Number(botao.dataset.minutos)));
});

el("form-personalizado").addEventListener("submit", (evento) => {
  evento.preventDefault();
  const minutos = Number(el("minutos").value);
  if (!Number.isInteger(minutos) || minutos < 1 || minutos > 1440) {
    mostrarMensagem("Informe de 1 a 1440 minutos.", "erro");
    return;
  }
  agendar(minutos);
});

el("desligar-agora").addEventListener("click", () => {
  if (confirm("Desligar o PC agora? Programas abertos serão fechados sem salvar.")) {
    executar("/api/desligar", { minutos: 0 }, "Desligando o PC…");
  }
});

el("cancelar").addEventListener("click", () => {
  executar("/api/cancelar", {}, "Desligamento cancelado.");
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && el("tela-login").hidden) carregarStatus();
});

carregarStatus();
setInterval(() => { if (el("tela-login").hidden) carregarStatus(); }, INTERVALO_STATUS_MS);
