"use strict";

const CHAVE_PIN = "desligador.pin";
const INTERVALO_STATUS_MS = 30_000;

const el = (id) => document.getElementById(id);
let fimContagem = null;
let timerContagem = null;

// ---------- PIN salvo (opcional) ----------

function lerPinSalvo() {
  try { return localStorage.getItem(CHAVE_PIN); } catch { return null; }
}

function lembrarPin(pin) {
  try {
    if (el("lembrar").checked) localStorage.setItem(CHAVE_PIN, pin);
    else localStorage.removeItem(CHAVE_PIN);
  } catch { /* armazenamento indisponível: segue sem lembrar */ }
}

// ---------- API ----------

async function chamarApi(caminho, corpo) {
  const opcoes = corpo === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  };
  const resposta = await fetch(caminho, opcoes);
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) throw new Error(dados.erro || `Erro ${resposta.status}`);
  return dados;
}

// ---------- Tela ----------

function mostrarMensagem(texto, tipo = "info") {
  const mensagem = el("mensagem");
  mensagem.textContent = texto;
  mensagem.dataset.tipo = tipo;
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
  } catch {
    el("status-texto").textContent = "Sem conexão com o PC";
    el("contagem").hidden = true;
    el("cancelar").hidden = true;
  }
}

// ---------- Ações ----------

function pinDigitado() {
  const pin = el("pin").value.trim();
  if (!pin) {
    mostrarMensagem("Digite o PIN.", "erro");
    el("pin").focus();
    return null;
  }
  return pin;
}

async function executar(caminho, extra, textoSucesso) {
  const pin = pinDigitado();
  if (!pin) return;
  definirOcupado(true);
  try {
    mostrarStatus(await chamarApi(caminho, { pin, ...extra }));
    lembrarPin(pin);
    mostrarMensagem(textoSucesso, "sucesso");
  } catch (erro) {
    // fetch lança TypeError quando não alcança o servidor (PC desligado, sem Tailscale…).
    mostrarMensagem(erro instanceof TypeError ? "Sem conexão com o PC." : erro.message, "erro");
  } finally {
    definirOcupado(false);
  }
}

function agendar(minutos) {
  executar("/api/desligar", { minutos }, `Desligamento agendado para daqui a ${minutos} min.`);
}

// ---------- Inicialização ----------

const pinSalvo = lerPinSalvo();
if (pinSalvo) {
  el("pin").value = pinSalvo;
  el("lembrar").checked = true;
}

el("lembrar").addEventListener("change", () => {
  if (!el("lembrar").checked) lembrarPin("");
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
  if (!document.hidden) carregarStatus();
});

carregarStatus();
setInterval(carregarStatus, INTERVALO_STATUS_MS);
