import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright-core';

function nowIso() {
  return new Date().toISOString();
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function diffMs(start, end) {
  const startMs = Date.parse(start ?? '');
  const endMs = Date.parse(end ?? '');
  if (!Number.isFinite(startMs) || !Number.isFinite(endMs)) {
    return null;
  }
  return endMs - startMs;
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { raw: text };
  }
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${JSON.stringify(body)}`);
  }
  return body;
}

async function waitFor(label, producer, { timeoutMs = 30000, intervalMs = 100 } = {}) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    try {
      const value = await producer();
      if (value) {
        return value;
      }
    } catch (error) {
      lastError = error;
    }
    await sleep(intervalMs);
  }
  throw new Error(`Timed out waiting for ${label}.${lastError ? ` Last error: ${lastError.message}` : ''}`);
}

function findBrowserExecutable() {
  const candidates = [
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  throw new Error('Neither Edge nor Chrome is installed for Playwright real E2E.');
}

async function locatorTone(page, testId) {
  return page.getByTestId(testId).evaluate((node) => node.className);
}

async function collectBadgeSnapshot(page) {
  const ids = [
    'copilot-console-status',
    'copilot-window-mode',
    'copilot-console-permissions',
    'copilot-console-project',
    'copilot-console-ready',
  ];
  const result = {};
  for (const id of ids) {
    result[id] = {
      text: await page.getByTestId(id).textContent(),
      className: await locatorTone(page, id),
    };
  }
  return result;
}

async function main() {
  const backendUrl = process.env.COPILOT_ADMIN_REAL_E2E_BACKEND_URL || 'http://127.0.0.1:8877';
  const runnerStateDir = process.env.COPILOT_ADMIN_RUNNER_STATE_DIR;
  const artifactPath = process.env.COPILOT_ADMIN_REAL_E2E_ARTIFACT || path.join(runnerStateDir || '.', 'real-visible-e2e-artifact.json');
  const expectedProject = (process.env.COPILOT_ADMIN_EXPECTED_PROJECT || 'SPS').toLowerCase();
  if (!runnerStateDir) {
    throw new Error('COPILOT_ADMIN_RUNNER_STATE_DIR is required.');
  }

  const sessionStatePath = path.join(runnerStateDir, 'node-pty-copilot-session.json');
  const executablePath = process.env.COPILOT_ADMIN_PLAYWRIGHT_BROWSER || findBrowserExecutable();
  let browser;
  const result = {
    status: 'failed',
    started_at: nowIso(),
    backend_url: backendUrl,
    runner_state_dir: runnerStateDir,
    browser_executable: executablePath,
  };

  try {
    browser = await chromium.launch({
      executablePath,
      headless: false,
      args: ['--disable-gpu', '--no-first-run', '--no-default-browser-check'],
    });
    const context = await browser.newContext();
    const page = await context.newPage();
    let inputRequestBody = null;
    let inputRequestObservedAt = null;
    let inputResponseBody = null;
    let inputResponseObservedAt = null;

    page.on('request', (request) => {
      if (request.method() !== 'POST' || !request.url().endsWith('/api/copilot/input')) {
        return;
      }
      inputRequestObservedAt = nowIso();
      try {
        inputRequestBody = request.postDataJSON();
      } catch {
        inputRequestBody = { raw: request.postData() };
      }
    });
    page.on('response', async (response) => {
      if (response.request().method() !== 'POST' || !response.url().endsWith('/api/copilot/input')) {
        return;
      }
      inputResponseObservedAt = nowIso();
      try {
        inputResponseBody = await response.json();
      } catch {
        inputResponseBody = null;
      }
    });

    await page.goto(`${backendUrl}/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    result.session_start = await requestJson(`${backendUrl}/api/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Trace-Id': 'real-visible-playwright-e2e' },
      body: JSON.stringify({ hidden_window: false, restart_existing: false, skip_browser_start: true, startup_model: null }),
    });
    await page.getByTestId('nav-copilot').click();

    await waitFor('Copilot status badge', async () => {
      const text = await page.getByTestId('copilot-console-status').textContent();
      const className = await locatorTone(page, 'copilot-console-status');
      return String(text).toLowerCase().includes('running') && className.includes('semantic-green');
    }, { timeoutMs: 180000, intervalMs: 250 });
    await waitFor('visible engine badge', async () => {
      const text = await page.getByTestId('copilot-window-mode').textContent();
      const className = await locatorTone(page, 'copilot-window-mode');
      return String(text).toLowerCase().includes('synlig') && className.includes('semantic-green');
    }, { timeoutMs: 30000, intervalMs: 150 });
    await waitFor('permissions badge', async () => {
      const text = await page.getByTestId('copilot-console-permissions').textContent();
      const className = await locatorTone(page, 'copilot-console-permissions');
      return String(text).toLowerCase().includes('allow-all') && className.includes('semantic-green');
    }, { timeoutMs: 60000, intervalMs: 150 });
    await waitFor('project badge', async () => {
      const text = await page.getByTestId('copilot-console-project').textContent();
      const className = await locatorTone(page, 'copilot-console-project');
      return String(text).toLowerCase().includes(expectedProject) && className.includes('semantic-green');
    }, { timeoutMs: 30000, intervalMs: 150 });
    await waitFor('prompt readiness badge', async () => {
      const text = await page.getByTestId('copilot-console-ready').textContent();
      const className = await locatorTone(page, 'copilot-console-ready');
      return String(text).toLowerCase().includes('redo') && className.includes('semantic-green');
    }, { timeoutMs: 30000, intervalMs: 150 });

    const baselineConsole = await requestJson(`${backendUrl}/api/copilot/console?limit=2048`);
    const baselineRunner = readJson(sessionStatePath);
    const baselineRender = await page.evaluate(() => window.__copilotAdminLastConsoleRender || null);
    const promptToken = `real-latency-${Date.now().toString(36)}`;
    const promptText = `Svara exakt med texten latency-ok och inget annat. Spåra detta test med token ${promptToken}.`;

    await page.getByTestId('copilot-console-input').fill(promptText);
    const clickSentAt = nowIso();
    await page.getByTestId('copilot-console-send').click();
    try {
      await waitFor('frontend input request', () => inputRequestObservedAt ? inputRequestObservedAt : null, { timeoutMs: 1500, intervalMs: 50 });
    } catch {
      await page.evaluate(() => document.getElementById('copilot-console-form')?.requestSubmit());
    }

    const accepted = await waitFor('frontend input response', () => inputResponseBody && inputResponseBody.accepted ? inputResponseBody : null, { timeoutMs: 30000, intervalMs: 50 });
    const jobId = accepted.job_id;
    const runnerAfterInput = await waitFor('PTY input write', () => {
      const state = readJson(sessionStatePath);
      return state.last_input_job_id === jobId && state.last_input_pty_write_at ? state : null;
    }, { timeoutMs: 30000, intervalMs: 50 });

    const runnerAfterOutput = await waitFor('CLI output change', () => {
      const state = readJson(sessionStatePath);
      const baselineSequence = Number(baselineRunner.last_output_sequence || 0);
      const currentSequence = Number(state.last_output_sequence || 0);
      if (state.last_output_chunk_at && currentSequence > baselineSequence && Date.parse(state.last_output_chunk_at) >= Date.parse(runnerAfterInput.last_input_pty_write_at)) {
        return state;
      }
      return null;
    }, { timeoutMs: 120000, intervalMs: 50 });

    const rendered = await waitFor('frontend console render', async () => {
      const snapshot = await page.evaluate(() => window.__copilotAdminLastConsoleRender || null);
      if (!snapshot?.rendered_at || !snapshot?.streamed_at) {
        return null;
      }
      const baselineRenderedAt = baselineRender?.rendered_at ? Date.parse(baselineRender.rendered_at) : 0;
      const renderAt = Date.parse(snapshot.rendered_at);
      const outputAt = Date.parse(runnerAfterOutput.last_output_chunk_at);
      if (renderAt <= baselineRenderedAt || renderAt < outputAt) {
        return null;
      }
      if ((snapshot.transcript_cursor ?? 0) < (baselineConsole.heartbeat?.next_cursor ?? 0)) {
        return null;
      }
      return snapshot;
    }, { timeoutMs: 15000, intervalMs: 50 });

    const badges = await collectBadgeSnapshot(page);
    const timings = {
      click_to_request_observed_ms: diffMs(clickSentAt, inputRequestObservedAt),
      client_to_backend_accept_ms: diffMs(inputRequestBody?.client_sent_at, accepted.accepted_at),
      backend_accept_to_host_runner_receive_ms: diffMs(accepted.accepted_at, accepted.response?.input?.host_runner_received_at),
      host_runner_receive_to_queue_write_ms: diffMs(accepted.response?.input?.host_runner_received_at, accepted.response?.input?.host_runner_queued_at),
      queue_write_to_queue_pickup_ms: diffMs(accepted.response?.input?.host_runner_queued_at, runnerAfterInput.last_input_queue_file_seen_at),
      queue_pickup_to_pty_write_ms: diffMs(runnerAfterInput.last_input_queue_file_seen_at, runnerAfterInput.last_input_pty_write_at),
      input_end_to_end_ms: diffMs(inputRequestBody?.client_sent_at, runnerAfterInput.last_input_pty_write_at),
      cli_output_to_backend_stream_ms: diffMs(runnerAfterOutput.last_output_chunk_at, rendered.streamed_at),
      backend_stream_to_frontend_render_ms: diffMs(rendered.streamed_at, rendered.rendered_at),
      cli_output_to_frontend_ms: diffMs(runnerAfterOutput.last_output_chunk_at, rendered.rendered_at),
      request_response_ms: diffMs(inputRequestObservedAt, inputResponseObservedAt),
    };

    result.status = 'passed';
    result.completed_at = nowIso();
    result.prompt = {
      token: promptToken,
      text: promptText,
      client_sent_at: inputRequestBody?.client_sent_at || clickSentAt,
      job_id: jobId,
    };
    result.badges = badges;
    result.baseline = {
      console_cursor: baselineConsole.heartbeat?.next_cursor ?? null,
      last_output_sequence: baselineRunner.last_output_sequence ?? null,
      render: baselineRender,
    };
    result.input = {
      request_observed_at: inputRequestObservedAt,
      response_observed_at: inputResponseObservedAt,
      backend_response: accepted,
      runner_state: {
        last_input_queue_file_seen_at: runnerAfterInput.last_input_queue_file_seen_at,
        last_input_pty_write_at: runnerAfterInput.last_input_pty_write_at,
        last_input_trace_id: runnerAfterInput.last_input_trace_id,
      },
    };
    result.output = {
      runner_state: {
        last_output_chunk_at: runnerAfterOutput.last_output_chunk_at,
        last_output_sequence: runnerAfterOutput.last_output_sequence,
      },
      frontend_render: rendered,
    };
    result.timings_ms = timings;
    writeJson(artifactPath, result);

    if (timings.input_end_to_end_ms === null || timings.input_end_to_end_ms >= 500) {
      throw new Error(`Input latency requirement failed: ${timings.input_end_to_end_ms} ms.`);
    }
    if (timings.cli_output_to_frontend_ms === null || timings.cli_output_to_frontend_ms >= 200) {
      throw new Error(`Output latency requirement failed: ${timings.cli_output_to_frontend_ms} ms.`);
    }
  } catch (error) {
    result.status = 'failed';
    result.failed_at = nowIso();
    result.error = { message: error.message, stack: error.stack };
    writeJson(artifactPath, result);
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

main().then(() => {
  console.log(JSON.stringify({ status: 'passed' }));
}).catch((error) => {
  console.error(error.stack || error.message);
  process.exitCode = 1;
});
