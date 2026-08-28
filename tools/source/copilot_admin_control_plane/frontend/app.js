const API_BASE = window.COPILOT_ADMIN_API_BASE || "";
const POLL_MS = 1500;
const CONSOLE_POLL_LIMIT = 24000;
const MAX_CONSOLE_BUFFER = 200000;
const CONSOLE_EVENT_LIMIT = 12000;
const REQUIRED_EVENTS = new Set([
  "page_view",
  "api_request_started",
  "api_request_completed",
  "api_request_failed",
  "button_clicked",
  "mode_changed",
  "ai_console_input_sent",
  "ai_console_refreshed",
  "ai_console_rendered",
  "job_created",
  "job_opened",
  "report_opened",
  "mermaid_zoom_changed",
  "mermaid_pan_changed",
  "mermaid_scroll_changed",
  "mermaid_search_changed",
  "status_diode_changed",
]);

const state = {
  sessionId: crypto.randomUUID?.() || `session-${Date.now()}`,
  traceId: crypto.randomUUID?.() || `trace-${Date.now()}`,
  activeView: "dashboard",
  mode: "unknown",
  copilotWindowVisible: true,
  status: null,
  tests: [],
  reports: [],
  jobs: [],
  aiConsole: null,
  aiConsoleTranscript: "",
  aiConsoleCursor: null,
  mermaid: "",
  mermaidTransform: { scale: 1, x: 0, y: 0 },
  lastDiode: "red",
  lastAiConsoleSignature: "",
  aiConsoleSending: false,
  aiConsoleStartInProgress: false,
  aiConsoleEvents: null,
  aiConsoleEventsConnected: false,
  lastAutoStartAttempt: 0,
  lastAiConsoleEventAt: null,
  lastAiConsoleInput: null,
  lastAiConsoleRender: null,
  logs: [],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

document.addEventListener("DOMContentLoaded", () => {
  bindNavigation();
  bindModeControls();
  bindRegressionControls();
  bindMermaidControls();
  bindAiConsole();
  bindReportFilter();
  bindStartupControls();
  $$("[data-action='start-session'], #start-session-button").forEach((button) => button.addEventListener("click", () => startSession(button.id)));
  logEvent("page_view", { view: state.activeView });
  connectAiConsoleEvents();
  refreshAll();
  setInterval(refreshStatusAndJobs, POLL_MS);
});

function bindNavigation() {
  $$(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      state.activeView = view;
      $$(".nav-item").forEach((item) => item.classList.toggle("active", item === button));
      $$(".view").forEach((panel) => panel.classList.toggle("active", panel.id === `view-${view}`));
      logEvent("page_view", { view });
      if (view === "ai-console") ensureCopilotSession();
    });
  });
}

function bindModeControls() {
  $$("#learning-mode-button, #testing-mode-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const mode = button.dataset.mode;
      logEvent("button_clicked", { button_id: button.id, user_action: "set_mode", mode });
      logEvent("mode_changed", { mode });
      const job = await createApiJob("/api/copilot/mode", { mode }, () => mockJob("mode", mode));
      state.mode = mode;
      if (job) addOrUpdateJob(job);
      renderAll();
    });
  });
}

function bindRegressionControls() {
  $("#run-all-button").addEventListener("click", async () => {
    logEvent("button_clicked", { button_id: "run-all-button", user_action: "run_all_regressions" });
    const job = await createApiJob("/api/regression/run", { scope: "all" }, () => mockJob("regression", "all regression tests"));
    if (job) addOrUpdateJob(job);
    renderAll();
  });
  $("#run-selected-button").addEventListener("click", async () => {
    const testId = $("#regression-select").value;
    logEvent("button_clicked", { button_id: "run-selected-button", user_action: "run_selected_regression", test_id: testId });
    const job = await createApiJob("/api/regression/run", { scope: "selected", test_id: testId }, () => mockJob("regression", testId));
    if (job) addOrUpdateJob(job);
    renderAll();
  });
}

function bindMermaidControls() {
  $("#mermaid-zoom-in").addEventListener("click", () => setMermaidZoom(state.mermaidTransform.scale + 0.15));
  $("#mermaid-zoom-out").addEventListener("click", () => setMermaidZoom(state.mermaidTransform.scale - 0.15));
  $("#mermaid-fit").addEventListener("click", () => {
    const viewport = $("#mermaid-viewport");
    const canvas = $("#mermaid-canvas");
    const next = Math.max(0.35, Math.min(viewport.clientWidth / canvas.scrollWidth, viewport.clientHeight / canvas.scrollHeight));
    setMermaidTransform(next, 0, 0);
  });
  $("#mermaid-reset").addEventListener("click", () => setMermaidTransform(1, 0, 0));
  $("#mermaid-search").addEventListener("input", () => {
    logEvent("mermaid_search_changed", { query: $("#mermaid-search").value });
    renderMermaidGraph();
  });

  const viewport = $("#mermaid-viewport");
  let drag = null;
  viewport.addEventListener("pointerdown", (event) => {
    drag = { x: event.clientX, y: event.clientY, startX: state.mermaidTransform.x, startY: state.mermaidTransform.y };
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add("dragging");
  });
  viewport.addEventListener("pointermove", (event) => {
    if (!drag) return;
    setMermaidTransform(state.mermaidTransform.scale, drag.startX + event.clientX - drag.x, drag.startY + event.clientY - drag.y, "mermaid_pan_changed");
  });
  viewport.addEventListener("pointerup", () => {
    drag = null;
    viewport.classList.remove("dragging");
  });
  viewport.addEventListener("wheel", (event) => {
    if (!event.ctrlKey) return;
    event.preventDefault();
    setMermaidZoom(state.mermaidTransform.scale + (event.deltaY < 0 ? 0.1 : -0.1));
  }, { passive: false });
  viewport.addEventListener("scroll", () => {
    logEvent("mermaid_scroll_changed", { scroll_left: viewport.scrollLeft, scroll_top: viewport.scrollTop });
  });
}

function bindReportFilter() {
  $("#report-filter").addEventListener("input", renderReports);
}

