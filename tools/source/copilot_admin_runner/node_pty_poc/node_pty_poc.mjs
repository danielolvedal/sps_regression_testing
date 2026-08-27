import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import pty from 'node-pty';

const scriptDir = path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1');
const repoRoot = path.resolve(scriptDir, '..', '..', '..', '..');
const logDir = path.join(repoRoot, 'tmp', 'copilot_admin_runner_logs');
const stateDir = path.resolve(process.env.COPILOT_ADMIN_RUNNER_STATE_DIR || path.join(repoRoot, 'tmp', 'copilot_admin_runner_state'));
const sessionId = process.env.COPILOT_ADMIN_RUNNER_SESSION_ID || 'node-pty-copilot';

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
}

function writeJson(payload) {
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
}

function statePath() {
  return path.join(stateDir, 'node-pty-copilot-session.json');
}

function transcriptPath() {
  return path.join(stateDir, 'node-pty-copilot-session-output.txt');
}

function inputTranscriptPath() {
  return path.join(stateDir, 'node-pty-copilot-session-input.txt');
}

function inputQueueDir() {
  return path.join(stateDir, 'node-pty-copilot-input-queue');
}

function queueSnapshot(queueDir) {
  try {
    fs.mkdirSync(queueDir, { recursive: true });
    const files = fs.readdirSync(queueDir);
    return {
      queue_dir: queueDir,
      pending: files.filter((name) => name.endsWith('.json')).length,
      done: files.filter((name) => name.endsWith('.json.done')).length,
      invalid: files.filter((name) => name.endsWith('.json.invalid')).length,
      skipped: files.filter((name) => name.endsWith('.json.skipped')).length,
      latest_files: files.sort().slice(-10),
    };
  } catch (error) {
    return {
      queue_dir: queueDir,
      pending: null,
      done: null,
      invalid: null,
      skipped: null,
      error: error.message,
      latest_files: [],
    };
  }
}

function stripAnsi(text) {
  return text.replace(/\x1B(?:\][^\x07]*(?:\x07|\x1B\\)|\[[0-?]*[ -/]*[@-~]|[@-Z\\-_])/g, '');
}

