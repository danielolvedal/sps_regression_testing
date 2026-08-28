import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import childProcess from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';
import pty from 'node-pty';
import xtermHeadless from '@xterm/headless';

const { Terminal: HeadlessTerminal } = xtermHeadless;

const scriptDir = path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1');
const repoRoot = path.resolve(scriptDir, '..', '..', '..', '..');
const logDir = path.join(repoRoot, 'tmp', 'copilot_admin_runner_logs');
const stateDir = path.resolve(process.env.COPILOT_ADMIN_RUNNER_STATE_DIR || path.join(repoRoot, 'tmp', 'copilot_admin_runner_state'));
const sessionId = process.env.COPILOT_ADMIN_RUNNER_SESSION_ID || 'node-pty-copilot';
const registryScript = path.join(repoRoot, 'tools', 'source', 'copilot_admin_runner', 'project_session_registry.py');
let transportSchemaInitialized = false;

function sleepMs(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function utcStamp() {
  return new Date().toISOString();
}

function logPath() {
  const day = utcStamp().slice(0, 10).replaceAll('-', '');
  return path.join(logDir, `node-pty-poc-${day}.jsonl`);
}

function ensureDirs() {
  fs.mkdirSync(logDir, { recursive: true });
  fs.mkdirSync(stateDir, { recursive: true });
}

function logEvent(event, details = {}) {
  ensureDirs();
  const record = {
    timestamp: utcStamp(),
    level: details.level ?? 'info',
    component: 'node-pty',
    event_id: crypto.randomUUID(),
    event,
    trace_id: details.trace_id ?? null,
    session_id: details.session_id ?? sessionId,
    job_id: details.job_id ?? null,
    status: details.status ?? null,
    pid: process.pid,
    repo_root: repoRoot,
    details,
  };
  fs.appendFileSync(logPath(), `${JSON.stringify(record)}\n`, 'utf8');
  if (record.trace_id || record.job_id) {
    recordTraceEvent({
      component: 'node-pty',
      event,
      trace_id: record.trace_id,
      job_id: record.job_id,
      status: record.status,
      details,
    });
  }
}

function writeJson(payload) {
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
}

function writeTextFileAtomic(filePath, text) {
  const tempPath = `${filePath}.${process.pid}.${crypto.randomUUID()}.tmp`;
  try {
    fs.writeFileSync(tempPath, text, 'utf8');
    fs.renameSync(tempPath, filePath);
  } finally {
    if (fs.existsSync(tempPath)) {
      fs.rmSync(tempPath, { force: true });
    }
  }
}

function writeJsonFileAtomic(filePath, payload) {
  writeTextFileAtomic(filePath, JSON.stringify(payload, null, 2));
}

function transcriptPath() {
  return path.join(stateDir, 'node-pty-copilot-session-output.txt');
}

function rawTranscriptPath() {
  return path.join(stateDir, 'node-pty-copilot-session-output-raw.txt');
}

function inputTranscriptPath() {
  return path.join(stateDir, 'node-pty-copilot-session-input.txt');
}

function inputQueueDir() {
  return path.join(stateDir, 'node-pty-copilot-input-queue');
}

function transportDbPath() {
  return path.join(stateDir, 'copilot-admin-transport.sqlite');
}

function sessionStateLocator() {
  return `${transportDbPath()}#session_state`;
}

function registrySessionKey() {
  return `node-pty::${stateDir}`;
}

function syncProjectSessionRegistry(args) {
  const result = childProcess.spawnSync('python', [registryScript, ...args], {
    cwd: repoRoot,
    encoding: 'utf8',
  });
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || '').trim();
    logEvent('project_session_registry_failed', { status: result.status, detail, args });
  }
}

function queueSnapshot(queueDir) {
  const dbPath = transportDbPath();
  try {
    const database = openTransportDb(dbPath);
    const counts = Object.fromEntries(
      database.prepare('SELECT status, COUNT(*) AS count FROM input_queue GROUP BY status').all().map((row) => [row.status, Number(row.count)]),
    );
    const latestItems = database.prepare(`
      SELECT input_id, status, job_id, trace_id, created_at, claimed_at, completed_at
      FROM input_queue
      ORDER BY id DESC
      LIMIT 10
    `).all();
    database.close();
    return {
      queue_dir: queueDir,
      db_path: dbPath,
      pending: counts.queued ?? 0,
      claimed: counts.claimed ?? 0,
      sent: counts.sent ?? 0,
      failed: counts.failed ?? 0,
      skipped: counts.skipped ?? 0,
      abandoned: counts.abandoned ?? 0,
      latest_items: latestItems,
    };
  } catch (error) {
    return {
      queue_dir: queueDir,
      db_path: dbPath,
      pending: null,
      claimed: null,
      sent: null,
      failed: null,
      skipped: null,
      abandoned: null,
      error: error.message,
      latest_items: [],
    };
  }
}