function bindAiConsole() {
  $("#ai-console-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendAiConsoleInput();
  });
  $("#ai-console-input").addEventListener("keydown", async (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendAiConsoleInput();
    }
  });
  $("#ai-console-send-esc").addEventListener("click", async () => {
    await sendAiConsoleInput({ text: "\x1b", submit: false, clearLine: false, sourceButtonId: "ai-console-send-esc" });
  });
  $("#ai-console-send-tab").addEventListener("click", async () => {
    await sendAiConsoleInput({ text: "\t", submit: false, clearLine: false, sourceButtonId: "ai-console-send-tab" });
  });
}

function bindStartupControls() {
  $("#copilot-window-visible-toggle").addEventListener("change", (event) => {
    state.copilotWindowVisible = event.target.checked;
    logEvent("button_clicked", {
      button_id: "copilot-window-visible-toggle",
      user_action: "toggle_copilot_window_visibility",
      hidden_window: !state.copilotWindowVisible,
    });
    renderAiConsole();
  });
}

async function refreshAll() {
  await Promise.allSettled([
    refreshStatusAndJobs(),
    loadTests(),
    loadMermaid(),
    loadReports(),
  ]);
  renderAll();
}

async function refreshStatusAndJobs() {
  const requests = [
    apiGet("/api/status", mockStatus),
    apiGet("/api/jobs", () => ({ jobs: state.jobs.length ? state.jobs : mockJobs() })),
  ];
  if (!state.aiConsoleEventsConnected) {
    const aiConsolePath = state.aiConsoleCursor === null
      ? `/api/ai-console?limit=${CONSOLE_POLL_LIMIT}`
      : `/api/ai-console?cursor=${state.aiConsoleCursor}&limit=${CONSOLE_POLL_LIMIT}`;
    requests.push(apiGet(aiConsolePath, mockAiConsole));
  }
  const [status, jobs, aiConsoleState] = await Promise.all(requests);
  const copilot = status?.copilot_session || status?.copilot || {};
  const browser = status?.browser_session || status?.browser || {};
  state.status = { ...status, copilot_session: copilot, browser_session: browser, copilot, browser };
  state.jobs = normalizeArray(jobs.jobs || jobs);
  if (aiConsoleState) {
    mergeAiConsoleState(aiConsoleState);
  } else if (state.aiConsole) {
    state.aiConsole = { ...state.aiConsole, ...copilot };
  }
  if (status?.mode) state.mode = status.mode;
  if (isCopilotOnline(state.aiConsole || {})) state.aiConsoleStartInProgress = false;
  if (state.activeView === "ai-console") ensureCopilotSession();
  renderAll();
}

async function loadTests() {
  const payload = await apiGet("/api/regression/tests", mockTests);
  state.tests = normalizeArray(payload.tests || payload);
}

async function loadMermaid() {
  const payload = await apiGet("/api/regression/mermaid", mockMermaid);
  state.mermaid = payload.mermaid || payload.source || String(payload);
}

async function loadReports() {
  const payload = await apiGet("/api/reports", mockReports);
  state.reports = normalizeArray(payload.reports || payload);
}

async function startSession(buttonId = "start-session-button", options = {}) {
  if (state.aiConsoleStartInProgress) return null;
  state.aiConsoleStartInProgress = true;
  renderAiConsole();
  logEvent("button_clicked", { button_id: buttonId, user_action: "start_session" });
  try {
    const payload = await apiPost("/api/session/start", { hidden_window: !state.copilotWindowVisible, restart_existing: false });
    if (payload?.job || payload?.job_id) addOrUpdateJob(payload.job || payload);
    if (!options.skipRefresh) await refreshStatusAndJobs();
    return payload;
  } finally {
    state.aiConsoleStartInProgress = false;
    renderAiConsole();
  }
}

async function ensureCopilotSession() {
  const aiConsoleState = state.aiConsole || {};
  if (isCopilotOnline(aiConsoleState) || state.aiConsoleStartInProgress) return;
  if (aiConsoleState.source === "injected") return;
  const status = aiConsoleState.status || "unknown";
  if (!["missing", "not_running", "failed", "unavailable", "unknown", "mocked"].includes(status)) return;
  const now = Date.now();
  if (now - state.lastAutoStartAttempt < 15000) return;
  state.lastAutoStartAttempt = now;
  await startSession("copilot-auto-start");
}

async function createApiJob(path, body, fallbackFactory) {
  const payload = await apiPost(path, body, fallbackFactory);
  const job = payload?.job || payload;
  if (job?.job_id || job?.id) logEvent("job_created", { job_id: job.job_id || job.id, details: job });
  return job;
}

async function sendAiConsoleInput(options = {}) {
  if (state.aiConsoleSending) return;
  const input = $("#ai-console-input");
  const hasExplicitText = Object.prototype.hasOwnProperty.call(options, "text");
  const text = hasExplicitText ? options.text : input.value;
  if (!String(text).trim() && !["\x1b", "\t"].includes(text)) return;
  const submit = options.submit !== false;
  const clearLine = options.clearLine !== false;
  const sourceButtonId = options.sourceButtonId || "ai-console-send";
  state.aiConsoleSending = true;
  renderAiConsole();
  logEvent("button_clicked", { button_id: sourceButtonId, user_action: "send_ai_console_input" });
  try {
    const clientSentAt = new Date().toISOString();
    state.lastAiConsoleInput = { text, submit, clear_line: clearLine, client_sent_at: clientSentAt };
    const payload = await apiPost("/api/ai-console/input", { text, submit, clear_line: clearLine, client_sent_at: clientSentAt });
    if (!payload?.accepted) {
      $("#ai-console-hint").textContent = payload?.error || "Input kunde inte skickas.";
      return;
    }
    state.lastAiConsoleInput = { ...state.lastAiConsoleInput, job_id: payload.job_id || null, accepted_at: payload.accepted_at || null, response: payload.response || null };
    if (payload.console) state.aiConsole = payload.console;
    if (payload.console) mergeAiConsoleState(payload.console);
    if (!hasExplicitText) input.value = "";
    logEvent("ai_console_input_sent", { status: "queued", job_id: payload.job_id, details: payload });
    $("#ai-console-hint").textContent = "Skickat till Copilot.";
  } finally {
    state.aiConsoleSending = false;
    renderAiConsole();
  }
}