function detectUserInputRequest(text) {
  const normalized = text.toLowerCase();
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

function spawnPty(command, args, options = {}) {
  const cols = options.cols ?? 240;
  const rows = options.rows ?? 40;
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
  const sessionStatePath = statePath();
  const sessionTranscriptPath = transcriptPath();
  const sessionInputTranscriptPath = inputTranscriptPath();
  const sessionInputQueueDir = inputQueueDir();
  const command = copilotCommand();
  const term = spawnPty(command, []);
  const startedAt = utcStamp();
  let plainOutput = '';
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
  let startupCommandsSent = false;

  fs.mkdirSync(sessionInputQueueDir, { recursive: true });

  function writeSessionState(extra = {}) {
    const recentOutput = plainOutput.slice(-1200);
    const userInputRequest = detectUserInputRequest(recentOutput);
    fs.writeFileSync(
      sessionStatePath,
      JSON.stringify(
        {
          status: 'running',
          started_at: startedAt,
          updated_at: utcStamp(),
          repo_root: repoRoot,
          mode: 'node-pty-interactive-copilot',
          wrapper_pid: process.pid,
          copilot_command: command,
          log_path: logPath(),
          transcript_path: sessionTranscriptPath,
          input_logging_enabled: Boolean(options.logInput),
          input_transcript_path: options.logInput ? sessionInputTranscriptPath : null,
          input_queue_dir: sessionInputQueueDir,
          input_queue_status: queueSnapshot(sessionInputQueueDir),
          user_input_required: userInputRequest.required,
          user_input_reason: userInputRequest.reason,
          last_output_tail: plainOutput.slice(-4000),
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
          note: 'node-pty owns stdin/stdout and mirrors output to this terminal. Type here to send input to Copilot.',
          ...extra,
        },
        null,
        2,
      ),
      'utf8',
    );
  }

  fs.writeFileSync(sessionTranscriptPath, '', 'utf8');
  if (options.logInput) {
    fs.writeFileSync(sessionInputTranscriptPath, '', 'utf8');
  }
  fs.writeFileSync(
    sessionStatePath,
    JSON.stringify(
      {
        status: 'running',
        started_at: startedAt,
        updated_at: utcStamp(),
        repo_root: repoRoot,
        mode: 'node-pty-interactive-copilot',
        wrapper_pid: process.pid,
        copilot_command: command,
        log_path: logPath(),
        transcript_path: sessionTranscriptPath,
        input_logging_enabled: Boolean(options.logInput),
        input_transcript_path: options.logInput ? sessionInputTranscriptPath : null,
        input_queue_dir: sessionInputQueueDir,
        input_queue_status: queueSnapshot(sessionInputQueueDir),
        user_input_required: false,
        user_input_reason: null,
        last_output_tail: '',
        last_output_chunk_at: null,
        last_output_chunk_bytes: 0,
        last_output_sequence: 0,
        last_output_transcript_size: 0,
        last_input_client_sent_at: null,
        last_input_backend_queued_at: null,
        last_input_host_runner_received_at: null,
        last_input_host_runner_queued_at: null,
        last_input_queue_file_seen_at: null,
        last_input_pty_write_at: null,
        last_input_trace_id: null,
        last_input_job_id: null,
        last_input_tail: options.logInput ? '' : null,
        last_injected_text: '',
        note: 'node-pty owns stdin/stdout and mirrors output to this terminal. Type here to send input to Copilot.',
      },
      null,
      2,
    ),
    'utf8',
  );
  logEvent('node_pty_interactive_started', {
    command,
    state_path: sessionStatePath,
    transcript_path: sessionTranscriptPath,
    input_logging_enabled: Boolean(options.logInput),
    input_transcript_path: options.logInput ? sessionInputTranscriptPath : null,
    input_queue_dir: sessionInputQueueDir,
  });

  process.stdout.write('Copilot node-pty wrapper started. Type in this window to interact with Copilot. Press Ctrl+C to end.\r\n\r\n');
  process.stdout.write(`External input queue: ${sessionInputQueueDir}\r\n\r\n`);
  if (options.logInput) {
    process.stdout.write('Diagnostic input logging is ENABLED. Type only non-sensitive test text in this window.\r\n\r\n');
  }

  if (process.stdin.isTTY) {
    process.stdin.setRawMode(true);
  }
  process.stdin.resume();
  process.stdin.on('data', (data) => {
    if (data.length === 1 && data[0] === 0x03) {
      writeSessionState({ status: 'stopping', stopped_by: 'ctrl_c' });
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
    plainOutput += stripAnsi(data);
    fs.appendFileSync(sessionTranscriptPath, stripAnsi(data), 'utf8');
    lastOutputChunkAt = utcStamp();
    lastOutputChunkBytes = Buffer.byteLength(data, 'utf8');
    lastOutputSequence += 1;
    lastOutputTranscriptSize = Buffer.byteLength(plainOutput, 'utf8');
    writeSessionState();
    process.stdout.write(data);
  });
  term.onExit((event) => {
    writeSessionState({ status: 'exited', exit_code: event.exitCode, signal: event.signal });
    logEvent('node_pty_interactive_exited', event);
    process.exit(event.exitCode ?? 0);
  });

  const queueTimer = setInterval(() => {
    try {
      const files = fs.readdirSync(sessionInputQueueDir)
        .filter((name) => name.endsWith('.json'))
        .sort();
      for (const fileName of files) {
        const filePath = path.join(sessionInputQueueDir, fileName);
        let request;
        try {
          request = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        } catch (error) {
          logEvent('node_pty_interactive_injection_invalid', { file_path: filePath, message: error.message });
          fs.renameSync(filePath, `${filePath}.invalid`);
          continue;
        }

        const text = String(request.text ?? '');
        const submit = request.submit !== false;
        const clearLine = request.clear_line === true;
        const queueFileSeenAt = utcStamp();
        if (!text) {
          logEvent('node_pty_interactive_injection_skipped', { file_path: filePath, reason: 'empty_text' });
          fs.renameSync(filePath, `${filePath}.skipped`);
          continue;
        }

        if (clearLine && !text.startsWith('\x15')) {
          term.write('\x15');
        }
        const payload = submit ? `${text}\r` : text;
        term.write(payload);
        const ptyWriteAt = utcStamp();
        lastInjectedText = String(request.display_text ?? text);
        lastInputClientSentAt = request.client_sent_at ?? null;
        lastInputBackendAcceptedAt = request.backend_accepted_at ?? request.backend_queued_at ?? request.queued_at ?? null;
        lastInputHostRunnerReceivedAt = request.host_runner_received_at ?? null;
        lastInputHostRunnerQueuedAt = request.host_runner_queued_at ?? null;
        lastInputQueueFileSeenAt = queueFileSeenAt;
        lastInputPtyWriteAt = ptyWriteAt;
        lastInputTraceId = request.trace_id ?? null;
        lastInputJobId = request.job_id ?? null;
        writeSessionState({
          last_injected_at: ptyWriteAt,
          last_injected_submit: submit,
          last_injected_clear_line: clearLine,
        });
        logEvent('node_pty_interactive_injection_sent', {
          file_path: filePath,
          byte_count: Buffer.byteLength(payload),
          submit,
          clear_line: clearLine,
          client_sent_at: request.client_sent_at ?? null,
          backend_accepted_at: request.backend_accepted_at ?? request.backend_queued_at ?? request.queued_at ?? null,
          host_runner_received_at: request.host_runner_received_at ?? null,
          host_runner_queued_at: request.host_runner_queued_at ?? null,
          queue_file_seen_at: queueFileSeenAt,
          pty_write_at: ptyWriteAt,
          trace_id: request.trace_id ?? null,
          job_id: request.job_id ?? null,
          text,
        });
        fs.renameSync(filePath, `${filePath}.done`);
      }
    } catch (error) {
      logEvent('node_pty_interactive_injection_error', { message: error.message, stack: error.stack });
    }
  }, 50);
  queueTimer.unref();

  const startupTimer = setInterval(() => {
    const recentOutput = plainOutput.slice(-4000);
    const userInputRequest = detectUserInputRequest(recentOutput);
    if (userInputRequest.reason === 'directory_trust_prompt') {
      if (!trustAcceptanceSubmitted) {
        trustAcceptanceSubmitted = true;
        term.write('\r');
        lastInjectedText = '<ENTER>';
        writeSessionState({
          directory_trust_requested: true,
          directory_trust_verified: false,
          startup_trust_action: 'accepted_session_default_enter',
          startup_policy_state: 'directory_trust_submitted',
          last_injected_at: utcStamp(),
          last_injected_submit: true,
        });
        logEvent('node_pty_startup_trust_submitted', { mode: 'session_default_enter' });
      }
      return;
    }
    if (trustAcceptanceSubmitted && !trustAccepted) {
      trustAccepted = true;
      writeSessionState({
        directory_trust_requested: true,
        directory_trust_verified: true,
        directory_trust_observed_at: utcStamp(),
        startup_policy_state: 'directory_trust_accepted',
      });
      logEvent('node_pty_startup_trust_accepted', { mode: 'session_default_enter' });
    }
    if (startupCommandsSent || userInputRequest.required) {
      return;
    }
    const startupCommands = [];
    if (options.startupModel) {
      startupCommands.push(`/model ${options.startupModel}`);
    }
    if (options.allowAll) {
      startupCommands.push('/allow-all');
    }
    if (startupCommands.length === 0) {
      startupCommandsSent = true;
      return;
    }
    for (const commandText of startupCommands) {
      term.write(`${commandText}\r`);
      lastInjectedText = commandText;
      logEvent('node_pty_startup_command_sent', {
        command: commandText.startsWith('/model ') ? '/model <configured>' : commandText,
      });
    }
    startupCommandsSent = true;
    writeSessionState({
      startup_model_requested: options.startupModel ?? null,
      startup_model: options.startupModel ?? null,
      startup_allow_all_requested: Boolean(options.allowAll),
      startup_allow_all: Boolean(options.allowAll),
      startup_commands_sent: true,
      allow_all_verified: Boolean(options.allowAll),
      permissions_hint: options.allowAll ? 'allow-all' : null,
      permissions_observed_at: options.allowAll ? utcStamp() : null,
      model_verified: false,
      current_model: null,
      startup_policy_state: options.allowAll ? 'allow_all_sent' : 'startup_commands_sent',
      last_injected_at: utcStamp(),
      last_injected_submit: true,
    });
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
