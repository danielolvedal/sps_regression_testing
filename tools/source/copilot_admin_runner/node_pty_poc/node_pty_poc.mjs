import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import pty from 'node-pty';

const scriptDir = path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1');
const repoRoot = path.resolve(scriptDir, '..', '..', '..', '..');
const logDir = path.join(repoRoot, 'tmp', 'copilot_admin_runner_logs');
const stateDir = path.join(repoRoot, 'tmp', 'copilot_admin_runner_state');

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
    event_id: crypto.randomUUID(),
    event,
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

function spawnPty(command, args, options = {}) {
  const cols = options.cols ?? 120;
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
  let plainOutput = '';
  let inputText = '';
  let lastInjectedText = '';

  fs.mkdirSync(sessionInputQueueDir, { recursive: true });

  function writeSessionState(extra = {}) {
    const recentOutput = plainOutput.slice(-1200);
    const userInputRequest = detectUserInputRequest(recentOutput);
    fs.writeFileSync(
      sessionStatePath,
      JSON.stringify(
        {
          status: 'running',
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
          user_input_required: userInputRequest.required,
          user_input_reason: userInputRequest.reason,
          last_output_tail: plainOutput.slice(-4000),
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
        started_at: utcStamp(),
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
        user_input_required: false,
        user_input_reason: null,
        last_output_tail: '',
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
        if (!text) {
          logEvent('node_pty_interactive_injection_skipped', { file_path: filePath, reason: 'empty_text' });
          fs.renameSync(filePath, `${filePath}.skipped`);
          continue;
        }

        const payload = submit ? `${text}\r` : text;
        term.write(payload);
        lastInjectedText = text;
        writeSessionState({ last_injected_at: utcStamp(), last_injected_submit: submit });
        logEvent('node_pty_interactive_injection_sent', {
          file_path: filePath,
          byte_count: Buffer.byteLength(payload),
          submit,
          text,
        });
        fs.renameSync(filePath, `${filePath}.done`);
      }
    } catch (error) {
      logEvent('node_pty_interactive_injection_error', { message: error.message, stack: error.stack });
    }
  }, 250);
  queueTimer.unref();
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
    await runInteractiveCopilot({ logInput: rest.includes('--log-input') });
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}

main().catch((error) => {
  logEvent('node_pty_error', { message: error.message, stack: error.stack });
  console.error(error);
  process.exitCode = 1;
});