function connectAiConsoleEvents() {
  if (!("EventSource" in window) || state.aiConsoleEvents) return;
  const cursorParam = state.aiConsoleCursor === null ? "" : `cursor=${encodeURIComponent(state.aiConsoleCursor)}&`;
  const url = `${API_BASE}/api/ai-console/events?${cursorParam}limit=${CONSOLE_EVENT_LIMIT}`;
  const events = new EventSource(url);
  state.aiConsoleEvents = events;
  events.addEventListener("open", () => {
    state.aiConsoleEventsConnected = true;
  });
  events.addEventListener("console", (event) => {
    try {
      const payload = JSON.parse(event.data);
      state.lastAiConsoleEventAt = new Date().toISOString();
      mergeAiConsoleState(payload);
      if (isCopilotOnline(state.aiConsole || {})) state.aiConsoleStartInProgress = false;
      renderAiConsole();
    } catch (error) {
      logEvent("api_request_failed", { method: "SSE", path: "/api/ai-console/events", error: error.message });
    }
  });
  events.addEventListener("error", () => {
    state.aiConsoleEventsConnected = false;
    events.close();
    state.aiConsoleEvents = null;
    setTimeout(connectAiConsoleEvents, 1000);
  });
}

function mergeAiConsoleState(aiConsoleState) {
  state.aiConsole = aiConsoleState || mockAiConsole();
  const transcript = state.aiConsole.transcript || null;
  if (transcript && typeof transcript.next_cursor === "number") {
    if (["tail", "reset_tail", "fallback_tail", "missing"].includes(transcript.mode)) {
      state.aiConsoleTranscript = transcript.text || "";
    } else if (transcript.mode === "delta" && transcript.text) {
      state.aiConsoleTranscript = `${state.aiConsoleTranscript}${transcript.text}`;
    }
    state.aiConsoleCursor = transcript.next_cursor;
  } else {
    state.aiConsoleTranscript = state.aiConsole.transcript_tail || state.aiConsole.last_output_tail || state.aiConsoleTranscript;
  }
  if (state.aiConsoleTranscript.length > MAX_CONSOLE_BUFFER) {
    state.aiConsoleTranscript = state.aiConsoleTranscript.slice(-MAX_CONSOLE_BUFFER);
  }
}

async function apiGet(path, fallbackFactory) {
  return apiRequest(path, { method: "GET" }, fallbackFactory);
}

async function apiPost(path, body, fallbackFactory = () => ({})) {
  return apiRequest(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }, fallbackFactory);
}

async function apiRequest(path, options, fallbackFactory) {
  const method = options.method || "GET";
  logEvent("api_request_started", { method, path });
  try {
    const response = await fetch(`${API_BASE}${path}`, options);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    const json = await response.json();
    logEvent("api_request_completed", { method, path, status: response.status });
    return json;
  } catch (error) {
    logEvent("api_request_failed", { method, path, error: error.message });
    return typeof fallbackFactory === "function" ? fallbackFactory() : fallbackFactory;
  }
}

function renderAll() {
  renderStatus();
  renderDashboard();
  renderAiConsole();
  renderTests();
  renderMermaidGraph();
  renderReports();
  renderJobs();
  renderLogs();
}

function renderStatus() {
  const hostState = state.status?.host_runner?.status || state.status?.host_runner_status || "unknown";
  const diode = state.jobs.length ? deriveDiode(state.jobs) : (state.status?.status_diode || "red");
  $("#mode-label").textContent = `Mode: ${state.mode}`;
  $("#host-runner-status").textContent = `Host runner: ${hostState}`;
  const diodeElement = $("#status-diode");
  diodeElement.className = `status-diode status-${diode}`;
  diodeElement.querySelector("strong").textContent = diodeLabel(diode);
  diodeElement.title = diodeTitle(diode);
  if (state.lastDiode !== diode) {
    state.lastDiode = diode;
    logEvent("status_diode_changed", { status: diode });
  }
}

function renderDashboard() {
  const copilot = state.status?.copilot_session || state.status?.copilot || {};
  const browser = state.status?.browser_session || state.status?.browser || {};
  const latestJob = state.jobs[0];
  const latestReport = state.reports[0];
  $("#card-copilot").textContent = copilot.status || copilot.state || "unknown";
  $("#card-copilot-tail").textContent = copilot.user_input_required ? "Väntar på manuell återkoppling" : (copilot.transcript_tail || copilot.latest_output || "Ingen output ännu");
  $("#card-browser").textContent = browser.status || "unknown";
  $("#card-browser-tail").textContent = browser.debug_port ? `Debug-port ${browser.debug_port}` : "Ingen debug-port";
  $("#card-job").textContent = latestJob ? `${latestJob.type || "job"} · ${latestJob.status}` : "Inget jobb";
  $("#card-job-tail").textContent = latestJob?.output_tail || latestJob?.command || "Skapa ett jobb från Regressioner eller Mode.";
  $("#card-report").textContent = latestReport?.title || latestReport?.name || "Ingen rapport";
  $("#card-report-tail").textContent = latestReport?.status || latestReport?.date || "Rapporter läses från backend.";
  const failed = state.jobs.find((job) => job.status === "failed");
  $("#card-error").textContent = failed ? failed.title || failed.job_id || failed.id : "Inget verifierat fel";
  $("#card-error-tail").textContent = failed?.output_tail || "Fel visas här när backend rapporterar dem.";
}

