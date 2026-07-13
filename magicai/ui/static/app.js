"use strict";

const STORAGE = {
  session: "magicai.ui.session.v1",
  transcript: "magicai.ui.transcript.v1",
  lastResult: "magicai.ui.lastResult.v1",
};

const STATUS_LABELS = {
  answered: "Respondido",
  needs_clarification: "Necesita aclaración",
  strategy_required: "Requiere Deck Master",
  insufficient_evidence: "Evidencia insuficiente",
  false_premise: "Premisa corregida",
};

const ORIGIN_LABELS = {
  disambiguation: "Desambiguación",
  deterministic_rule: "Reglas deterministas",
  deterministic_oracle: "Oracle determinista",
  deterministic_rulings: "Rulings deterministas",
  premise_guard: "Control de premisa",
  strategy_boundary: "Frontera estratégica",
  llm_validated: "LLM validado",
  safe_fallback: "Fallback seguro",
};

const state = {
  sessionId: readStorage(STORAGE.session, null),
  messages: readStorage(STORAGE.transcript, []),
  lastResult: readStorage(STORAGE.lastResult, null),
  sending: false,
  metadata: null,
};

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  captureElements();
  bindEvents();
  restoreState();
  void loadMetadata();
  void refreshHealth();
  window.setInterval(refreshHealth, 30000);
});

function captureElements() {
  const ids = [
    "health-badge",
    "health-label",
    "new-session-button",
    "session-label",
    "message-list",
    "welcome-message",
    "question-form",
    "question-input",
    "send-button",
    "result-status",
    "result-summary",
    "evidence-sections",
    "cards-count",
    "cards-list",
    "rules-count",
    "rules-list",
    "rulings-count",
    "rulings-list",
    "assumptions-count",
    "assumptions-list",
    "warnings-count",
    "warnings-list",
    "sources-list",
    "version-label",
    "toast-region",
  ];

  for (const id of ids) {
    elements[id] = document.getElementById(id);
  }
}

function bindEvents() {
  elements["question-form"].addEventListener("submit", event => {
    event.preventDefault();
    void submitQuestion();
  });

  elements["question-input"].addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion();
    }
  });

  elements["question-input"].addEventListener("input", autoResizeTextarea);
  elements["new-session-button"].addEventListener("click", resetConversation);

  for (const button of document.querySelectorAll(".suggestion")) {
    button.addEventListener("click", () => {
      elements["question-input"].value = button.textContent.trim();
      autoResizeTextarea();
      elements["question-input"].focus();
    });
  }
}

function restoreState() {
  if (state.messages.length) {
    removeWelcome();
    for (const message of state.messages) {
      renderMessage(message, false);
    }
  }

  if (state.lastResult) {
    renderEvidence(state.lastResult);
  }

  updateSessionLabel();
  scrollMessagesToEnd();
}

async function loadMetadata() {
  try {
    state.metadata = await fetchJson("/meta");
    const projectVersion = state.metadata.project_version || "local";
    const schemaVersion = state.metadata.judge_result_schema_version || "?";
    elements["version-label"].textContent = `MagicAI ${projectVersion} · JudgeResult ${schemaVersion}`;
  } catch (error) {
    elements["version-label"].textContent = "MagicAI local · metadata no disponible";
  }
}

async function refreshHealth() {
  const badge = elements["health-badge"];
  const label = elements["health-label"];

  try {
    const health = await fetchJson("/health");
    badge.className = "health-badge";

    if (health.status === "ok") {
      badge.classList.add("is-ok");
      label.textContent = "Juez listo";
    } else if (health.ready) {
      badge.classList.add("is-degraded");
      label.textContent = health.full_service ? "Fuentes parciales" : "Modo determinista";
    } else {
      badge.classList.add("is-unavailable");
      label.textContent = "Fuentes no disponibles";
    }

    badge.title = buildHealthDescription(health);
  } catch (error) {
    badge.className = "health-badge is-unavailable";
    label.textContent = "API no disponible";
    badge.title = error.message;
  }
}

function buildHealthDescription(health) {
  const sourceState = health.sources?.status || "desconocido";
  const ollamaState = health.services?.ollama?.status || "desconocido";
  return `Fuentes: ${sourceState}. Ollama: ${ollamaState}.`;
}

