"use strict";

const STORAGE = {
  session: "magicai.ui.session.v1",
  transcript: "magicai.ui.transcript.v1",
  lastResult: "magicai.ui.lastResult.v1",
  profile: "magicai.ui.profile.v1",
};

const ASK_TIMEOUT_MS = 180000;
const AUXILIARY_TIMEOUT_MS = 10000;
const MAX_STORED_MESSAGES = 40;
const MAX_DISAMBIGUATION_CANDIDATES = 8;
const ALLOWED_MESSAGE_ROLES = new Set(["user", "assistant", "error"]);

let storageAvailable = true;
let storageWarningPending = false;
let storageWarningShown = false;

const STATUS_LABELS = {
  answered: "Respondido",
  needs_clarification: "Necesita aclaración",
  strategy_required: "Requiere Estratega",
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
  tactician_strategy: "Análisis estratégico",
  tactician_judge_gate: "Respuesta factual del Juez",
  tactician_repair: "Reparación revisada",
  llm_validated: "LLM validado",
  safe_fallback: "Fallback seguro",
};

const STATUS_EXPLANATIONS = {
  answered: "El Juez ha respondido usando la evidencia recuperada y la ruta indicada.",
  needs_clarification: "Hay varias cartas compatibles. Elige una opción para continuar la pregunta original.",
  strategy_required: "Los hechos están validados, pero la recomendación final corresponde al Estratega.",
  insufficient_evidence: "Las fuentes disponibles no bastan para responder con seguridad.",
  false_premise: "El Juez ha corregido una premisa incompatible con Oracle o las reglas antes de responder.",
};

const elements = {};

const state = {
  sessionId: loadStoredSession(),
  messages: loadStoredMessages(),
  lastResult: loadStoredResult(),
  profile: loadStoredProfile(),
  sending: false,
  metadata: null,
  activeRequest: null,
  requestSequence: 0,
  healthRequestPending: false,
  conversations: [],
  historyLoading: false,
};

document.addEventListener("DOMContentLoaded", () => {
  captureElements();
  bindEvents();
  flushStorageWarning();
  restoreState();
  void loadMetadata();
  void refreshHealth();
  void loadConversationHistory();
  window.setInterval(refreshHealth, 30000);
});