function renderAiConsole() {
  const aiConsoleState = state.aiConsole || mockAiConsole();
  const status = aiConsoleState.status || "unknown";
  const queue = aiConsoleState.input_queue || {};
  const heartbeat = aiConsoleState.heartbeat || {};
  const isOnline = isCopilotOnline(aiConsoleState);
  const rawOutput = isOnline
    ? (state.aiConsoleTranscript || aiConsoleState.transcript_tail || aiConsoleState.last_output_tail || "Connected - waiting for Copilot output.")
    : state.aiConsoleStartInProgress
    ? "Starting Copilot session - please wait..."
    : "Disconnected - please wait until Copilot is online";
  const output = formatCopilotTranscriptForDisplay(rawOutput);
  const outputHtml = copilotTranscriptToHtml(output);
  const windowExpected = Boolean(aiConsoleState.visible_window_expected);
  const windowMatches = isOnline && windowExpected === state.copilotWindowVisible;
  const modelVerified = isOnline && Boolean(aiConsoleState.model_verified && aiConsoleState.model_hint);
  const permissionsVerified = isOnline && Boolean(aiConsoleState.permissions_verified && aiConsoleState.permissions_hint);
  const projectVerified = isOnline && Boolean(aiConsoleState.project_verified && aiConsoleState.project_name);
  const commandReady = isOnline && Boolean(aiConsoleState.command_ready);
  setSemanticBadge($("#ai-console-status"), `Status: ${status}${queue.pending ? ` · kö ${queue.pending}` : ""}`, statusBadgeTone(status, isOnline));
  setSemanticBadge($("#copilot-window-mode"), `Motor: ${state.copilotWindowVisible ? "synlig" : "osynlig"}`, windowMatches ? "green" : (isOnline ? "yellow" : "gray"));
  setSemanticBadge($("#ai-console-model"), modelVerified ? `Modell: ${aiConsoleState.model_hint}` : "Modell: ej verifierad", modelVerified ? "green" : (isOnline ? "yellow" : "gray"));
  setSemanticBadge($("#ai-console-permissions"), permissionsVerified ? `Permissions: ${aiConsoleState.permissions_hint}` : "Permissions: ej verifierad", permissionsVerified ? "green" : (isOnline ? "yellow" : "gray"));
  setSemanticBadge($("#ai-console-project"), projectVerified ? `Projekt: ${aiConsoleState.project_name}` : "Projekt: okänt", projectVerified ? "green" : (isOnline ? "yellow" : "gray"));
  setSemanticBadge($("#ai-console-ready"), commandReady ? "Prompt: redo" : "Prompt: väntar", commandReady ? "green" : (isOnline ? "yellow" : "gray"));
  $("#ai-console-send").textContent = state.aiConsoleSending ? "Skickar..." : "Skicka";
  $("#ai-console-send").disabled = state.aiConsoleSending;
  $("#ai-console-send-esc").disabled = state.aiConsoleSending;
  $("#ai-console-send-tab").disabled = state.aiConsoleSending;
  $("#copilot-start-session-button").textContent = state.aiConsoleStartInProgress ? "Startar..." : "Starta Copilot CLI-session";
  $("#copilot-start-session-button").disabled = state.aiConsoleStartInProgress;
  const outputElement = $("#ai-console-output");
  const shouldStickToBottom = outputElement.scrollTop + outputElement.clientHeight >= outputElement.scrollHeight - 12;
  if (outputElement.dataset.renderedTranscript !== outputHtml) {
    outputElement.innerHTML = outputHtml;
    outputElement.dataset.renderedTranscript = outputHtml;
    const renderedAt = new Date().toISOString();
    const renderSnapshot = {
      rendered_at: renderedAt,
      status,
      transcript_cursor: heartbeat.next_cursor ?? state.aiConsoleCursor,
      transcript_length: output.length,
      streamed_at: aiConsoleState.streamed_at || null,
      server_timestamp: aiConsoleState.server_timestamp || null,
      last_output_chunk_at: aiConsoleState.last_output_chunk_at || null,
      last_output_sequence: aiConsoleState.last_output_sequence ?? null,
      project_name: aiConsoleState.project_name || null,
      permissions_verified: permissionsVerified,
      command_ready: commandReady,
      last_event_received_at: state.lastAiConsoleEventAt,
      last_input: state.lastAiConsoleInput,
    };
    state.lastAiConsoleRender = renderSnapshot;
    window.__copilotAdminLastAiConsoleRender = renderSnapshot;
    logEvent("ai_console_rendered", { status, transcript_cursor: renderSnapshot.transcript_cursor, transcript_length: output.length, rendered_at: renderedAt, streamed_at: renderSnapshot.streamed_at, last_output_chunk_at: renderSnapshot.last_output_chunk_at, command_ready: commandReady });
    if (shouldStickToBottom) outputElement.scrollTop = outputElement.scrollHeight;
  }
  $("#ai-console-hint").textContent = aiConsoleState.user_input_required
    ? "Copilot väntar på input."
    : (state.aiConsoleStartInProgress ? "Startar eller återansluter Copilot-session..." : (state.aiConsoleSending ? "Skickar till Copilot..." : "Redo."));
  const signature = `${status}|${Boolean(aiConsoleState.user_input_required)}|${output.length}|${queue.pending || 0}|${heartbeat.next_cursor ?? ""}`;
  if (state.lastAiConsoleSignature !== signature) {
    state.lastAiConsoleSignature = signature;
    logEvent("ai_console_refreshed", { status, user_input_required: Boolean(aiConsoleState.user_input_required), transcript_length: output.length, transcript_cursor: heartbeat.next_cursor ?? state.aiConsoleCursor });
  }
}

function isCopilotOnline(aiConsoleState) {
  const status = aiConsoleState.status || "unknown";
  return Boolean(aiConsoleState.running) || ["running", "user_input_required"].includes(status);
}

function statusBadgeTone(status, isOnline) {
  if (isOnline) return "green";
  if (["starting", "queued", "unknown", "mocked"].includes(status)) return "yellow";
  if (["missing", "not_running", "failed", "unavailable"].includes(status)) return "red";
  return "gray";
}

function setSemanticBadge(element, text, tone) {
  element.textContent = text;
  element.className = `pill semantic-badge semantic-${tone}`;
}

function renderTests() {
  const select = $("#regression-select");
  select.innerHTML = state.tests.map((test) => {
    const id = test.test_id || test.id || test.catalog_key;
    return `<option value="${escapeAttr(id)}">${escapeHtml(test.catalog_key || id)} · ${escapeHtml(id)} · ${escapeHtml(test.title || test.summary || "")}</option>`;
  }).join("");
  $("#regression-list").innerHTML = state.tests.map((test) => {
    const id = test.test_id || test.id || test.catalog_key;
    return `
    <article class="item" data-testid="regression-item" data-test-id="${escapeAttr(id)}">
      <h3>${escapeHtml(test.catalog_key || "")} · ${escapeHtml(id || "Regressionstest")}</h3>
      <p>${escapeHtml(test.summary || "Ingen sammanfattning.")}</p>
      <div class="item-meta">Beroenden: ${escapeHtml((test.dependencies || []).join(", ") || "inga")}</div>
      <div class="item-actions">
        <button data-testid="run-regression-item-button" data-run-test-id="${escapeAttr(id)}">Kör detta test</button>
      </div>
    </article>
  `;
  }).join("");
  $$("[data-run-test-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const testId = button.dataset.runTestId;
      $("#regression-select").value = testId;
      logEvent("button_clicked", { button_id: "run-regression-item-button", user_action: "run_selected_regression", test_id: testId });
      const job = await createApiJob("/api/regression/run", { scope: "selected", test_id: testId }, () => mockJob("regression", testId));
      if (job) addOrUpdateJob(job);
      renderAll();
    });
  });
}