function openTransportDb(dbPath = transportDbPath()) {
  ensureDirs();
  const database = new DatabaseSync(dbPath);
  database.exec('PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA busy_timeout = 5000;');
  if (!transportSchemaInitialized) {
    database.exec(`
      CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      );
      CREATE TABLE IF NOT EXISTS input_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_id TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        source TEXT NOT NULL,
        status TEXT NOT NULL,
        text TEXT NOT NULL,
        display_text TEXT,
        clear_line INTEGER NOT NULL DEFAULT 0,
        submit INTEGER NOT NULL DEFAULT 1,
        job_id TEXT,
        trace_id TEXT,
        client_sent_at TEXT,
        backend_accepted_at TEXT,
        backend_queued_at TEXT,
        host_runner_received_at TEXT,
        host_runner_queued_at TEXT,
        claimed_at TEXT,
        claimed_by TEXT,
        pty_write_at TEXT,
        completed_at TEXT,
        error_message TEXT
      );
      CREATE INDEX IF NOT EXISTS idx_input_queue_status_created
        ON input_queue (status, created_at, id);
      CREATE INDEX IF NOT EXISTS idx_input_queue_trace
        ON input_queue (trace_id, created_at, id);
      CREATE INDEX IF NOT EXISTS idx_input_queue_job
        ON input_queue (job_id, created_at, id);
      CREATE TABLE IF NOT EXISTS trace_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        trace_id TEXT,
        job_id TEXT,
        component TEXT NOT NULL,
        event TEXT NOT NULL,
        status TEXT,
        details_json TEXT
      );
      CREATE INDEX IF NOT EXISTS idx_trace_events_trace_created
        ON trace_events (trace_id, created_at, id);
      CREATE INDEX IF NOT EXISTS idx_trace_events_job_created
        ON trace_events (job_id, created_at, id);
      CREATE INDEX IF NOT EXISTS idx_trace_events_component_event_created
        ON trace_events (component, event, created_at, id);
      CREATE TABLE IF NOT EXISTS session_state (
        session_id TEXT PRIMARY KEY,
        updated_at TEXT NOT NULL,
        status TEXT NOT NULL,
        wrapper_pid INTEGER,
        launcher_pid INTEGER,
        visible_window_expected INTEGER,
        user_input_required INTEGER,
        last_output_chunk_at TEXT,
        last_output_sequence INTEGER,
        last_input_job_id TEXT,
        transcript_path TEXT,
        payload_json TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_session_state_status_updated
        ON session_state (status, updated_at);
      INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '2');
    `);
    transportSchemaInitialized = true;
  }
  return database;
}

function isSqliteBusyError(error) {
  const message = String(error?.message ?? '');
  return error?.code === 'ERR_SQLITE_ERROR' && /database is locked/i.test(message);
}

function withSqliteRetry(action, { attempts = 6, delayMs = 50, context = 'sqlite' } = {}) {
  let lastError = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return action();
    } catch (error) {
      lastError = error;
      if (!isSqliteBusyError(error) || attempt === attempts) {
        throw error;
      }
      logEvent('sqlite_busy_retry', {
        level: 'warn',
        context,
        attempt,
        attempts,
        message: error.message,
      });
      sleepMs(delayMs * attempt);
    }
  }
  throw lastError;
}

function upsertSessionState(payload) {
  const state = {
    ...payload,
    session_id: payload.session_id ?? sessionId,
    updated_at: payload.updated_at ?? utcStamp(),
  };
  withSqliteRetry(() => {
    const database = openTransportDb();
    try {
      database.prepare(`
        INSERT INTO session_state (
          session_id, updated_at, status, wrapper_pid, launcher_pid,
          visible_window_expected, user_input_required, last_output_chunk_at,
          last_output_sequence, last_input_job_id, transcript_path, payload_json
        ) VALUES (
          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(session_id) DO UPDATE SET
          updated_at = excluded.updated_at,
          status = excluded.status,
          wrapper_pid = excluded.wrapper_pid,
          launcher_pid = excluded.launcher_pid,
          visible_window_expected = excluded.visible_window_expected,
          user_input_required = excluded.user_input_required,
          last_output_chunk_at = excluded.last_output_chunk_at,
          last_output_sequence = excluded.last_output_sequence,
          last_input_job_id = excluded.last_input_job_id,
          transcript_path = excluded.transcript_path,
          payload_json = excluded.payload_json
      `).run(
        state.session_id,
        state.updated_at,
        state.status ?? 'unknown',
        state.wrapper_pid ?? null,
        state.launcher_pid ?? null,
        state.visible_window_expected ? 1 : 0,
        state.user_input_required ? 1 : 0,
        state.last_output_chunk_at ?? null,
        Number(state.last_output_sequence ?? 0),
        state.last_input_job_id ?? null,
        state.transcript_path ?? null,
        JSON.stringify(state),
      );
    } finally {
      database.close();
    }
  }, { context: 'session_state_upsert' });
  return state;
}