async function submitQuestion() {
  const input = elements["question-input"];
  const question = input.value.trim();

  if (!question || state.sending) {
    return;
  }

  setSending(true);
  removeWelcome();
  addStoredMessage({role: "user", text: question});
  input.value = "";
  autoResizeTextarea();

  const loadingNode = renderLoadingMessage();

  try {
    const payload = {question};
    if (state.sessionId) {
      payload.session_id = state.sessionId;
    }

    const result = await fetchJson("/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });

    loadingNode.remove();
    state.sessionId = result.session_id || state.sessionId;
    state.lastResult = result;
    writeStorage(STORAGE.session, state.sessionId);
    writeStorage(STORAGE.lastResult, result);

    addStoredMessage({
      role: "assistant",
      text: result.answer || "El Juez no devolvió texto.",
      status: result.status,
    });
    renderEvidence(result);
    updateSessionLabel();
  } catch (error) {
    loadingNode.remove();
    const message = error.userMessage || error.message || "No se pudo completar la consulta.";
    addStoredMessage({role: "error", text: message});
    showToast(message);
  } finally {
    setSending(false);
    input.focus();
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  let payload = null;

  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }

  if (!response.ok) {
    const apiError = payload?.error;
    const error = new Error(apiError?.message || `HTTP ${response.status}`);
    error.userMessage = apiError?.message || "MagicAI no pudo completar la solicitud.";
    error.code = apiError?.code || "http_error";
    error.retryable = Boolean(apiError?.retryable);
    throw error;
  }

  if (!payload || typeof payload !== "object") {
    throw new Error("La API devolvió una respuesta no válida.");
  }

  return payload;
}

function renderMessage(message, shouldScroll = true) {
  const article = document.createElement("article");
  article.className = `message is-${message.role}`;

  const header = document.createElement("div");
  header.className = "message-header";
  header.textContent = message.role === "user" ? "Tú" : message.role === "error" ? "Error" : "Juez";

  if (message.status) {
    const status = document.createElement("span");
    status.className = "message-status";
    status.textContent = STATUS_LABELS[message.status] || message.status;
    header.appendChild(status);
  }

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  renderRichText(bubble, message.text || "");

  article.append(header, bubble);
  elements["message-list"].appendChild(article);

  if (shouldScroll) {
    scrollMessagesToEnd();
  }

  return article;
}

function renderLoadingMessage() {
  const article = document.createElement("article");
  article.className = "message is-assistant";

  const header = document.createElement("div");
  header.className = "message-header";
  header.textContent = "Juez · consultando fuentes";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const dots = document.createElement("span");
  dots.className = "loading-dots";
  dots.setAttribute("aria-label", "Procesando");
  dots.append(document.createElement("span"), document.createElement("span"), document.createElement("span"));

  bubble.appendChild(dots);
  article.append(header, bubble);
  elements["message-list"].appendChild(article);
  scrollMessagesToEnd();
  return article;
}

function renderRichText(container, text) {
  const lines = String(text).replace(/\r\n?/g, "\n").split("\n");
  let list = null;
  let listType = null;

  const flushList = () => {
    if (list) {
      container.appendChild(list);
      list = null;
      listType = null;
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      continue;
    }

    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    const bulleted = line.match(/^[-*]\s+(.*)$/);

    if (numbered || bulleted) {
      const nextType = numbered ? "ol" : "ul";
      if (!list || listType !== nextType) {
        flushList();
        listType = nextType;
        list = document.createElement(nextType);
      }
      const item = document.createElement("li");
      appendInlineFormatting(item, (numbered || bulleted)[1]);
      list.appendChild(item);
      continue;
    }

    flushList();
    const paragraph = document.createElement("p");
    appendInlineFormatting(paragraph, line);
    container.appendChild(paragraph);
  }

  flushList();
}

function appendInlineFormatting(container, text) {
  const chunks = String(text).split(/(\*\*[^*]+\*\*)/g);
  for (const chunk of chunks) {
    if (chunk.startsWith("**") && chunk.endsWith("**") && chunk.length > 4) {
      const strong = document.createElement("strong");
      strong.textContent = chunk.slice(2, -2);
      container.appendChild(strong);
    } else if (chunk) {
      container.appendChild(document.createTextNode(chunk));
    }
  }
}

function renderEvidence(result) {
  const status = result.status || "answered";
  const statusBadge = elements["result-status"];
  statusBadge.className = `status-badge is-${status}`;
  statusBadge.textContent = STATUS_LABELS[status] || status;

  const summary = elements["result-summary"];
  clearNode(summary);

  const row = document.createElement("div");
  row.className = "status-row";
  row.append(
    createPill(ORIGIN_LABELS[result.origin] || result.origin || "Origen desconocido"),
    createPill(`Confianza: ${translateConfidence(result.confidence)}`, `is-${result.confidence || "unknown"}`),
    createPill(`Autoridad: ${result.authority || "judge"}`),
  );
  summary.appendChild(row);

  elements["evidence-sections"].hidden = false;

  renderCards(result.cards || []);
  renderRules(result.rules || []);
  renderRulings(result.rulings || []);
  renderNotes("assumptions", result.assumptions || [], "No se declararon supuestos.");
  renderNotes("warnings", result.warnings || [], "No hay advertencias.");
  renderTechnicalDetails(result);
}

function createPill(text, className = "") {
  const pill = document.createElement("span");
  pill.className = `meta-pill ${className}`.trim();
  pill.textContent = text;
  return pill;
}

function translateConfidence(value) {
  return {high: "alta", medium: "media", low: "baja"}[value] || value || "desconocida";
}

function renderCards(cards) {
  const list = elements["cards-list"];
  clearNode(list);
  elements["cards-count"].textContent = String(cards.length);

  if (!cards.length) {
    list.appendChild(createEmptyNote("No se recuperaron cartas para esta respuesta."));
    return;
  }

  for (const card of cards) {
    const node = document.createElement("article");
    node.className = "evidence-card";

    const title = document.createElement("h3");
    title.textContent = card.name || "Carta sin nombre";
    node.appendChild(title);

    const identity = [card.mana_cost, card.type_line].filter(Boolean).join(" · ");
    if (identity) {
      const line = document.createElement("p");
      line.textContent = identity;
      node.appendChild(line);
    }

    if (card.oracle_text) {
      const oracle = document.createElement("p");
      oracle.textContent = card.oracle_text;
      node.appendChild(oracle);
    }

    if (card.scryfall_uri) {
      const link = document.createElement("a");
      link.className = "evidence-link";
      link.href = card.scryfall_uri;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Abrir en Scryfall ↗";
      node.appendChild(link);
    }

    list.appendChild(node);
  }
}

function renderRules(rules) {
  const list = elements["rules-list"];
  clearNode(list);
  elements["rules-count"].textContent = String(rules.length);

  if (!rules.length) {
    list.appendChild(createEmptyNote("No se recuperaron reglas explícitas."));
    return;
  }

  for (const rule of rules) {
    const node = document.createElement("article");
    node.className = "evidence-card";
    const title = document.createElement("h3");
    title.textContent = [rule.number, rule.title].filter(Boolean).join(" · ") || "Regla recuperada";
    node.appendChild(title);
    list.appendChild(node);
  }
}

function renderRulings(rulings) {
  const list = elements["rulings-list"];
  clearNode(list);
  elements["rulings-count"].textContent = String(rulings.length);

  if (!rulings.length) {
    list.appendChild(createEmptyNote("No se recuperaron rulings para esta respuesta."));
    return;
  }

  for (const ruling of rulings) {
    const node = document.createElement("article");
    node.className = "evidence-card";

    const title = document.createElement("h3");
    title.textContent = ruling.card_name || "Ruling";
    node.appendChild(title);

    const metadata = document.createElement("p");
    metadata.textContent = [ruling.published_at, String(ruling.source || "").toUpperCase()].filter(Boolean).join(" · ");
    node.appendChild(metadata);

    const comment = document.createElement("p");
    comment.textContent = ruling.comment || "";
    node.appendChild(comment);

    list.appendChild(node);
  }
}

function renderNotes(kind, notes, emptyMessage) {
  const list = elements[`${kind}-list`];
  clearNode(list);
  elements[`${kind}-count`].textContent = String(notes.length);

  if (!notes.length) {
    list.appendChild(createEmptyNote(emptyMessage));
    return;
  }

  for (const note of notes) {
    const node = document.createElement("p");
    node.className = "evidence-note";
    node.textContent = note;
    list.appendChild(node);
  }
}

function renderTechnicalDetails(result) {
  const list = elements["sources-list"];
  clearNode(list);

  const definitionList = document.createElement("dl");
  definitionList.className = "meta-grid";

  const rows = [
    ["Schema", result.schema_version],
    ["Estado", result.status],
    ["Origen", result.origin],
    ["Confianza", result.confidence],
    ["Intent", result.intent || "—"],
    ["Intentos de validación", String(result.validation_attempts ?? 0)],
    ["Sesión", result.session_id || "—"],
  ];

  for (const [label, value] of rows) {
    appendMetaRow(definitionList, label, value || "—");
  }

  const versions = result.source_versions || {};
  for (const [key, value] of Object.entries(versions)) {
    appendMetaRow(definitionList, formatKey(key), String(value));
  }

  const sourceHealth = result.source_health || {};
  if (sourceHealth.status) {
    appendMetaRow(definitionList, "Salud de fuentes", String(sourceHealth.status));
  }

  list.appendChild(definitionList);
}

function appendMetaRow(container, label, value) {
  const row = document.createElement("div");
  row.className = "meta-row";
  const term = document.createElement("dt");
  term.textContent = label;
  const description = document.createElement("dd");
  description.textContent = value;
  row.append(term, description);
  container.appendChild(row);
}

function formatKey(key) {
  return String(key)
    .replaceAll("_", " ")
    .replace(/^./, first => first.toUpperCase());
}

function createEmptyNote(text) {
  const node = document.createElement("p");
  node.className = "evidence-note";
  node.textContent = text;
  return node;
}

function addStoredMessage(message) {
  state.messages.push(message);
  state.messages = state.messages.slice(-40);
  writeStorage(STORAGE.transcript, state.messages);
  renderMessage(message);
}

function resetConversation() {
  state.sessionId = null;
  state.messages = [];
  state.lastResult = null;

  localStorage.removeItem(STORAGE.session);
  localStorage.removeItem(STORAGE.transcript);
  localStorage.removeItem(STORAGE.lastResult);

  clearNode(elements["message-list"]);
  const welcome = buildWelcomeClone();
  elements["message-list"].appendChild(welcome);
  bindSuggestionButtons(welcome);

  elements["result-status"].className = "status-badge is-idle";
  elements["result-status"].textContent = "Sin respuesta";
  elements["result-summary"].textContent = "La evidencia de la última respuesta aparecerá aquí.";
  elements["evidence-sections"].hidden = true;
  updateSessionLabel();
  elements["question-input"].focus();
}

function buildWelcomeClone() {
  const article = document.createElement("article");
  article.id = "welcome-message";
  article.className = "welcome-card";

  const kicker = document.createElement("p");
  kicker.className = "welcome-kicker";
  kicker.textContent = "More Gathering. Less Guessing.";

  const title = document.createElement("h3");
  title.textContent = "Pregunta por cartas, reglas o interacciones.";

  const description = document.createElement("p");
  description.textContent = "El Juez recupera Oracle, Comprehensive Rules y rulings locales antes de responder. Las consultas estratégicas se reservan para el futuro Deck Master.";

  const suggestions = document.createElement("div");
  suggestions.className = "suggestion-grid";
  suggestions.setAttribute("aria-label", "Preguntas de ejemplo");

  for (const text of [
    "¿Puedo responder durante la resolución de una habilidad?",
    "¿Cuántos Kobolds crea Prossh?",
    "¿Qué ocurre si sacrifico Young Wolf?",
  ]) {
    const button = document.createElement("button");
    button.className = "suggestion";
    button.type = "button";
    button.textContent = text;
    suggestions.appendChild(button);
  }

  article.append(kicker, title, description, suggestions);
  return article;
}

function bindSuggestionButtons(root) {
  for (const button of root.querySelectorAll(".suggestion")) {
    button.addEventListener("click", () => {
      elements["question-input"].value = button.textContent.trim();
      autoResizeTextarea();
      elements["question-input"].focus();
    });
  }
}

function removeWelcome() {
  document.getElementById("welcome-message")?.remove();
}

function updateSessionLabel() {
  elements["session-label"].textContent = state.sessionId
    ? `Sesión ${state.sessionId.slice(0, 8)}`
    : "Sesión nueva";
}

function setSending(value) {
  state.sending = value;
  elements["send-button"].disabled = value;
  elements["new-session-button"].disabled = value;
  elements["question-input"].disabled = value;
}

function autoResizeTextarea() {
  const textarea = elements["question-input"];
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
}

function scrollMessagesToEnd() {
  window.requestAnimationFrame(() => {
    elements["message-list"].scrollTop = elements["message-list"].scrollHeight;
  });
}

function clearNode(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  elements["toast-region"].appendChild(toast);
  window.setTimeout(() => toast.remove(), 5500);
}

function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch (error) {
    localStorage.removeItem(key);
    return fallback;
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    // The UI remains usable when private mode or storage limits block persistence.
  }
}
