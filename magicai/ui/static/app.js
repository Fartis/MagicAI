"use strict";

const STORAGE = {
  session: "magicai.ui.session.v1",
  transcript: "magicai.ui.transcript.v1",
  lastResult: "magicai.ui.lastResult.v1",
};

const ASK_TIMEOUT_MS = 180000;
const AUXILIARY_TIMEOUT_MS = 10000;
const MAX_STORED_MESSAGES = 40;
const ALLOWED_MESSAGE_ROLES = new Set(["user", "assistant", "error"]);

let storageAvailable = true;
let storageWarningPending = false;
let storageWarningShown = false;

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

const elements = {};

const state = {
  sessionId: loadStoredSession(),
  messages: loadStoredMessages(),
  lastResult: loadStoredResult(),
  sending: false,
  metadata: null,
  activeRequest: null,
  requestSequence: 0,
  healthRequestPending: false,
};

document.addEventListener("DOMContentLoaded", () => {
  captureElements();
  bindEvents();
  flushStorageWarning();
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
    "cancel-request-button",
    "request-status",
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
  elements["cancel-request-button"].addEventListener("click", cancelActiveRequest);

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
  if (state.healthRequestPending) {
    return;
  }

  state.healthRequestPending = true;
  const badge = elements["health-badge"];
  const label = elements["health-label"];
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort("timeout"), AUXILIARY_TIMEOUT_MS);

  try {
    const health = await fetchJson("/health", {signal: controller.signal});
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
    label.textContent = error.name === "AbortError" ? "Salud sin respuesta" : "API no disponible";
    badge.title = error.message;
  } finally {
    window.clearTimeout(timeoutId);
    state.healthRequestPending = false;
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

  const requestId = ++state.requestSequence;
  const sentSessionId = state.sessionId;
  const controller = new AbortController();
  const activeRequest = {
    id: requestId,
    controller,
    cancelReason: null,
    timeoutId: null,
  };
  state.activeRequest = activeRequest;
  activeRequest.timeoutId = window.setTimeout(() => {
    activeRequest.cancelReason = "timeout";
    controller.abort("timeout");
  }, ASK_TIMEOUT_MS);

  setSending(true);
  removeWelcome();
  addStoredMessage({role: "user", text: question});
  input.value = "";
  autoResizeTextarea();

  const loadingNode = renderLoadingMessage();

  try {
    const payload = {question};
    if (sentSessionId) {
      payload.session_id = sentSessionId;
    }

    const result = await fetchJson("/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!isCurrentRequest(requestId)) {
      loadingNode.remove();
      return;
    }

    loadingNode.remove();
    state.sessionId = normalizeSessionId(result.session_id) || sentSessionId;
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
    announceRequestStatus("Respuesta recibida.");
  } catch (error) {
    if (!isCurrentRequest(requestId)) {
      loadingNode.remove();
      return;
    }

    loadingNode.remove();
    const message = describeRequestError(error, activeRequest.cancelReason);
    addStoredMessage({role: "error", text: message});
    showToast(message, activeRequest.cancelReason === "user" ? "info" : "error");
    announceRequestStatus(message);
  } finally {
    window.clearTimeout(activeRequest.timeoutId);
    if (isCurrentRequest(requestId)) {
      state.activeRequest = null;
      setSending(false);
      input.focus();
    }
  }
}

function cancelActiveRequest() {
  const activeRequest = state.activeRequest;
  if (!activeRequest || activeRequest.controller.signal.aborted) {
    return;
  }

  activeRequest.cancelReason = "user";
  announceRequestStatus("Cancelando consulta…");
  activeRequest.controller.abort("user");
}

function isCurrentRequest(requestId) {
  return state.activeRequest?.id === requestId;
}

function describeRequestError(error, cancelReason) {
  if (error?.name === "AbortError") {
    if (cancelReason === "user") {
      return "Consulta cancelada.";
    }
    return "La consulta superó el tiempo máximo de espera. Puedes volver a intentarlo.";
  }
  return error.userMessage || error.message || "No se pudo completar la consulta.";
}

function announceRequestStatus(message) {
  elements["request-status"].textContent = message;
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
  article.setAttribute("role", "status");
  article.setAttribute("aria-label", "El Juez está consultando las fuentes");

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

    const scryfallUrl = getTrustedScryfallUrl(card.scryfall_uri);
    if (scryfallUrl) {
      const link = document.createElement("a");
      link.className = "evidence-link";
      link.href = scryfallUrl;
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
  state.messages = state.messages.slice(-MAX_STORED_MESSAGES);
  writeStorage(STORAGE.transcript, state.messages);
  renderMessage(message);
}

function resetConversation() {
  state.sessionId = null;
  state.messages = [];
  state.lastResult = null;

  removeStorage(STORAGE.session);
  removeStorage(STORAGE.transcript);
  removeStorage(STORAGE.lastResult);

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
  const sessionId = normalizeSessionId(state.sessionId);
  elements["session-label"].textContent = sessionId
    ? `Sesión ${sessionId.slice(0, 8)}`
    : "Sesión nueva";
}

function setSending(value) {
  state.sending = value;
  elements["send-button"].disabled = value;
  elements["send-button"].hidden = value;
  elements["cancel-request-button"].hidden = !value;
  elements["new-session-button"].disabled = value;
  elements["question-input"].disabled = value;
  elements["question-form"].setAttribute("aria-busy", String(value));
  elements["message-list"].setAttribute("aria-busy", String(value));
  if (value) {
    announceRequestStatus("Consulta enviada. El Juez está consultando las fuentes.");
  }
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

function showToast(message, kind = "error") {
  const toast = document.createElement("div");
  toast.className = `toast is-${kind}`;
  toast.textContent = message;
  elements["toast-region"].appendChild(toast);
  window.setTimeout(() => toast.remove(), 5500);
}

function loadStoredSession() {
  const value = readStorage(STORAGE.session, null);
  const normalized = normalizeSessionId(value);
  if (value !== null && normalized === null) {
    removeStorage(STORAGE.session);
  }
  return normalized;
}

function loadStoredMessages() {
  const value = readStorage(STORAGE.transcript, []);
  if (!Array.isArray(value)) {
    removeStorage(STORAGE.transcript);
    return [];
  }

  const messages = value
    .filter(isValidStoredMessage)
    .map(message => ({
      role: message.role,
      text: message.text,
      ...(typeof message.status === "string" ? {status: message.status} : {}),
    }))
    .slice(-MAX_STORED_MESSAGES);

  if (messages.length !== value.length) {
    writeStorage(STORAGE.transcript, messages);
  }
  return messages;
}

function loadStoredResult() {
  const value = readStorage(STORAGE.lastResult, null);
  if (value === null) {
    return null;
  }
  if (!isRecord(value) || typeof value.answer !== "string" || typeof value.status !== "string") {
    removeStorage(STORAGE.lastResult);
    return null;
  }
  return value;
}

function normalizeSessionId(value) {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized && normalized.length <= 256 ? normalized : null;
}

function isValidStoredMessage(value) {
  return isRecord(value)
    && ALLOWED_MESSAGE_ROLES.has(value.role)
    && typeof value.text === "string"
    && (value.status === undefined || typeof value.status === "string");
}

function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function readStorage(key, fallback) {
  if (!storageAvailable) {
    return fallback;
  }

  try {
    const raw = localStorage.getItem(key);
    if (raw === null) {
      return fallback;
    }
    return JSON.parse(raw);
  } catch (error) {
    if (error instanceof SyntaxError) {
      removeStorage(key);
    } else {
      markStorageUnavailable();
    }
    return fallback;
  }
}

function writeStorage(key, value) {
  if (!storageAvailable) {
    return false;
  }

  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    markStorageUnavailable();
    return false;
  }
}

function removeStorage(key) {
  if (!storageAvailable) {
    return false;
  }

  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    markStorageUnavailable();
    return false;
  }
}

function markStorageUnavailable() {
  storageAvailable = false;
  storageWarningPending = true;
  flushStorageWarning();
}

function flushStorageWarning() {
  if (!storageWarningPending || storageWarningShown || !elements["toast-region"]) {
    return;
  }

  storageWarningPending = false;
  storageWarningShown = true;
  const message = "El navegador no permite guardar el historial local. La conversación seguirá funcionando, pero no persistirá al recargar.";
  showToast(message, "warning");
  announceRequestStatus(message);
}

function getTrustedScryfallUrl(value) {
  if (typeof value !== "string" || !value.trim()) {
    return null;
  }

  try {
    const url = new URL(value);
    const hostname = url.hostname.toLowerCase();
    if (url.protocol !== "https:" || !["scryfall.com", "www.scryfall.com"].includes(hostname)) {
      return null;
    }
    return url.href;
  } catch (error) {
    return null;
  }
}