function recordTraceEvent(details) {
  withSqliteRetry(() => {
    const database = openTransportDb();
    try {
      database.prepare(`
        INSERT INTO trace_events (
          event_id, created_at, trace_id, job_id, component, event, status, details_json
        ) VALUES (
          ?, ?, ?, ?, ?, ?, ?, ?
        )
      `).run(
        crypto.randomUUID().replaceAll('-', ''),
        utcStamp(),
        details.trace_id ?? null,
        details.job_id ?? null,
        details.component,
        details.event,
        details.status ?? null,
        JSON.stringify(details.details ?? {}),
      );
    } finally {
      database.close();
    }
  }, { context: 'trace_event_insert' });
}

function stripAnsi(text) {
  return text.replace(/\x1B(?:\][^\x07]*(?:\x07|\x1B\\)|\[[0-?]*[ -/]*[@-~]|[@-Z\\-_])/g, '');
}

function detectUserInputRequest(text) {
  const normalized = text.toLowerCase();
  const permissionsConfirmed = hasPermissionConfirmation(normalized);
  const patterns = [
    {
      reason: 'directory_trust_prompt',
      pattern: /trust (the )?(files|folder|directory)|trusted workspace|do you trust|approve.*(folder|directory)/i,
    },
    {
      reason: 'confirmation_prompt',
      pattern: /\(y\/n\)|\[y\/n\]|yes\/no|press enter|continue\?/i,
    },
    {
      reason: 'authentication_prompt',
      pattern: /sign in|log in|login|authenticate|device code|authorization/i,
    },
  ];

  for (const item of patterns) {
    if (item.reason === 'directory_trust_prompt' && permissionsConfirmed) {
      continue;
    }
    if (item.pattern.test(normalized)) {
      return {
        required: true,
        reason: item.reason,
      };
    }
  }

  return {
    required: false,
    reason: null,
  };
}

function hasPermissionConfirmation(text) {
  return /all permissions are now enabled|tool, path, and url requests will be automatically approved/i.test(text);
}

const PERMISSION_ALLOW_ALL_COMMAND = '/permissions allow-all';

function sendStartupCommand(term, command) {
  term.write('\x15');
  term.write(`${command}\r`);
}

function parseArgs(argv) {
  const [command, ...rest] = argv;
  return { command, rest };
}

function optionValue(args, name, defaultValue = null) {
  const index = args.indexOf(name);
  if (index < 0 || index + 1 >= args.length) {
    return defaultValue;
  }
  return args[index + 1];
}

