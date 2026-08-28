# AI console latency, layout and startup-policy plan

## Goal

The Copilot-admin console must control a real node-pty-owned Copilot CLI session without mixing production and test traffic. It must automatically prepare a controlled session for work, render the same meaningful terminal state as the Copilot CLI window, and meet strict latency guarantees:

- Copilot output must reach AI-konsolen within 200 ms through the owned transcript/event path.
- AI-console input must be accepted and handed to host-runner or the isolated node-pty queue within 500 ms.
- Green UI badges mean verified active state, never merely requested configuration.

## Fleet workstream A: startup policy and verified state

Owned files:

- `tools\source\copilot_admin_runner\node_pty_poc\node_pty_poc.mjs`
- `tools\source\copilot_admin_runner\copilot_admin_runner.py`
- `runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-window.ps1`
- `tools\source\copilot_admin_control_plane\backend\app.py`
- backend/unit tests

Tasks:

1. Keep startup policy explicit in runner state: requested fields and verified fields must be separate.
2. Automatically answer current-directory/session trust prompts when Copilot asks for workspace trust.
3. Automatically send `/allow-all` once the session is ready for commands.
4. Do not send startup policy commands while Copilot is in Microsoft login, auth, or another user-critical prompt.
5. Keep model badges unverified unless the active Copilot session confirms the current model.

Acceptance:

- `Permissions: allow-all` turns green only from runner/backend state showing the command was applied/sent for that session.
- Directory trust is recorded as verified only after the wrapper handled the prompt.
- `Modell` stays yellow/gray when only a configured startup model is known.

## Fleet workstream B: low-latency transport

Owned files:

- `tools\source\copilot_admin_runner\node_pty_poc\node_pty_poc.mjs`
- `tools\source\copilot_admin_runner\copilot_admin_runner.py`
- `tools\source\copilot_admin_control_plane\backend\app.py`
- `tools\source\copilot_admin_control_plane\frontend\app.js`
- latency regression tests

Tasks:

1. Use Server-Sent Events from `/api/ai-console/events` as the primary AI-console output transport.
2. Keep cursor-based transcript recovery for reconnects and long runs.
3. Keep node-pty input queue polling fast enough for the 500 ms requirement; current protected value is 50 ms.
4. Preserve timestamp fields across frontend, backend, queue, and PTY injection for real-path diagnostics.

Acceptance:

- Backend latency regression fails if an isolated transcript delta takes 200 ms or more to appear on the SSE stream.
- Dev E2E fails if AI-console input enqueue takes 500 ms or more.
- Frontend static validation fails if EventSource integration is removed.

## Fleet workstream C: layout parity and terminal cleanup

Owned files:

- `tools\source\copilot_admin_control_plane\frontend\app.js`
- `tools\source\copilot_admin_control_plane\frontend\styles.css`
- `tools\source\copilot_admin_control_plane\e2e\test_frontend_browser_e2e.py`

Tasks:

1. Match the visible Copilot CLI window's meaningful layout: prompt cards, selected options, navigation hints, command blocks and text flow.
2. Filter timer, spinner, backspace and box-drawing redraw artifacts without deleting real Copilot content.
3. Render selected options for any option number, not only option 1.
4. Avoid artificial truncation; if the PTY stream itself is truncated, label it clearly.

Acceptance:

- Browser E2E verifies no raw backspace or TUI box characters are shown.
- Browser E2E verifies timer artifacts are suppressed and meaningful adjacent content remains.
- Approval prompts and selected options render as stable semantic blocks.

## Fleet workstream D: documentation, regression and integration

Owned files:

- `tools\docs\copilot-admin-e2e-critical-coverage.md`
- `dokument_index\index.md`
- `runtime\test-copilot-admin-test-isolation.ps1`
- `runtime\docker\copilot-admin\test-e2e-dev.ps1`

Tasks:

1. Document the 200 ms output and 500 ms input requirements.
2. Document startup-policy automation and verified badge semantics.
3. Keep test isolation non-negotiable: dev/browser/backend tests use injected state; real E2E uses hidden isolated runner state.
4. Run integration validation after all workstreams merge.

Acceptance:

- Documentation is reachable from `dokument_index\index.md`.
- `runtime\test-copilot-admin-test-isolation.ps1` fails if tests write to the production Copilot input queue.
- Final integration passes backend unit tests, frontend static validation, browser E2E, dev E2E, isolation guard and document-index validation.