function captureElements() {
  const ids = [
    "health-badge",
    "health-label",
    "new-session-button",
    "refresh-history-button",
    "history-status",
    "conversation-list",
    "session-label",
    "profile-eyebrow",
    "conversation-title",
    "question-label",
    "judge-profile-button",
    "tactician-profile-button",
    "message-list",
    "welcome-message",
    "question-form",
    "question-input",
    "send-button",
    "cancel-request-button",
    "request-status",
    "result-status",
    "result-summary",
    "result-actions",
    "copy-answer-button",
    "copy-evidence-button",
    "export-result-button",
    "export-feedback-button",
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
  elements["refresh-history-button"].addEventListener("click", () => void loadConversationHistory());
  elements["cancel-request-button"].addEventListener("click", cancelActiveRequest);
  elements["copy-answer-button"].addEventListener("click", () => void copyLastAnswer());
  elements["copy-evidence-button"].addEventListener("click", () => void copyLastEvidence());
  elements["export-result-button"].addEventListener("click", exportLastResult);
  elements["export-feedback-button"].addEventListener("click", exportFeedbackCase);
  elements["judge-profile-button"].addEventListener("click", () => setProfile("judge"));
  elements["tactician-profile-button"].addEventListener("click", () => setProfile("tactician"));

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

  updateProfileUI();
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

    const endpoint = state.profile === "tactician" ? "/tactician/ask" : "/ask";
    const result = await fetchJson(endpoint, {
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

    markClarificationResolved(question);
    const candidates = getClarificationCandidates(result);
    addStoredMessage({
      role: "assistant",
      text: result.answer || "MagicAI no devolvió texto.",
      status: result.status,
      profile: result.authority === "tactician" ? "tactician" : state.profile,
      ...(candidates.length ? {candidates} : {}),
    });
    renderEvidence(result);
    updateSessionLabel();
    renderConversationHistory();
    void loadConversationHistory({silent: true});
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
  header.textContent = message.role === "user"
    ? "Tú"
    : message.role === "error"
      ? "Error"
      : message.profile === "tactician" ? "Estratega" : "Juez";

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

  const candidates = normalizeCandidates(message.candidates);
  if (message.role === "assistant" && candidates.length) {
    article.appendChild(renderDisambiguationActions(candidates, message.selectedCandidate));
  }
  elements["message-list"].appendChild(article);

  if (shouldScroll) {
    scrollMessagesToEnd();
  }

  return article;
}

function renderDisambiguationActions(candidates, selectedCandidate = null) {
  const container = document.createElement("div");
  container.className = "clarification-actions";
  if (selectedCandidate) {
    container.classList.add("is-resolved");
  }
  container.setAttribute("aria-label", "Opciones de carta para aclarar la consulta");

  const label = document.createElement("p");
  label.className = "clarification-label";
  label.textContent = "Selecciona la carta:";
  container.appendChild(label);

  const options = document.createElement("div");
  options.className = "clarification-options";

  for (const candidate of candidates) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "clarification-option";
    button.textContent = candidate;
    button.dataset.resolved = String(Boolean(selectedCandidate));
    button.disabled = state.sending || Boolean(selectedCandidate);
    button.classList.toggle("is-selected", candidate === selectedCandidate);
    button.setAttribute("aria-label", candidate === selectedCandidate
      ? `Opción seleccionada: ${candidate}`
      : `Continuar con ${candidate}`);
    button.addEventListener("click", () => submitClarificationCandidate(candidate));
    options.appendChild(button);
  }

  container.appendChild(options);
  return container;
}

function markClarificationResolved(candidate) {
  if (typeof candidate !== "string") {
    return;
  }

  const normalized = candidate.trim();
  for (let index = state.messages.length - 1; index >= 0; index -= 1) {
    const message = state.messages[index];
    const candidates = normalizeCandidates(message.candidates);
    if (!candidates.includes(normalized) || message.selectedCandidate) {
      continue;
    }

    message.selectedCandidate = normalized;
    writeStorage(STORAGE.transcript, state.messages);

    const actionGroups = [...document.querySelectorAll(".clarification-actions:not(.is-resolved)")];
    const actionGroup = actionGroups.at(-1);
    if (actionGroup) {
      actionGroup.classList.add("is-resolved");
      for (const button of actionGroup.querySelectorAll(".clarification-option")) {
        const selected = button.textContent.trim() === normalized;
        button.dataset.resolved = "true";
        button.disabled = true;
        button.classList.toggle("is-selected", selected);
        button.setAttribute("aria-label", selected
          ? `Opción seleccionada: ${normalized}`
          : `Opción descartada: ${button.textContent.trim()}`);
      }
    }
    return;
  }
}

function submitClarificationCandidate(candidate) {
  if (state.sending || typeof candidate !== "string" || !candidate.trim()) {
    return;
  }

  elements["question-input"].value = candidate.trim();
  autoResizeTextarea();
  void submitQuestion();
}

function getClarificationCandidates(result) {
  if (result?.status !== "needs_clarification") {
    return [];
  }

  return normalizeCandidates((result.cards || []).map(card => card?.name));
}

function normalizeCandidates(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  return [...new Set(
    value
      .filter(candidate => typeof candidate === "string")
      .map(candidate => candidate.trim())
      .filter(Boolean),
  )].slice(0, MAX_DISAMBIGUATION_CANDIDATES);
}

function renderLoadingMessage() {
  const article = document.createElement("article");
  article.className = "message is-assistant";
  article.setAttribute("role", "status");
  const profileLabel = state.profile === "tactician" ? "Estratega" : "Juez";
  article.setAttribute("aria-label", `${profileLabel} está procesando la consulta`);

  const header = document.createElement("div");
  header.className = "message-header";
  header.textContent = state.profile === "tactician"
    ? "Estratega · consultando al Juez"
    : "Juez · consultando fuentes";

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

  const explanation = document.createElement("p");
  explanation.className = "status-explanation";
  explanation.textContent = result.authority === "tactician"
    ? "El Estratega ha usado exclusivamente la base factual entregada por el Juez."
    : STATUS_EXPLANATIONS[status] || "Resultado estructurado del Juez.";
  summary.appendChild(explanation);

  const row = document.createElement("div");
  row.className = "status-row";
  row.append(
    createPill(ORIGIN_LABELS[result.origin] || result.origin || "Origen desconocido"),
    createPill(`Confianza: ${translateConfidence(result.confidence)}`, `is-${result.confidence || "unknown"}`),
    createPill(`Autoridad: ${result.authority || "judge"}`),
  );
  if (result.combo_classification) {
    row.appendChild(createPill(`Combo: ${result.combo_classification}`));
  }
  summary.appendChild(row);

  if ((result.combo_steps || []).length || (result.outcomes || []).length) {
    summary.appendChild(renderStrategySummary(result));
  }

  elements["evidence-sections"].hidden = false;
  setResultActionsEnabled(true);

  const cards = result.cards || [];
  const rules = result.rules || [];
  const rulings = result.rulings || [];
  const assumptions = result.assumptions || [];
  const warnings = [
    ...(result.warnings || []),
    ...(result.risks || []),
    ...(result.review_challenges || []).map(item => item.message || item.code).filter(Boolean),
  ];

  renderCards(cards);
  renderRules(rules);
  renderRulings(rulings);
  renderNotes("assumptions", assumptions, "No se declararon supuestos.");
  renderNotes("warnings", warnings, "No hay advertencias.");
  renderTechnicalDetails(result);
  configureEvidenceSections({cards, rules, rulings, assumptions, warnings, result});
}


function renderStrategySummary(result) {
  const container = document.createElement("section");
  container.className = "strategy-summary";

  if ((result.combo_steps || []).length) {
    const title = document.createElement("h3");
    title.textContent = "Línea validada";
    container.appendChild(title);
    const list = document.createElement("ol");
    for (const step of result.combo_steps) {
      const item = document.createElement("li");
      item.textContent = step;
      list.appendChild(item);
    }
    container.appendChild(list);
  }

  if ((result.outcomes || []).length) {
    const title = document.createElement("h3");
    title.textContent = "Resultado por ciclo";
    container.appendChild(title);
    const list = document.createElement("ul");
    for (const outcome of result.outcomes) {
      const item = document.createElement("li");
      item.textContent = outcome;
      list.appendChild(item);
    }
    container.appendChild(list);
  }

  return container;
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

    const header = document.createElement("div");
    header.className = "evidence-card-header";

    const title = document.createElement("h3");
    title.textContent = card.name || "Carta sin nombre";
    header.appendChild(title);

    if (card.mana_cost) {
      const mana = document.createElement("span");
      mana.className = "card-mana-cost";
      mana.textContent = card.mana_cost;
      header.appendChild(mana);
    }
    node.appendChild(header);

    if (card.type_line) {
      const typeLine = document.createElement("p");
      typeLine.className = "card-type-line";
      typeLine.textContent = card.type_line;
      node.appendChild(typeLine);
    }

    if (card.oracle_text) {
      const oracle = document.createElement("p");
      oracle.className = "oracle-text";
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
    node.className = "evidence-card rule-card";

    if (rule.number) {
      const number = document.createElement("span");
      number.className = "rule-number";
      number.textContent = rule.number;
      node.appendChild(number);
    }

    const title = document.createElement("h3");
    title.textContent = rule.title || "Regla recuperada";
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
    metadata.className = "ruling-meta";
    metadata.textContent = [ruling.published_at, String(ruling.source || "").toUpperCase()].filter(Boolean).join(" · ");
    node.appendChild(metadata);

    const comment = document.createElement("p");
    comment.className = "ruling-comment";
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
    node.className = `evidence-note is-${kind}`;
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
    ["Intent estratégico", result.strategy_intent || "—"],
    ["Clasificación de combo", result.combo_classification || "—"],
    ["Cartas heredadas", (result.inherited_cards || []).join(" · ") || "—"],
    ["Resultados", (result.outcomes || []).join(" · ") || "—"],
    ["Consultas al Juez", (result.judge_queries || []).map(item => `${item.sequence}: ${item.purpose}`).join(" · ") || "—"],
    ["Herramientas del Juez", (result.judge_tool_calls || []).map(item => `${item.tool}: ${item.status}${item.cache_hit ? " (caché)" : ""}`).join(" · ") || "—"],
    ["Síntesis del Estratega", result.tactician_synthesized ? "sí" : "no"],
    ["Input analizado", result.input_analysis?.speech_act || "—"],
    ["Afirmaciones evaluadas", String((result.claim_verdicts || []).length)],
    ["Consultas planificadas", String(result.queries_planned ?? 0)],
    ["Consultas completadas", String(result.queries_completed ?? 0)],
    ["Verificado por evidencia", result.judge_verified ? "sí" : "no"],
    ["Resumen de razonamiento", (result.reasoning_summary || []).join(" · ") || "—"],
    ["Intentos de validación", String(result.validation_attempts ?? 0)],
    ["Revisado por", (result.reviewed_by || []).join(" · ") || "—"],
    ["Trazado de autoridad", (result.authority_trace || []).join(" → ") || "—"],
    ["Sinergias", (result.synergies || []).join(" · ") || "—"],
    ["Consultas de recuperación", (result.retrieval_queries || []).join(" · ") || "—"],
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

function configureEvidenceSections({cards, rules, rulings, assumptions, warnings, result}) {
  const configuration = [
    ["cards-section", cards.length, cards.length > 0],
    ["rules-section", rules.length, rules.length > 0],
    ["rulings-section", rulings.length, rulings.length > 0],
    ["assumptions-section", assumptions.length, assumptions.length > 0],
    ["warnings-section", warnings.length, warnings.length > 0],
    ["sources-section", 1, false],
  ];

  for (const [id, count, shouldOpen] of configuration) {
    const section = document.getElementById(id);
    if (!section) {
      continue;
    }
    section.classList.toggle("is-empty", count === 0);
    section.open = Boolean(shouldOpen);
  }

  if (result.status === "needs_clarification") {
    document.getElementById("cards-section").open = true;
  }
}

function setResultActionsEnabled(enabled) {
  for (const id of ["copy-answer-button", "copy-evidence-button", "export-result-button", "export-feedback-button"]) {
    elements[id].disabled = !enabled;
  }
}

async function copyLastAnswer() {
  const answer = state.lastResult?.answer;
  if (!answer) {
    showToast("No hay una respuesta para copiar.", "warning");
    return;
  }

  const copied = await copyText(answer);
  showToast(copied ? "Respuesta copiada." : "No se pudo copiar la respuesta.", copied ? "info" : "error");
}

async function copyLastEvidence() {
  if (!state.lastResult) {
    showToast("No hay evidencia para copiar.", "warning");
    return;
  }

  const copied = await copyText(buildEvidenceText(state.lastResult));
  showToast(copied ? "Respuesta y evidencia copiadas." : "No se pudo copiar la evidencia.", copied ? "info" : "error");
}

async function copyText(text) {
  const value = String(text || "");
  if (!value) {
    return false;
  }

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch (error) {
    // Fall back to the local textarea method below.
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "");
  textarea.className = "clipboard-fallback";
  document.body.appendChild(textarea);
  textarea.select();
  textarea.setSelectionRange(0, value.length);

  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (error) {
    copied = false;
  } finally {
    textarea.remove();
  }
  return copied;
}

function exportLastResult() {
  if (!state.lastResult) {
    showToast("No hay un resultado para exportar.", "warning");
    return;
  }

  downloadJson(
    state.lastResult,
    `magicai-judge-result-${formatExportTimestamp(new Date())}.json`,
  );
  showToast("JudgeResult exportado en JSON.", "info");
}

function exportFeedbackCase() {
  const userMessages = state.messages
    .filter(message => message?.role === "user" && typeof message.text === "string")
    .map(message => message.text.trim())
    .filter(Boolean);

  if (!userMessages.length || !state.lastResult) {
    showToast("No hay una conversación para convertir en caso Gauntlet.", "warning");
    return;
  }

  const now = new Date();
  const timestamp = formatExportTimestamp(now);
  const caseId = `CF-UI-${timestamp}`;
  const firstQuestion = userMessages[0];
  const payload = {
    schema_version: "1.0",
    artifact_purpose: "evaluation",
    training_allowed: false,
    automatic_learning: false,
    automatic_promotion: false,
    id: caseId,
    title: buildFeedbackTitle(firstQuestion),
    mode: "exploratory",
    source: {
      platform: "manual",
      url: "",
      topic_id: "",
      published_at: "",
      retrieved_at: now.toISOString(),
      paraphrased: true,
      contains_verbatim_quote: false,
      contains_personal_data: false,
      notes: "Generado desde una conversación local de la UI. Verifica que las preguntas estén parafraseadas antes de ejecutar o compartir el caso.",
    },
    review: {
      status: "unreviewed",
      rules_version: "",
      validated_at: "",
      expected_summary: "",
      notes: `Último JudgeResult observado: status=${state.lastResult.status || ""}; origin=${state.lastResult.origin || ""}. Describe aquí por qué sospechas que la respuesta necesita revisión.`,
    },
    tags: ["ui-feedback", "manual-feedback"],
    turns: userMessages.map((question, index) => ({
      id: `${caseId}-${String(index + 1).padStart(2, "0")}`,
      question,
      notes: "",
    })),
  };

  downloadJson(payload, `magicai-community-feedback-${timestamp}.json`);
  showToast("Caso exploratorio Gauntlet exportado.", "info");
}

function buildFeedbackTitle(question) {
  const normalized = String(question || "")
    .replace(/\s+/g, " ")
    .trim();
  if (!normalized) {
    return "Caso manual desde la UI";
  }
  return normalized.length <= 90 ? normalized : `${normalized.slice(0, 87)}…`;
}

function downloadJson(value, filename) {
  const payload = JSON.stringify(value, null, 2);
  const blob = new Blob([payload], {type: "application/json;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function formatExportTimestamp(date) {
  const parts = [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
    "-",
    String(date.getHours()).padStart(2, "0"),
    String(date.getMinutes()).padStart(2, "0"),
    String(date.getSeconds()).padStart(2, "0"),
  ];
  return parts.join("");
}

function buildEvidenceText(result) {
  const lines = [
    "MagicAI Judge",
    "",
    `Pregunta: ${result.question || "—"}`,
    "",
    "Respuesta:",
    result.answer || "—",
    "",
    `Estado: ${STATUS_LABELS[result.status] || result.status || "—"}`,
    `Origen: ${ORIGIN_LABELS[result.origin] || result.origin || "—"}`,
    `Confianza: ${translateConfidence(result.confidence)}`,
    `Autoridad: ${result.authority || "judge"}`,
  ];

  appendEvidenceTextSection(lines, "Cartas", (result.cards || []).map(card => {
    const identity = [card.name, card.mana_cost, card.type_line].filter(Boolean).join(" · ");
    return card.oracle_text ? `${identity}\n  ${card.oracle_text}` : identity;
  }));
  appendEvidenceTextSection(lines, "Reglas", (result.rules || []).map(rule => [rule.number, rule.title].filter(Boolean).join(" · ")));
  appendEvidenceTextSection(lines, "Rulings", (result.rulings || []).map(ruling => {
    const metadata = [ruling.card_name, ruling.published_at, ruling.source].filter(Boolean).join(" · ");
    return `${metadata}\n  ${ruling.comment || ""}`.trimEnd();
  }));
  appendEvidenceTextSection(lines, "Consultas de recuperación", result.retrieval_queries || []);
  appendEvidenceTextSection(lines, "Supuestos", result.assumptions || []);
  appendEvidenceTextSection(lines, "Advertencias", result.warnings || []);
  appendEvidenceTextSection(lines, "Versiones de fuentes", Object.entries(result.source_versions || {}).map(
    ([key, value]) => `${formatKey(key)}: ${value}`,
  ));

  const sourceHealth = result.source_health || {};
  if (sourceHealth.status) {
    lines.push("", `Salud de fuentes: ${sourceHealth.status}`);
  }

  return lines.join("\n").trim();
}

function appendEvidenceTextSection(lines, title, entries) {
  const values = entries.filter(entry => typeof entry === "string" && entry.trim());
  if (!values.length) {
    return;
  }

  lines.push("", `${title}:`);
  for (const value of values) {
    lines.push(`- ${value}`);
  }
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

async function loadConversationHistory({silent = false} = {}) {
  if (state.historyLoading) {
    return;
  }

  state.historyLoading = true;
  elements["refresh-history-button"].disabled = true;
  if (!silent) {
    elements["history-status"].textContent = "Actualizando historial…";
  }

  try {
    const conversations = await fetchJson("/conversations?limit=50");
    state.conversations = Array.isArray(conversations) ? conversations : [];
    renderConversationHistory();
    elements["history-status"].textContent = state.conversations.length
      ? `${state.conversations.length} conversación${state.conversations.length === 1 ? "" : "es"} guardada${state.conversations.length === 1 ? "" : "s"}`
      : "Aún no hay conversaciones guardadas.";
  } catch (error) {
    elements["history-status"].textContent = "No se pudo cargar el historial local.";
    if (!silent) {
      showToast(error.userMessage || error.message || "No se pudo cargar el historial.", "error");
    }
  } finally {
    state.historyLoading = false;
    elements["refresh-history-button"].disabled = state.sending;
  }
}

function renderConversationHistory() {
  const container = elements["conversation-list"];
  if (!container) {
    return;
  }

  clearNode(container);

  if (!state.conversations.length) {
    const empty = document.createElement("p");
    empty.className = "history-empty";
    empty.textContent = "Las conversaciones aparecerán aquí después de la primera respuesta.";
    container.appendChild(empty);
    return;
  }

  for (const conversation of state.conversations) {
    if (!isRecord(conversation) || !normalizeSessionId(conversation.session_id)) {
      continue;
    }

    const item = document.createElement("article");
    item.className = "conversation-item";
    if (conversation.session_id === state.sessionId) {
      item.classList.add("is-active");
    }

    const openButton = document.createElement("button");
    openButton.className = "conversation-open";
    openButton.type = "button";
    openButton.disabled = state.sending;
    openButton.addEventListener("click", () => void openConversation(conversation.session_id));

    const title = document.createElement("strong");
    title.textContent = conversation.title || "Conversación sin título";
    const metadata = document.createElement("span");
    metadata.textContent = `${conversation.message_count || 0} mensajes · ${formatConversationDate(conversation.updated_at)}`;
    openButton.append(title, metadata);

    const actions = document.createElement("div");
    actions.className = "conversation-actions";

    const renameButton = document.createElement("button");
    renameButton.className = "conversation-action";
    renameButton.type = "button";
    renameButton.textContent = "✎";
    renameButton.title = "Renombrar conversación";
    renameButton.setAttribute("aria-label", `Renombrar ${conversation.title || "conversación"}`);
    renameButton.disabled = state.sending;
    renameButton.addEventListener("click", () => void renameConversation(conversation));

    const deleteButton = document.createElement("button");
    deleteButton.className = "conversation-action is-danger";
    deleteButton.type = "button";
    deleteButton.textContent = "×";
    deleteButton.title = "Eliminar conversación";
    deleteButton.setAttribute("aria-label", `Eliminar ${conversation.title || "conversación"}`);
    deleteButton.disabled = state.sending;
    deleteButton.addEventListener("click", () => void deleteConversation(conversation));

    actions.append(renameButton, deleteButton);
    item.append(openButton, actions);
    container.appendChild(item);
  }
}

async function openConversation(sessionId, {quiet = false} = {}) {
  const normalized = normalizeSessionId(sessionId);
  if (!normalized || state.sending) {
    return;
  }

  try {
    const detail = await fetchJson(`/conversations/${encodeURIComponent(normalized)}`);
    const messages = Array.isArray(detail.messages)
      ? detail.messages
        .filter(message => isRecord(message) && ["user", "assistant"].includes(message.role) && typeof message.content === "string")
        .map(message => ({role: message.role, text: message.content}))
        .slice(-MAX_STORED_MESSAGES)
      : [];

    const lastResult = isRecord(detail.last_result) ? detail.last_result : null;
    if (lastResult && messages.length) {
      const lastAssistant = [...messages].reverse().find(message => message.role === "assistant");
      if (lastAssistant) {
        lastAssistant.status = lastResult.status;
        const candidates = getClarificationCandidates(lastResult);
        if (candidates.length) {
          lastAssistant.candidates = candidates;
        }
      }
    }

    state.sessionId = normalized;
    state.messages = messages;
    state.lastResult = lastResult;
    writeStorage(STORAGE.session, state.sessionId);
    writeStorage(STORAGE.transcript, state.messages);
    writeStorage(STORAGE.lastResult, state.lastResult);
    renderCurrentConversation();
    renderConversationHistory();
    if (!quiet) {
      showToast("Conversación recuperada desde el historial local.", "info");
    }
  } catch (error) {
    showToast(error.userMessage || error.message || "No se pudo abrir la conversación.", "error");
  }
}

function renderCurrentConversation() {
  clearNode(elements["message-list"]);

  if (state.messages.length) {
    for (const message of state.messages) {
      renderMessage(message, false);
    }
  } else {
    const welcome = buildWelcomeClone();
    elements["message-list"].appendChild(welcome);
    bindSuggestionButtons(welcome);
  }

  if (state.lastResult) {
    renderEvidence(state.lastResult);
  } else {
    elements["result-status"].className = "status-badge is-idle";
    elements["result-status"].textContent = "Sin respuesta";
    elements["result-summary"].textContent = "La evidencia de la última respuesta aparecerá aquí.";
    elements["evidence-sections"].hidden = true;
    setResultActionsEnabled(false);
  }

  updateSessionLabel();
  scrollMessagesToEnd();
}

async function renameConversation(conversation) {
  const currentTitle = String(conversation.title || "").trim();
  const requested = window.prompt("Nuevo título de la conversación:", currentTitle);
  if (requested === null) {
    return;
  }
  const title = requested.trim();
  if (!title || title === currentTitle) {
    return;
  }

  try {
    await fetchJson(`/conversations/${encodeURIComponent(conversation.session_id)}`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({title}),
    });
    await loadConversationHistory({silent: true});
    showToast("Conversación renombrada.", "info");
  } catch (error) {
    showToast(error.userMessage || error.message || "No se pudo renombrar la conversación.", "error");
  }
}

async function deleteConversation(conversation) {
  const title = conversation.title || "esta conversación";
  if (!window.confirm(`¿Eliminar “${title}”? Esta acción no se puede deshacer.`)) {
    return;
  }

  try {
    await fetchJson(`/conversations/${encodeURIComponent(conversation.session_id)}`, {
      method: "DELETE",
    });
    if (conversation.session_id === state.sessionId) {
      resetConversation();
    }
    await loadConversationHistory({silent: true});
    showToast("Conversación eliminada.", "info");
  } catch (error) {
    showToast(error.userMessage || error.message || "No se pudo eliminar la conversación.", "error");
  }
}

function formatConversationDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "fecha desconocida";
  }
  return new Intl.DateTimeFormat("es", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
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
  setResultActionsEnabled(false);
  updateSessionLabel();
  renderConversationHistory();
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
  description.textContent = state.profile === "tactician"
    ? "El Estratega no consulta fuentes por su cuenta: solicita al Juez un paquete factual y propone líneas, sinergias y riesgos sobre esa base."
    : "El Juez recupera Oracle, Comprehensive Rules y rulings locales antes de responder.";

  const suggestions = document.createElement("div");
  suggestions.className = "suggestion-grid";
  suggestions.setAttribute("aria-label", "Preguntas de ejemplo");

  const examples = state.profile === "tactician"
    ? [
        "¿Young Wolf y Carrion Feeder forman un combo o una sinergia?",
        "¿Qué papel cumple Sol Ring en este plan de juego?",
        "¿Qué riesgos tiene esta línea de sacrificio?",
      ]
    : [
        "¿Puedo responder durante la resolución de una habilidad?",
        "¿Cuántos Kobolds crea Prossh?",
        "¿Qué ocurre si sacrifico Young Wolf?",
      ];

  for (const text of examples) {
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
  elements["refresh-history-button"].disabled = value;
  elements["judge-profile-button"].disabled = value;
  elements["tactician-profile-button"].disabled = value;
  elements["question-input"].disabled = value;
  for (const button of document.querySelectorAll(".conversation-action, .conversation-open")) {
    button.disabled = value;
  }
  elements["question-form"].setAttribute("aria-busy", String(value));
  elements["message-list"].setAttribute("aria-busy", String(value));
  for (const button of document.querySelectorAll(".clarification-option")) {
    button.disabled = value || button.dataset.resolved === "true";
  }
  if (value) {
    announceRequestStatus(state.profile === "tactician"
      ? "Consulta enviada. El Estratega está solicitando hechos al Juez."
      : "Consulta enviada. El Juez está consultando las fuentes.");
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

function setProfile(profile) {
  if (!new Set(["judge", "tactician"]).has(profile) || state.sending) {
    return;
  }
  state.profile = profile;
  writeStorage(STORAGE.profile, profile);
  updateProfileUI();

  if (!state.messages.length) {
    clearNode(elements["message-list"]);
    const welcome = buildWelcomeClone();
    elements["message-list"].appendChild(welcome);
    bindSuggestionButtons(welcome);
  }
  elements["question-input"].focus();
}

function updateProfileUI() {
  const tacticianActive = state.profile === "tactician";
  elements["judge-profile-button"].classList.toggle("is-active", !tacticianActive);
  elements["judge-profile-button"].setAttribute("aria-pressed", String(!tacticianActive));
  elements["tactician-profile-button"].classList.toggle("is-active", tacticianActive);
  elements["tactician-profile-button"].setAttribute("aria-pressed", String(tacticianActive));
  elements["profile-eyebrow"].textContent = tacticianActive ? "Autoridad estratégica" : "Autoridad factual";
  elements["conversation-title"].textContent = tacticianActive ? "Consulta al Estratega" : "Consulta al Juez";
  elements["question-label"].textContent = tacticianActive
    ? "Escribe tu consulta para el Estratega"
    : "Escribe tu pregunta para el Juez";
  elements["question-input"].placeholder = tacticianActive
    ? "Describe una jugada, sinergia o plan…"
    : "Escribe una pregunta de reglas…";
  elements["send-button"].querySelector("span").textContent = tacticianActive ? "Analizar" : "Preguntar";
}

function loadStoredProfile() {
  const value = readStorage(STORAGE.profile, "judge");
  return value === "tactician" ? "tactician" : "judge";
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
      ...(normalizeCandidates(message.candidates).length ? {candidates: normalizeCandidates(message.candidates)} : {}),
      ...(typeof message.selectedCandidate === "string" ? {selectedCandidate: message.selectedCandidate} : {}),
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
    && (value.status === undefined || typeof value.status === "string")
    && (value.candidates === undefined || Array.isArray(value.candidates))
    && (value.selectedCandidate === undefined || typeof value.selectedCandidate === "string");
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