function integerOption(value, fallback) {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function configuredTerminalCols() {
  return integerOption(process.env.COPILOT_ADMIN_PTY_COLS, 160);
}

function configuredTerminalRows() {
  return integerOption(process.env.COPILOT_ADMIN_PTY_ROWS, 42);
}

function renderTerminalViewport(screen) {
  const buffer = screen.buffer.active;
  const start = Math.max(0, buffer.baseY);
  const end = start + screen.rows;
  const lines = [];
  for (let index = start; index < end; index += 1) {
    const line = buffer.getLine(index);
    lines.push(line ? line.translateToString(true).replace(/\u00A0/g, ' ') : '');
  }
  while (lines.length > 1 && lines[lines.length - 1] === '') {
    lines.pop();
  }
  return lines.join('\n');
}

function detectCurrentModel(text) {
  const changed = String(text || '').match(/Model changed from .* to ([^.]+?) for this session/i);
  if (changed?.[1]) {
    return changed[1].trim();
  }
  return null;
}

function hasCopilotCommandPrompt(text) {
  const normalized = String(text || '');
  return /open sidebar .*\/ commands .*help .*tab next tab/i.test(normalized)
    || /C:\\Copilot_projects\\SPS \[.*\]/i.test(normalized);
}

function hasPendingCopilotActivity(text) {
  return /(◉|○)\s+(Working|Loading)\b/i.test(String(text || ''));
}

function isReadyForStartupCommand(text) {
  return hasCopilotCommandPrompt(text) && !hasPendingCopilotActivity(text);
}

function hasRestoreInterruptedSessionsPrompt(text) {
  return /Restore interrupted sessions:/i.test(String(text || ''))
    && /esc start fresh/i.test(String(text || ''));
}

function spawnPty(command, args, options = {}) {
  const cols = options.cols ?? configuredTerminalCols();
  const rows = options.rows ?? configuredTerminalRows();
  return pty.spawn(command, args, {
    name: 'xterm-256color',
    cols,
    rows,
    cwd: repoRoot,
    env: {
      ...process.env,
      TERM: 'xterm-256color',
    },
  });
}

function copilotCommand() {
  return process.env.COPILOT_CLI_PATH || 'copilot';
}

async function runProbe() {
  return runScripted(['cmd.exe', '/d', '/c', 'echo node-pty-probe-ok'], {
    expected: 'node-pty-probe-ok',
    timeoutMs: 10000,
  });
}

async function runScripted(parts, options = {}) {
  if (parts.length === 0) {
    throw new Error('scripted requires a command after --');
  }
  const [command, ...args] = parts;
  const timeoutMs = options.timeoutMs ?? 20000;
  const expected = options.expected;
  const sendLines = options.sendLines ?? [];
  const mirror = options.mirror ?? false;
  let output = '';
  let exitCode = null;
  let signal = null;

  logEvent('node_pty_scripted_started', { command, args, timeout_ms: timeoutMs });
  const term = spawnPty(command, args);
  term.onData((data) => {
    output += data;
    if (mirror) {
      process.stdout.write(data);
    }
  });
  term.onExit((event) => {
    exitCode = event.exitCode;
    signal = event.signal;
  });

  for (const line of sendLines) {
    term.write(`${line}\r`);
  }

  const started = Date.now();
  while (exitCode === null && Date.now() - started < timeoutMs) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  let status = 'completed';
  if (exitCode === null) {
    status = 'timeout_terminated';
    term.kill();
  }

  const plainOutput = stripAnsi(output);
  const userInputRequest = detectUserInputRequest(plainOutput);
  const passed = status === 'completed' && (!expected || plainOutput.includes(expected));
  if (!passed && userInputRequest.required) {
    status = 'user_input_required';
  }
  const payload = {
    status: passed ? 'passed' : status === 'completed' ? 'completed' : status,
    mode: 'scripted',
    command,
    args,
    exit_code: exitCode,
    signal,
    expected,
    expected_found: expected ? plainOutput.includes(expected) : null,
    user_input_required: userInputRequest.required,
    user_input_reason: userInputRequest.reason,
    captured_output_tail: plainOutput.slice(-4000),
    raw_output_tail: output.slice(-4000),
    log_path: logPath(),
    conclusion: passed
      ? 'node-pty owns PTY stdin/stdout for this command.'
      : userInputRequest.required
        ? 'Copilot appears to be waiting for user input in the PTY, not hung.'
      : 'node-pty did not prove successful command completion for this case.',
  };
  logEvent('node_pty_scripted_completed', {
    command,
    args,
    status: payload.status,
    exit_code: exitCode,
    expected_found: payload.expected_found,
    user_input_required: payload.user_input_required,
    user_input_reason: payload.user_input_reason,
  });
  writeJson(payload);
  return passed ? 0 : 1;
}

async function runInteractiveCopilot(options = {}) {
  ensureDirs();
  const sessionTranscriptPath = transcriptPath();
  const sessionRawTranscriptPath = rawTranscriptPath();
  const sessionInputTranscriptPath = inputTranscriptPath();
  const sessionInputQueueDir = inputQueueDir();
  const sessionStateDbPath = transportDbPath();
  const sessionStatePath = sessionStateLocator();
  const command = copilotCommand();
  const terminalCols = configuredTerminalCols();
  const terminalRows = configuredTerminalRows();
  const launcherPid = Number.parseInt(process.env.COPILOT_ADMIN_LAUNCHER_PID ?? '', 10) || null;
  const term = spawnPty(command, [], { cols: terminalCols, rows: terminalRows });
  const screen = new HeadlessTerminal({ cols: terminalCols, rows: terminalRows, scrollback: 1000, allowProposedApi: true });
  const hiddenWindow = process.env.COPILOT_ADMIN_PROJECT_SESSION_HIDDEN === '1';
  const startedAt = utcStamp();
  let screenText = '';
  let recentPlainStream = '';
  let inputText = '';
  let lastInjectedText = '';
  let lastOutputChunkAt = null;
  let lastOutputChunkBytes = 0;
  let lastOutputSequence = 0;
  let lastOutputTranscriptSize = 0;
  let lastInputClientSentAt = null;
  let lastInputBackendAcceptedAt = null;
  let lastInputHostRunnerReceivedAt = null;
  let lastInputHostRunnerQueuedAt = null;
  let lastInputQueueFileSeenAt = null;
  let lastInputPtyWriteAt = null;
  let lastInputTraceId = null;
  let lastInputJobId = null;
  let trustAccepted = false;
  let trustAcceptanceSubmitted = false;
  let restoreSessionsDismissed = false;
  let startupCommandsSent = false;
  let allowAllCommandSent = false;
  let modelCommandSent = false;
  let startupModelRequested = options.startupModel ?? null;
  let startupModel = options.startupModel ?? null;
  let startupAllowAllRequested = Boolean(options.allowAll);
  let startupAllowAll = Boolean(options.allowAll);
  let allowAllVerified = false;
  let permissionsHint = null;
  let permissionsObservedAt = null;
  let modelVerified = false;
  let currentModel = null;
  let directoryTrustRequested = Boolean(options.allowAll);
  let directoryTrustVerified = false;
  let directoryTrustObservedAt = null;
  let startupPolicyState = null;
  let lastInjectedAt = null;
  let lastInjectedSubmit = null;
  let lastInjectedClearLine = null;

  fs.mkdirSync(sessionInputQueueDir, { recursive: true });
  const transportDatabase = openTransportDb();
  transportDatabase.close();
  const startupDb = openTransportDb();
  const abandonedInputs = startupDb.prepare(`
    UPDATE input_queue
    SET status = 'abandoned',
        completed_at = ?,
        error_message = COALESCE(error_message, ?)
    WHERE status IN ('queued', 'claimed')
  `).run(utcStamp(), 'node-pty restarted before queued input was fully processed');
  startupDb.close();
  if (Number(abandonedInputs.changes ?? 0) > 0) {
    logEvent('node_pty_interactive_abandoned_stale_inputs', {
      status: 'abandoned',
      abandoned_count: Number(abandonedInputs.changes ?? 0),
    });
  }

  function writeSessionState(extra = {}) {
    const recentOutput = screenText.slice(-4000);
    const userInputRequest = detectUserInputRequest(recentOutput);
    try {
      upsertSessionState({
        session_id: sessionId,
        status: 'running',
        started_at: startedAt,
        updated_at: utcStamp(),
        repo_root: repoRoot,
        mode: 'node-pty-interactive-copilot',
        wrapper_pid: process.pid,
        launcher_pid: extra.launcher_pid ?? launcherPid,
        hidden: hiddenWindow,
        visible_window_expected: !hiddenWindow,
        state_storage: 'sqlite',
        state_db_path: sessionStateDbPath,
        state_path: sessionStatePath,
        window_state_path: sessionStatePath,
        copilot_command: command,
        log_path: logPath(),
        transcript_path: sessionTranscriptPath,
        transcript_kind: 'screen_snapshot',
        raw_transcript_path: sessionRawTranscriptPath,
        input_logging_enabled: Boolean(options.logInput),
        input_transcript_path: options.logInput ? sessionInputTranscriptPath : null,
        input_queue_dir: sessionInputQueueDir,
        input_queue_db_path: transportDbPath(),
        trace_db_path: transportDbPath(),
        input_queue_status: queueSnapshot(sessionInputQueueDir),
        user_input_required: userInputRequest.required,
        user_input_reason: userInputRequest.reason,
        last_output_tail: screenText.slice(-4000),
        last_output_chunk_at: lastOutputChunkAt,
        last_output_chunk_bytes: lastOutputChunkBytes,
        last_output_sequence: lastOutputSequence,
        last_output_transcript_size: lastOutputTranscriptSize,
        last_input_client_sent_at: lastInputClientSentAt,
        last_input_backend_queued_at: lastInputBackendAcceptedAt,
        last_input_host_runner_received_at: lastInputHostRunnerReceivedAt,
        last_input_host_runner_queued_at: lastInputHostRunnerQueuedAt,
        last_input_queue_file_seen_at: lastInputQueueFileSeenAt,
        last_input_pty_write_at: lastInputPtyWriteAt,
        last_input_trace_id: lastInputTraceId,
        last_input_job_id: lastInputJobId,
        last_input_tail: options.logInput ? inputText.slice(-1000) : null,
        last_injected_text: lastInjectedText,
        last_injected_at: lastInjectedAt,
        last_injected_submit: lastInjectedSubmit,
        last_injected_clear_line: lastInjectedClearLine,
        startup_model_requested: startupModelRequested,
        startup_model: startupModel,
        startup_allow_all_requested: startupAllowAllRequested,
        startup_allow_all: startupAllowAll,
        startup_commands_sent: startupCommandsSent,
        allow_all_verified: allowAllVerified,
        permissions_hint: permissionsHint,
        permissions_observed_at: permissionsObservedAt,
        model_verified: modelVerified,
        current_model: currentModel,
        terminal_cols: terminalCols,
        terminal_rows: terminalRows,
        directory_trust_requested: directoryTrustRequested,
        directory_trust_verified: directoryTrustVerified,
        directory_trust_observed_at: directoryTrustObservedAt,
        startup_policy_state: startupPolicyState,
        note: 'node-pty owns stdin/stdout and mirrors output to this terminal. Type here to send input to Copilot.',
        ...extra,
      });
    } catch (error) {
      if (isSqliteBusyError(error)) {
        logEvent('node_pty_session_state_write_blocked', {
          level: 'warn',
          message: error.message,
          updated_at: utcStamp(),
        });
        return;
      }
      throw error;
    }
  }

  fs.writeFileSync(sessionTranscriptPath, '', 'utf8');
  fs.writeFileSync(sessionRawTranscriptPath, '', 'utf8');
  if (options.logInput) {
    fs.writeFileSync(sessionInputTranscriptPath, '', 'utf8');
  }
  writeSessionState();
  logEvent('node_pty_interactive_started', {
    command,
    state_db_path: sessionStateDbPath,
    state_path: sessionStatePath,
    transcript_path: sessionTranscriptPath,
    raw_transcript_path: sessionRawTranscriptPath,
    input_logging_enabled: Boolean(options.logInput),
    input_transcript_path: options.logInput ? sessionInputTranscriptPath : null,
    input_queue_dir: sessionInputQueueDir,
    terminal_cols: terminalCols,
    terminal_rows: terminalRows,
  });
  syncProjectSessionRegistry([
    'upsert',
    '--session-key', registrySessionKey(),
    '--kind', 'node-pty',
    '--source', 'tools\\source\\copilot_admin_runner\\node_pty_poc\\node_pty_poc.mjs',
    '--status', 'running',
    '--control-method', 'runner-state',
    '--state-dir', stateDir,
    '--state-path', sessionStatePath,
    '--window-state-path', sessionStatePath,
    '--wrapper-pid', String(process.pid),
    '--hidden', hiddenWindow ? 'true' : 'false',
    '--visible-window-expected', hiddenWindow ? 'false' : 'true',
    '--note', 'node-pty interactive Copilot wrapper',
  ]);

  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true);
  }
  process.stdin.resume();
  process.stdin.on('data', (data) => {
    if (data.length === 1 && data[0] === 0x03) {
      writeSessionState({ status: 'stopping', stopped_by: 'ctrl_c' });
      syncProjectSessionRegistry(['mark-stopped', '--session-key', registrySessionKey()]);
      term.kill();
      process.exit(0);
    }
    if (options.logInput) {
      const text = data.toString('utf8');
      inputText += text;
      fs.appendFileSync(sessionInputTranscriptPath, text, 'utf8');
      writeSessionState();
      logEvent('node_pty_interactive_input_forwarded', { byte_count: data.length, text });
    } else {
      logEvent('node_pty_interactive_input_forwarded', { byte_count: data.length });
    }
    term.write(data.toString('utf8'));
  });
  term.onData((data) => {
    recentPlainStream = `${recentPlainStream}${stripAnsi(data)}`.slice(-16000);
    fs.appendFileSync(sessionRawTranscriptPath, data, 'utf8');
    screen.write(data, () => {
      screenText = renderTerminalViewport(screen);
      const recentOutput = screenText.slice(-4000);
      const detectedModel = detectCurrentModel(recentOutput);
      if (detectedModel) {
        currentModel = detectedModel;
        modelVerified = true;
        startupPolicyState = allowAllVerified || !startupAllowAllRequested ? 'ready' : 'model_verified';
      }
      if (hasPermissionConfirmation(recentOutput)) {
        directoryTrustRequested = true;
        directoryTrustVerified = true;
        directoryTrustObservedAt = directoryTrustObservedAt || utcStamp();
        allowAllVerified = true;
        permissionsHint = 'allow-all';
        permissionsObservedAt = permissionsObservedAt || utcStamp();
        startupPolicyState = modelVerified ? 'ready' : 'allow_all_verified';
        trustAccepted = true;
      }
      fs.writeFileSync(sessionTranscriptPath, screenText, 'utf8');
      lastOutputChunkAt = utcStamp();
      lastOutputChunkBytes = Buffer.byteLength(data, 'utf8');
      lastOutputSequence += 1;
      lastOutputTranscriptSize = Buffer.byteLength(screenText, 'utf8');
      writeSessionState();
      if (lastInputTraceId || lastInputJobId) {
        recordTraceEvent({
          component: 'node-pty',
          event: 'output_chunk_captured',
          trace_id: lastInputTraceId,
          job_id: lastInputJobId,
          status: 'output',
          details: {
            chunk_bytes: lastOutputChunkBytes,
            output_sequence: lastOutputSequence,
            transcript_size: lastOutputTranscriptSize,
            output_detected_at: lastOutputChunkAt,
          },
        });
      }
    });
    process.stdout.write(data);
  });
  term.onExit((event) => {
    writeSessionState({ status: 'exited', exit_code: event.exitCode, signal: event.signal });
    syncProjectSessionRegistry(['mark-stopped', '--session-key', registrySessionKey()]);
    logEvent('node_pty_interactive_exited', event);
    process.exit(event.exitCode ?? 0);
  });

  const queueTimer = setInterval(() => {
    try {
      const database = openTransportDb();
      const claim = database.prepare(`
        UPDATE input_queue
        SET status = 'claimed',
            claimed_at = ?,
            claimed_by = ?
        WHERE input_id = (
          SELECT input_id
          FROM input_queue
          WHERE status = 'queued'
          ORDER BY created_at ASC, id ASC
          LIMIT 1
        )
        RETURNING *
      `).get(utcStamp(), sessionId);
      database.close();
      if (claim) {
        const request = claim;
        const text = String(request.text ?? '');
        const submit = request.submit !== 0;
        const clearLine = request.clear_line === 1;
        const queueClaimedAt = request.claimed_at ?? utcStamp();
        if (!text) {
          const skippedDb = openTransportDb();
          skippedDb.prepare(`
            UPDATE input_queue
            SET status = 'skipped',
                completed_at = ?,
                error_message = ?
            WHERE input_id = ?
          `).run(utcStamp(), 'empty_text', request.input_id);
          skippedDb.close();
          logEvent('node_pty_interactive_injection_skipped', { input_id: request.input_id, reason: 'empty_text', trace_id: request.trace_id ?? null, job_id: request.job_id ?? null });
        } else {
          if (clearLine && !text.startsWith('\x15')) {
            term.write('\x15');
          }
          const payload = submit ? `${text}\r` : text;
          term.write(payload);
          const ptyWriteAt = utcStamp();
          const sentDb = openTransportDb();
          sentDb.prepare(`
            UPDATE input_queue
            SET status = 'sent',
                pty_write_at = ?,
                completed_at = ?
            WHERE input_id = ?
          `).run(ptyWriteAt, ptyWriteAt, request.input_id);
          sentDb.close();
          lastInjectedText = String(request.display_text ?? text);
          lastInputClientSentAt = request.client_sent_at ?? null;
          lastInputBackendAcceptedAt = request.backend_accepted_at ?? request.backend_queued_at ?? null;
          lastInputHostRunnerReceivedAt = request.host_runner_received_at ?? null;
          lastInputHostRunnerQueuedAt = request.host_runner_queued_at ?? null;
          lastInputQueueFileSeenAt = queueClaimedAt;
          lastInputPtyWriteAt = ptyWriteAt;
          lastInputTraceId = request.trace_id ?? null;
          lastInputJobId = request.job_id ?? null;
          lastInjectedAt = ptyWriteAt;
          lastInjectedSubmit = submit;
          lastInjectedClearLine = clearLine;
          writeSessionState();
          logEvent('node_pty_interactive_injection_sent', {
            input_id: request.input_id,
            byte_count: Buffer.byteLength(payload),
            submit,
            clear_line: clearLine,
            client_sent_at: request.client_sent_at ?? null,
            backend_accepted_at: request.backend_accepted_at ?? request.backend_queued_at ?? null,
            host_runner_received_at: request.host_runner_received_at ?? null,
            host_runner_queued_at: request.host_runner_queued_at ?? null,
            queue_claimed_at: queueClaimedAt,
            pty_write_at: ptyWriteAt,
            trace_id: request.trace_id ?? null,
            job_id: request.job_id ?? null,
            text,
          });
        }
      }
    } catch (error) {
      logEvent('node_pty_interactive_injection_error', { message: error.message, stack: error.stack });
    }
  }, 50);
  queueTimer.unref();

  const startupTimer = setInterval(() => {
    const recentOutput = screenText.slice(-4000) || recentPlainStream.slice(-4000);
    const userInputRequest = detectUserInputRequest(recentOutput);
    if (hasRestoreInterruptedSessionsPrompt(recentOutput)) {
      if (!restoreSessionsDismissed) {
        restoreSessionsDismissed = true;
        startupPolicyState = 'restore_sessions_dismissed';
        term.write('\x1B');
        lastInjectedText = '<ESC>';
        lastInjectedAt = utcStamp();
        lastInjectedSubmit = false;
        lastInjectedClearLine = false;
        writeSessionState();
        logEvent('node_pty_startup_restore_sessions_dismissed', { action: 'esc_start_fresh' });
      }
      return;
    }
    if (hasPermissionConfirmation(recentOutput) && !trustAccepted) {
      trustAccepted = true;
      directoryTrustRequested = true;
      directoryTrustVerified = true;
      directoryTrustObservedAt = directoryTrustObservedAt || utcStamp();
      allowAllVerified = true;
      permissionsHint = 'allow-all';
      permissionsObservedAt = permissionsObservedAt || utcStamp();
      startupPolicyState = 'directory_trust_accepted';
      writeSessionState();
      logEvent('node_pty_startup_trust_accepted', { mode: 'permission_confirmation_output' });
      return;
    }
    if (userInputRequest.reason === 'directory_trust_prompt') {
      if (!trustAcceptanceSubmitted) {
        trustAcceptanceSubmitted = true;
        directoryTrustRequested = true;
        directoryTrustVerified = false;
        startupPolicyState = 'directory_trust_submitted';
        term.write('\r');
        lastInjectedText = '<ENTER>';
        lastInjectedAt = utcStamp();
        lastInjectedSubmit = true;
        lastInjectedClearLine = false;
        writeSessionState({
          startup_trust_action: 'accepted_session_default_enter',
        });
        logEvent('node_pty_startup_trust_submitted', { mode: 'session_default_enter' });
      }
      return;
    }
    if (trustAcceptanceSubmitted && !trustAccepted) {
      trustAccepted = true;
      directoryTrustRequested = true;
      directoryTrustVerified = true;
      directoryTrustObservedAt = utcStamp();
      startupPolicyState = 'directory_trust_accepted';
      writeSessionState();
      logEvent('node_pty_startup_trust_accepted', { mode: 'session_default_enter' });
    }
    if (startupCommandsSent || userInputRequest.required) {
      startupCommandsSent =
        (!options.allowAll || allowAllCommandSent)
        && (!options.startupModel || modelCommandSent);
    }
    if (userInputRequest.required) {
      return;
    }
    if (!isReadyForStartupCommand(recentOutput)) {
      return;
    }
    if (options.allowAll && !allowAllCommandSent) {
      allowAllCommandSent = true;
      sendStartupCommand(term, PERMISSION_ALLOW_ALL_COMMAND);
      lastInjectedText = PERMISSION_ALLOW_ALL_COMMAND;
      lastInjectedAt = utcStamp();
      lastInjectedSubmit = true;
      lastInjectedClearLine = true;
      startupCommandsSent = !options.startupModel;
      permissionsHint = 'allow-all';
      startupPolicyState = 'allow_all_sent';
      writeSessionState();
      logEvent('node_pty_startup_command_sent', { command: PERMISSION_ALLOW_ALL_COMMAND });
      return;
    }
    if (options.startupModel && (!options.allowAll || allowAllVerified) && !modelCommandSent) {
      modelCommandSent = true;
      const startupModelCommand = `/model ${options.startupModel}`;
      sendStartupCommand(term, startupModelCommand);
      lastInjectedText = startupModelCommand;
      lastInjectedAt = utcStamp();
      lastInjectedSubmit = true;
      lastInjectedClearLine = true;
      modelVerified = false;
      currentModel = null;
      startupCommandsSent = true;
      startupPolicyState = 'model_sent';
      writeSessionState();
      logEvent('node_pty_startup_command_sent', { command: '/model <configured>' });
      return;
    }
    if ((!options.allowAll || allowAllVerified) && (!options.startupModel || modelVerified)) {
      startupCommandsSent = true;
      startupPolicyState = 'ready';
      writeSessionState();
    }
  }, 200);
  startupTimer.unref();
}

async function main() {
  const { command, rest } = parseArgs(process.argv.slice(2));
  if (command === 'probe') {
    process.exit(await runProbe());
  }
  if (command === 'scripted') {
    const separatorIndex = rest.indexOf('--');
    const parts = separatorIndex >= 0 ? rest.slice(separatorIndex + 1) : rest;
    process.exit(await runScripted(parts));
  }
  if (command === 'copilot-prompt') {
    const prompt = rest.join(' ') || 'Svara exakt: node-pty-copilot-prompt-ok';
    process.exit(await runScripted([copilotCommand(), '-p', prompt], {
      expected: 'node-pty-copilot-prompt-ok',
      timeoutMs: 60000,
    }));
  }
  if (command === 'interactive-copilot') {
    await runInteractiveCopilot({
      logInput: rest.includes('--log-input'),
      startupModel: optionValue(rest, '--startup-model'),
      allowAll: rest.includes('--allow-all'),
    });
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}

main().catch((error) => {
  logEvent('node_pty_error', { message: error.message, stack: error.stack });
  console.error(error);
  process.exitCode = 1;
});