function renderMermaidGraph() {
  $("#mermaid-source").textContent = state.mermaid;
  const graph = parseMermaid(state.mermaid);
  const filter = $("#mermaid-search").value.trim().toLowerCase();
  const nodeW = 220;
  const nodeH = 66;
  const gapX = 80;
  const gapY = 54;
  const positions = layoutMermaidGraph(graph, nodeW, nodeH, gapX, gapY);
  const maxX = Math.max(0, ...[...positions.values()].map((position) => position.x));
  const maxY = Math.max(0, ...[...positions.values()].map((position) => position.y));
  const width = Math.max(900, maxX + nodeW + 120);
  const height = Math.max(620, maxY + nodeH + 120);
  const edges = graph.edges.map(([from, to]) => {
    const a = positions.get(from);
    const b = positions.get(to);
    if (!a || !b) return "";
    const points = edgePoints(a, b, nodeW, nodeH);
    return `<line class="graph-edge" x1="${points.x1}" y1="${points.y1}" x2="${points.x2}" y2="${points.y2}" />`;
  }).join("");
  const nodes = graph.nodes.map(({ id, label }) => {
    const p = positions.get(id);
    const dimmed = filter && !`${id} ${label}`.toLowerCase().includes(filter);
    const lines = wrapText(label, 28);
    const firstY = nodeH / 2 - ((lines.length - 1) * 8);
    return `<g class="graph-node ${dimmed ? "dimmed" : ""}" data-testid="mermaid-node" transform="translate(${p.x} ${p.y})">
      <rect rx="16" width="${nodeW}" height="${nodeH}"></rect>
      <text x="${nodeW / 2}" y="${firstY}">${lines.map((line, index) => `<tspan x="${nodeW / 2}" dy="${index ? 18 : 0}">${escapeHtml(line)}${index < lines.length - 1 ? " " : ""}</tspan>`).join("")}</text>
    </g>`;
  }).join("");
  $("#mermaid-canvas").style.width = `${width}px`;
  $("#mermaid-canvas").style.height = `${height}px`;
  $("#mermaid-canvas").style.transform = `translate(${state.mermaidTransform.x}px, ${state.mermaidTransform.y}px) scale(${state.mermaidTransform.scale})`;
  $("#mermaid-canvas").innerHTML = `<svg width="${width}" height="${height}" role="img" aria-label="Regression dependency graph">
    <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="rgba(255,255,255,0.45)"/></marker></defs>
    ${edges}${nodes}
  </svg>`;
}

function renderReports() {
  const filter = $("#report-filter").value.trim().toLowerCase();
  const reports = state.reports.filter((report) => `${report.title || ""} ${report.name || ""} ${report.path || ""} ${report.status || ""}`.toLowerCase().includes(filter));
  $("#report-list").innerHTML = reports.map((report) => `
    <article class="item" data-testid="report-item">
      <h3>${escapeHtml(report.title || report.name || report.report_id || report.id)}</h3>
      <div class="item-meta">${escapeHtml(report.run_id || report.date || "")} ${escapeHtml(report.status || report.type || "")}</div>
      <div class="item-actions"><button data-testid="open-report-button" data-report-id="${escapeAttr(report.report_id || report.id)}">Öppna rapport</button></div>
    </article>
  `).join("");
  $$("[data-report-id]").forEach((button) => {
    button.addEventListener("click", () => openReport(button.dataset.reportId));
  });
}

async function openReport(reportId) {
  logEvent("button_clicked", { button_id: "open-report-button", user_action: "open_report", report_id: reportId });
  const report = await apiGet(`/api/reports/${encodeURIComponent(reportId)}`, () => mockReport(reportId));
  logEvent("report_opened", { report_id: reportId });
  $("#report-reader").innerHTML = markdownToHtml(report.markdown || report.content || "Rapporten saknar innehåll.");
}

function renderJobs() {
  $("#job-list").innerHTML = state.jobs.map((job) => `
    <article class="item" data-testid="job-item">
      <h3>${escapeHtml(job.title || job.command || job.job_id || job.id)}</h3>
      <span class="status-badge ${escapeAttr(job.status)}">${escapeHtml(job.status || "unknown")}</span>
      <p>${escapeHtml(job.output_tail || job.transcript_tail || "Ingen output ännu.")}</p>
      <div class="item-meta">Skapad: ${escapeHtml(job.created_at || "okänt")} · Uppdaterad: ${escapeHtml(job.updated_at || "okänt")}</div>
      <div class="item-actions">
        <button data-testid="open-job-result-button" data-job-id="${escapeAttr(job.job_id || job.id)}">Öppna resultat</button>
      </div>
    </article>
  `).join("");
  $$("[data-job-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const jobId = button.dataset.jobId;
      logEvent("button_clicked", { button_id: "open-job-result-button", user_action: "open_job", job_id: jobId });
      await apiPost(`/api/jobs/${encodeURIComponent(jobId)}/open`, {});
      logEvent("job_opened", { job_id: jobId });
      state.jobs = state.jobs.map((job) => (job.job_id === jobId || job.id === jobId) && job.status === "completed_unopened" ? { ...job, status: "completed_opened" } : job);
      renderAll();
    });
  });
}

function renderLogs() {
  $("#frontend-log").textContent = state.logs.slice(-80).map((entry) => JSON.stringify(entry)).join("\n");
}

function setMermaidZoom(scale) {
  setMermaidTransform(Math.max(0.25, Math.min(2.5, scale)), state.mermaidTransform.x, state.mermaidTransform.y, "mermaid_zoom_changed");
}

function setMermaidTransform(scale, x, y, eventName = "mermaid_zoom_changed") {
  state.mermaidTransform = { scale, x, y };
  logEvent(eventName, { scale, x, y });
  renderMermaidGraph();
}

function addOrUpdateJob(job) {
  const normalized = normalizeJob(job);
  const id = normalized.job_id || normalized.id;
  state.jobs = [normalized, ...state.jobs.filter((existing) => (existing.job_id || existing.id) !== id)];
}

function deriveDiode(jobs) {
  if (jobs.some((job) => ["queued", "running", "user_input_required"].includes(job.status))) return "yellow";
  if (jobs.some((job) => job.status === "completed_unopened")) return "green";
  return "red";
}

function diodeLabel(color) {
  return { red: "Röd", yellow: "Gul", green: "Grön" }[color] || color;
}

function diodeTitle(color) {
  return {
    red: "Inget jobb körs och inget oöppnat resultat finns",
    yellow: "Minst ett jobb är aktivt eller väntar på användarinput",
    green: "Minst ett klart jobb väntar på att öppnas",
  }[color] || "Okänd status";
}

function logEvent(event, details = {}) {
  if (!REQUIRED_EVENTS.has(event) && !event.startsWith("api_")) return;
  const entry = {
    timestamp: new Date().toISOString(),
    level: details.error ? "warn" : "info",
    component: "frontend",
    event,
    trace_id: state.traceId,
    session_id: state.sessionId,
    job_id: details.job_id,
    user_action: details.user_action,
    status: details.status,
    details,
  };
  state.logs.push(entry);
  renderLogs();
  fetch(`${API_BASE}/api/frontend/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entry),
    keepalive: true,
  }).catch(() => undefined);
}

function parseMermaid(source) {
  const nodes = new Map();
  const edges = [];
  const upsertNode = (token) => {
    const parsed = parseMermaidNodeToken(token);
    if (!parsed) return null;
    const existing = nodes.get(parsed.id);
    const parsedHasExplicitLabel = parsed.label && parsed.label !== parsed.id;
    nodes.set(parsed.id, { id: parsed.id, label: parsedHasExplicitLabel ? parsed.label : existing?.label || parsed.label || parsed.id });
    return parsed.id;
  };
  source.split(/\r?\n/).forEach((line) => {
    const clean = line.trim().replace(/;$/, "");
    if (!clean || /^(graph|flowchart)\b/i.test(clean)) return;
    const match = clean.match(/^(.+?)\s*[-.=]+(?:\|[^|]*\|)?[ox]?>\s*(.+)$/);
    if (match) {
      const from = upsertNode(match[1]);
      const to = upsertNode(match[2]);
      if (from && to) edges.push([from, to]);
    } else {
      upsertNode(clean);
    }
  });
  return { nodes: [...nodes.values()], edges };
}

function parseMermaidNodeToken(token) {
  const trimmed = token.trim();
  const match = trimmed.match(/^([\w.-]+)\s*(?:\[\s*"?([^"\]]+)"?\s*\]|\(\s*"?([^")]+)"?\s*\))?/);
  if (!match) return null;
  return { id: match[1], label: (match[2] || match[3] || match[1]).trim() };
}

function layoutMermaidGraph(graph, nodeW, nodeH, gapX, gapY) {
  const ids = graph.nodes.map((node) => node.id);
  const parents = new Map(ids.map((id) => [id, []]));
  const children = new Map(ids.map((id) => [id, []]));
  for (const [from, to] of graph.edges) {
    if (!parents.has(to)) parents.set(to, []);
    if (!children.has(from)) children.set(from, []);
    parents.get(to).push(from);
    children.get(from).push(to);
  }
  const levelCache = new Map();
  const levelOf = (id, visiting = new Set()) => {
    if (levelCache.has(id)) return levelCache.get(id);
    if (visiting.has(id)) return 0;
    visiting.add(id);
    const parentLevels = (parents.get(id) || []).map((parent) => levelOf(parent, visiting));
    visiting.delete(id);
    const level = parentLevels.length ? Math.max(...parentLevels) + 1 : 0;
    levelCache.set(id, level);
    return level;
  };
  const groups = new Map();
  ids.forEach((id) => {
    const level = levelOf(id);
    if (!groups.has(level)) groups.set(level, []);
    groups.get(level).push(id);
  });
  const positions = new Map();
  [...groups.keys()].sort((a, b) => a - b).forEach((level) => {
    groups.get(level).forEach((id, row) => {
      positions.set(id, {
        x: 60 + level * (nodeW + gapX),
        y: 60 + row * (nodeH + gapY),
      });
    });
  });
  return positions;
}

function edgePoints(a, b, nodeW, nodeH) {
  if (b.x > a.x) {
    return { x1: a.x + nodeW, y1: a.y + nodeH / 2, x2: b.x, y2: b.y + nodeH / 2 };
  }
  if (b.x < a.x) {
    return { x1: a.x, y1: a.y + nodeH / 2, x2: b.x + nodeW, y2: b.y + nodeH / 2 };
  }
  if (b.y >= a.y) {
    return { x1: a.x + nodeW / 2, y1: a.y + nodeH, x2: b.x + nodeW / 2, y2: b.y };
  }
  return { x1: a.x + nodeW / 2, y1: a.y, x2: b.x + nodeW / 2, y2: b.y + nodeH };
}

function wrapText(text, maxChars) {
  const words = String(text || "").split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    if ((current ? `${current} ${word}` : word).length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = current ? `${current} ${word}` : word;
    }
  }
  if (current) lines.push(current);
  return lines.slice(0, 3);
}

function formatCopilotTranscriptForDisplay(text) {
  return applyTerminalRedrawControls(removeCopilotTimerRedrawArtifacts(String(text || "")))
    .replace(/\x1B(?:\][^\x07]*(?:\x07|\x1B\\)|\[[0-?]*[ -/]*[@-~]|[@-Z\\-_])/g, "")
    .replace(/[^\S\r\n]+$/gm, "")
    .replace(/\n{4,}/g, "\n\n\n")
    .trimEnd();
}

function removeCopilotTimerRedrawArtifacts(text) {
  return text.replace(
    /([╰└][─━═┄┈┉\s]+[╯┘])(?:[0-9ms/ \b]+)(?=\s{2,}[\p{L}$●⌄∨/])/gu,
    "$1\n",
  );
}

function applyTerminalRedrawControls(text) {
  const lines = [[]];
  let row = 0;
  let column = 0;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === "\r") {
      if (text[index + 1] === "\n") {
        index += 1;
        row += 1;
        lines[row] = lines[row] || [];
        column = 0;
      } else {
        column = 0;
      }
      continue;
    }
    if (char === "\n") {
      row += 1;
      lines[row] = lines[row] || [];
      column = 0;
      continue;
    }
    if (char === "\b") {
      column = Math.max(0, column - 1);
      if (lines[row]) lines[row].splice(column, 1);
      continue;
    }
    if (char < " " && char !== "\t") continue;
    lines[row] = lines[row] || [];
    lines[row][column] = char;
    column += 1;
  }
  return lines.map((line) => line.join("")).join("\n");
}

function copilotTranscriptToHtml(text) {
  const lines = String(text || "").split("\n");
  const html = [];
  let blankCount = 0;
  let inThought = false;
  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index];
    const line = normalizeCopilotTranscriptLine(rawLine);
    const trimmed = line.trim();
    if (isCopilotTimerArtifact(trimmed)) continue;
    if (!trimmed || isCopilotBorderLine(trimmed)) {
      blankCount += 1;
      if (blankCount <= 1) html.push('<div class="copilot-line spacer"></div>');
      continue;
    }
    blankCount = 0;
    const special = classifyCopilotLine(trimmed);
    if (special) inThought = false;
    if (/^[⌄∨]\s*Thought for/i.test(trimmed)) {
      inThought = true;
      html.push(`<div class="copilot-line thought-heading">${escapeHtml(trimmed.replace(/^∨/, "⌄"))}</div>`);
    } else if (special === "message") {
      html.push(`<div class="copilot-line message">${escapeHtml(trimmed)}</div>`);
    } else if (special === "shell") {
      html.push(`<div class="copilot-line shell-call">${escapeHtml(trimmed)}</div>`);
    } else if (special === "command-title") {
      html.push(`<div class="copilot-line command-title">${escapeHtml(trimmed)}</div>`);
    } else if (special === "command-code") {
      const commandLines = [trimmed];
      while (index + 1 < lines.length) {
        const nextLine = normalizeCopilotTranscriptLine(lines[index + 1]).trim();
        if (!isContinuationCommandLine(nextLine)) break;
        commandLines.push(nextLine);
        index += 1;
      }
      html.push(commandCodeToHtml(commandLines.join(" ")));
    } else if (special === "question") {
      html.push(`<div class="copilot-line question">${escapeHtml(trimmed)}</div>`);
    } else if (special === "selected-option") {
      html.push(`<div class="copilot-line selected-option">${escapeHtml(trimmed.replace(/^[>›]\s*/, "❯ "))}</div>`);
    } else if (special === "option") {
      html.push(`<div class="copilot-line option">${escapeHtml(trimmed)}</div>`);
    } else if (special === "navigation-hint") {
      html.push(`<div class="copilot-line navigation-hint">${escapeHtml(trimmed)}</div>`);
    } else if (trimmed.startsWith("Disconnected -")) {
      html.push(`<div class="copilot-line disconnected">${escapeHtml(trimmed)}</div>`);
    } else if (inThought) {
      html.push(`<div class="copilot-line thought-body">${escapeHtml(trimmed)}</div>`);
    } else {
      html.push(`<div class="copilot-line plain">${escapeHtml(trimmed)}</div>`);
    }
  }
  return html.join("");
}

function normalizeCopilotTranscriptLine(line) {
  return String(line || "")
    .replace(/[│┃║╎┆]/g, "")
    .replace(/[╭╮╰╯┌┐└┘]/g, "")
    .replace(/^[\s─━═┄┈┉-]+$/, "")
    .replace(/[ \t]{2,}/g, " ")
    .trimEnd();
}

function isCopilotBorderLine(line) {
  return /^[─━═┄┈┉\s-]+$/.test(line);
}

function isCopilotTimerArtifact(line) {
  if (!line) return false;
  const compact = line.replace(/[◉◎○●∙·•⌛⠁-⣿\s]+/g, "");
  const timerMatches = compact.match(/\d+(?:m|s)/g) || [];
  const digitRuns = compact.match(/\d{4,}/g) || [];
  if (!compact && /[◉◎○●∙·•⌛⠁-⣿]/.test(line)) return true;
  if (/Session:\s*\d+(?:\.\d+)?\s+AIC used/i.test(line)) return true;
  return timerMatches.length >= 2 || digitRuns.length >= 2 || (/^[0-9ms/.:/]+$/.test(compact) && compact.length > 6);
}

function classifyCopilotLine(line) {
  if (/^●\s+/.test(line)) return "message";
  if (/^\$\s+Shell\b/.test(line)) return "shell";
  if (/^Run safe host-runner smoke tests\b/.test(line)) return "command-title";
  if (/^\$ErrorActionPreference=/.test(line) || /^\$targets\s*=/.test(line) || /^host-runner-/.test(line)) return "command-code";
  if (/^Do you want to run this command\?/.test(line)) return "question";
  if (/^(❯|›|>)\s*\d+\.\s+/.test(line)) return "selected-option";
  if (/^\d+\.\s+/.test(line)) return "option";
  if (/^↑\/↓\s+to (navigate|select)/.test(line) || /enter to (select|confirm)/.test(line)) return "navigation-hint";
  return null;
}

function isContinuationCommandLine(line) {
  return Boolean(line)
    && !classifyCopilotLine(line)
    && !isCopilotBorderLine(line)
    && !isCopilotTimerArtifact(line)
    && !/^(Copilot is attempting|Do you want|Question|User selected|Check if|C:\\|↑\/↓|[❯›>]\s*\d+\.|\d+\.)/.test(line);
}

function commandCodeToHtml(command) {
  const isTruncated = /…\s*$/.test(command);
  const label = isTruncated ? '<span class="command-truncated-label">Sammanfattning - fullständigt kommando visas av Copilot i approval-kortet när det finns tillgängligt.</span>' : "";
  return `<div class="copilot-line command-code ${isTruncated ? "truncated" : ""}">${escapeHtml(command)}${label}</div>`;
}

function markdownToHtml(markdown) {
  const lines = markdown.split(/\r?\n/);
  let inList = false;
  let inCode = false;
  let inTable = false;
  const html = [];
  const closeList = () => {
    if (inList) html.push("</ul>");
    inList = false;
  };
  const closeTable = () => {
    if (inTable) html.push("</tbody></table>");
    inTable = false;
  };
  for (let index = 0; index < lines.length; index += 1) {
    const raw = lines[index];
    const line = escapeHtml(raw);
    if (raw.startsWith("```")) {
      closeList();
      closeTable();
      html.push(inCode ? "</code></pre>" : "<pre><code>");
      inCode = !inCode;
      continue;
    }
    if (inCode) {
      html.push(`${line}\n`);
      continue;
    }
    const next = lines[index + 1] || "";
    if (isMarkdownTableHeader(raw, next)) {
      closeList();
      closeTable();
      html.push("<table><thead><tr>");
      html.push(markdownTableCells(raw, "th").join(""));
      html.push("</tr></thead><tbody>");
      inTable = true;
      index += 1;
      continue;
    }
    if (inTable && isMarkdownTableRow(raw)) {
      html.push(`<tr>${markdownTableCells(raw, "td").join("")}</tr>`);
      continue;
    }
    closeTable();
    if (/^#\s+/.test(raw)) {
      closeList();
      html.push(`<h1>${formatInlineMarkdown(raw.replace(/^#\s+/, ""))}</h1>`);
    } else if (/^##\s+/.test(raw)) {
      closeList();
      html.push(`<h2>${formatInlineMarkdown(raw.replace(/^##\s+/, ""))}</h2>`);
    } else if (/^###\s+/.test(raw)) {
      closeList();
      html.push(`<h3>${formatInlineMarkdown(raw.replace(/^###\s+/, ""))}</h3>`);
    }
    else if (/^\s*-\s+/.test(raw)) {
      if (!inList) html.push("<ul>");
      inList = true;
      html.push(`<li>${formatInlineMarkdown(raw.replace(/^\s*-\s+/, ""))}</li>`);
    } else {
      closeList();
      if (raw.trim()) html.push(`<p>${formatInlineMarkdown(raw)}</p>`);
    }
  }
  closeList();
  closeTable();
  return html.join("\n");
}

function isMarkdownTableHeader(line, nextLine) {
  return isMarkdownTableRow(line) && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(nextLine);
}

function isMarkdownTableRow(line) {
  return /^\s*\|.*\|\s*$/.test(line);
}

function markdownTableCells(line, tag) {
  return splitMarkdownTableRow(line).map((cell) => `<${tag}>${formatInlineMarkdown(cell)}</${tag}>`);
}

function splitMarkdownTableRow(line) {
  let text = line.trim();
  if (text.startsWith("|")) text = text.slice(1);
  if (text.endsWith("|")) text = text.slice(0, -1);
  const cells = [];
  let current = "";
  let escaped = false;
  let inCode = false;
  for (const char of text) {
    if (escaped) {
      current += char;
      escaped = false;
    } else if (char === "\\") {
      escaped = true;
    } else if (char === "`") {
      inCode = !inCode;
      current += char;
    } else if (char === "|" && !inCode) {
      cells.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  cells.push(current.trim());
  return cells;
}

function formatInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, href) => {
      const safeHref = String(href).trim();
      if (/^(https?:|\/|\.\/|[A-Za-z0-9_.-])/.test(safeHref) && !/^javascript:/i.test(safeHref)) {
        return `<a href="${escapeAttr(safeHref)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
      }
      return label;
    });
}

function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeJob(job) {
  const id = job.job_id || job.id || `job-${Date.now()}`;
  return {
    ...job,
    job_id: id,
    id,
    status: job.status || "queued",
    created_at: job.created_at || new Date().toISOString(),
    updated_at: job.updated_at || new Date().toISOString(),
  };
}

function mockStatus() {
  return {
    mode: state.mode,
    status_diode: deriveDiode(state.jobs),
    host_runner: { status: "mocked" },
    copilot: { status: "unknown", transcript_tail: "Backend saknas; frontend kör mockad kontraktsvy." },
    browser: { status: "unknown" },
  };
}

function mockTests() {
  return {
    tests: [
      { id: "A", title: "Kontraktssökning och serviceportal-login", summary: "Verifierar grundflöde och login.", dependencies: [] },
      { id: "B", title: "Nytt kontrakt på migrerat DS", summary: "Verifierar köpflöde efter migreringsval.", dependencies: ["A"] },
      { id: "C", title: "Checkout och skapa kontrakt", summary: "Verifierar checkoutdata och avtalsskapande.", dependencies: ["B"] },
      { id: "D", title: "Nytt kontrakt på ej migrerat DS", summary: "Verifierar köpbar produkt för non-migrated DS.", dependencies: ["A"] },
    ],
  };
}

function mockMermaid() {
  return { mermaid: "graph TD\nA[Kontraktssökning] --> B[Migrerat DS]\nB --> C[Checkout]\nA --> D[Ej migrerat DS]" };
}

function mockReports() {
  return { reports: [{ id: "latest", title: "Mockad senaste rapport", date: new Date().toISOString().slice(0, 10), status: "demo" }] };
}

function mockAiConsole() {
  return {
    status: "mocked",
    running: false,
    transcript_tail: "AI-konsolen kör i mockläge tills backend/host-runner svarar.",
    transcript: { mode: "fallback_tail", text: "AI-konsolen kör i mockläge tills backend/host-runner svarar.", cursor: null, next_cursor: 66, size: 66, truncated: false },
    heartbeat: { next_cursor: 66, transcript_size: 66, server_timestamp: new Date().toISOString() },
    input_queue: { pending: 0 },
    model_hint: null,
    model_verified: false,
    permissions_hint: null,
    permissions_verified: false,
    user_input_required: false,
  };
}

function mockReport(reportId) {
  return { id: reportId, markdown: `# ${reportId}\n\n**Status:** demo\n\n- Backend är inte ansluten.\n- När backend finns hämtas rapporten från \`/api/reports/${reportId}\`.` };
}

function mockJobs() {
  return [];
}

function mockJob(type, command) {
  return normalizeJob({
    job_id: `mock-${Date.now()}`,
    type,
    title: `${type}: ${command}`,
    command,
    status: "queued",
    output_tail: "Mockat asynkront jobb skapat eftersom backend inte svarade.",
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}
