# Copilot-admin E2E critical coverage analysis

## Scope and validation level

This analysis covers the E2E ownership for the Copilot-admin control plane. The current development E2E suites are `tools\source\copilot_admin_control_plane\e2e\test_control_plane_dev_e2e.py` and `tools\source\copilot_admin_control_plane\e2e\test_frontend_browser_e2e.py`, both runnable through `runtime\docker\copilot-admin\test-e2e-dev.ps1`.

The development suite runs against the real Python backend, the real repository regression catalog, the real Mermaid source, real report files, the real frontend static files, real backend JSONL logs, a browser DOM harness, and injected safe host state. It must not dispatch to the user's live Copilot session. Full real integration is covered by `runtime\docker\copilot-admin\test-real-visible-e2e.ps1`, which starts backend and host-runner API on isolated ports and uses a separate runner state directory for its Copilot input queue, transcript and state.

Real Copilot E2E must use an isolated hidden Copilot engine session, not the production/user Copilot session. The isolated runner state directory is under `tmp\copilot_admin_control_plane\real_visible_e2e\runner_state`, and the automated test browser uses its own debug port by default (`9322`). This keeps the tests meaningful while preventing test prompts from being injected into the user's active production session or the visible manual frontend browser.

## Release evidence 2026-08-27

| Evidence | Result |
| --- | --- |
| Backend unit/API suite | Passed, including AI console input, cursor-based transcript polling, SSE output latency and verified startup-policy semantics. |
| Development E2E | Passed, 4 backend/control-plane tests plus 1 browser DOM-harness test through `test-e2e-dev.ps1`. |
| Frontend static validation | Passed. |
| Frontend AI console | Passed in browser E2E: user input is entered in frontend, queued to the same node-pty session, and transcript/status/user-input-required state is shown without using the raw CLI as input surface. |
| Copilot engine visibility control | Passed in browser E2E: the engine window is visible by default, and the frontend toggle sends `hidden_window=true` only when the user chooses hidden mode before session start. |
| Real isolated control-plane E2E | Uses an isolated hidden Copilot engine session and separate runner state directory; the strict AI-console check verifies `/api/ai-console/input` through host-runner and the exact node-pty input file `.done` marker. |
| Copilot startup policy | The runner automatically requests session-only directory trust approval and `/permissions allow-all`; UI badges may turn green only from verified runner/backend state. Model state is explicitly unverified unless the active Copilot session confirms it. |
| Browser singleton | Verified through debug-port reuse on port `9222`; real-E2E did not start a second browser when the existing session was running. |
| Regression B | Passed in Regression Mode and produced `test_reports\20260827v1`. |
| Regression G | Verified failed in Regression Mode after B; report created at `test_reports\20260827v1\RegressionError01\report.md`. |

## User story coverage

| User story | Test coverage | Validation level |
| --- | --- | --- |
| Start the admin tool. | `test_startup_api_and_frontend_static_contract` verifies backend health and session-start API; `runtime\docker\copilot-admin\start-backend.ps1` is the documented startup command. | Real backend integration plus static frontend contract. |
| Automatically start a shared visible Copilot window/session. | `test_startup_api_and_frontend_static_contract` injects a running node-pty state and verifies `/api/session/start` creates an asynchronous session job dispatched to the input queue. `runtime\test-copilot-admin-host-runner-status-input.ps1` verifies safe Copilot status and dry-run input queue behavior. `runtime\test-copilot-admin-host-runner-real-copilot.ps1` starts, observes and stops a real visible node-pty Copilot window for manual smoke validation. `runtime\docker\copilot-admin\test-real-visible-e2e.ps1` verifies full backend/runner integration through a hidden isolated test Copilot session. | Real backend integration, host-runner dry-run, real visible smoke and full real isolated E2E. |
| Work with Copilot without typing in the unstable raw CLI window. | `GET /api/ai-console` exposes status, heartbeat, input queue and cursor-based transcript deltas. `POST /api/ai-console/input` queues direct AI-console input asynchronously. `test_ai_console_contract_input_and_logs` verifies backend behavior and log correlation; `test_frontend_in_real_browser` verifies the two-panel AI-konsolen. | Real backend integration plus browser DOM-harness E2E; real visible E2E includes AI-console input observation. |
| See Copilot output quickly in AI-konsolen. | `GET /api/ai-console/events` is the primary output channel. `test_ai_console_event_stream_delta_within_200ms` appends transcript data in an isolated test harness and fails if the SSE delta takes 200 ms or more. Frontend static validation requires `EventSource` integration so the UI cannot rely on 5 second polling as the primary AI-console output path. | Backend latency regression plus static frontend contract. |
| Send AI-console input quickly to Copilot. | `POST /api/ai-console/input` returns after enqueue/dispatch and records client/backend timestamps. `test_ai_console_contract_input_and_logs` fails if the backend enqueue path takes 500 ms or more; the node-pty wrapper polls the input queue every 50 ms and records queue-file and PTY-write timestamps for real-path verification. | Backend/control-plane latency regression with isolated node-pty queue instrumentation. |
| Choose whether the Copilot engine window should be visible. | The dashboard exposes `copilot-window-visible-toggle`. Browser E2E verifies visible-by-default behavior and hidden-mode payload propagation to `/api/session/start`. Backend tests verify `hidden_window` is forwarded to host-runner. | Browser DOM-harness E2E plus backend fake-runner integration. |
| Automatically start a shared visible browser window. | Injected browser state verifies backend/UI contract with debug port; `runtime\test-copilot-admin-host-runner-browser-start.ps1` verifies browser-status and dry-run collaborative-browser start path. `runtime\test-copilot-admin-host-runner-real-browser.ps1` starts, observes and stops a real visible collaborative browser on an isolated smoke port. `runtime\docker\copilot-admin\test-real-visible-e2e.ps1` verifies reuse of the existing collaborative browser. | Real backend integration, host-runner dry-run, real visible smoke and full real visible E2E. |
| See all regression tests and their Mermaid relationships. | `test_mermaid_reports_user_input_required_and_log_correlation` reads real `testing\regression_test\regression-test-catalog.md` and real `regression-test-dependencies.mmd`. | Real backend/repository integration. |
| Zoom, scroll and pan in a large Mermaid diagram. | Frontend static validation verifies controls and event hooks; `test_frontend_browser_e2e.py` drives the real frontend DOM through Chrome/Edge CDP and verifies Mermaid zoom, pan, scroll, fit/reset and search behavior. | Browser DOM-harness E2E plus static contract. |
| Set Copilot to learning or testing mode from frontend. | `test_status_diode_job_lifecycle_and_mode_switching` creates real backend async mode jobs for both modes and verifies persisted mode in `/api/status`. | Real backend integration with injected host state. |
| Run regression testing from frontend. | `test_status_diode_job_lifecycle_and_mode_switching` creates a selected regression job, verifies immediate return, queue dispatch and yellow diode. | Real backend integration with injected host state. |
| Choose and read a report in formatted frontend. | `test_mermaid_reports_user_input_required_and_log_correlation` reads real report list and selected Markdown report; frontend static contract verifies report reader hook. | Real backend/repository integration plus static frontend contract. |

## Critical E2E questions

| Question | Current answer |
| --- | --- |
| Do tests cover every user story? | Yes, every first-version user story has at least static or mocked/backend integration coverage. |
| Is at least one test run against a real node-pty Copilot session? | Yes. Manual smoke can use `runtime\test-copilot-admin-host-runner-real-copilot.ps1`; full control-plane E2E uses `runtime\docker\copilot-admin\test-real-visible-e2e.ps1` with a hidden isolated test Copilot session. |
| Is at least one test run against a real collaborative browser? | Yes, via `runtime\test-copilot-admin-host-runner-real-browser.ps1` when Edge or Chrome is available. |
| Are any user stories only mocked? | No first-version user story is only mocked. Full business success for G is blocked by a verified SPS checkout defect, not by missing control-plane coverage. |
| Do logs show frontend activity? | Yes. E2E posts frontend events and verifies JSONL log correlation. |
| Can frontend, backend and runner be correlated with the same ID? | Backend/frontend correlation is verified by trace ID in JSONL; real host-runner and node-pty logs expose compatible `trace_id`/`job_id` fields and are exercised by real visible E2E. |
| Is Mermaid verified with a large diagram? | The real repository Mermaid source is verified and browser DOM-harness E2E verifies zoom/pan/scroll/fit/reset/search controls. |
| Is asynchronicity verified? | Yes. E2E asserts session/regression APIs return immediately and status diode moves through yellow/green/red lifecycle states. |
| Are latency requirements verified? | Yes. AI-console output must reach the SSE event stream within 200 ms in the deterministic backend harness, and AI-console input must be accepted/enqueued within 500 ms in dev-E2E. Node-pty writes input queue files to PTY on a 50 ms poll cycle and stores injection timestamps for real E2E analysis. |
| Can a long-running Copilot session be observed without repeatedly re-reading the whole transcript? | Yes. The console API supports `cursor` and `limit`, returns transcript `next_cursor`, size and heartbeat metadata, and backend tests verify tail-then-delta polling. Frontend keeps a bounded local transcript buffer. |
| Is the Windows input queue JSON safe for node-pty over long runs? | Yes. The queue writer uses UTF-8 without BOM because Node `JSON.parse` rejected PowerShell's BOM-prefixed UTF-8 files during strict real-E2E. |

## Remaining product blocker

The control-plane implementation is usable, but the SPS business regression `G` is currently a verified product defect rather than a control-plane gap. Checkout still reproduces `SEK NaN`, an empty notification-method dropdown, missing clear setup/service fee presentation and failure to create a contract; the developer-facing report is `test_reports\20260827v1\RegressionError01\report.md`.

## Test isolation and real-window correction

### Non-negotiable rule for future agents

Do **not** run automated validation against the user's production Copilot engine session. The production session is the one the user starts or reuses through the normal admin flow against `tmp\copilot_admin_runner_state`, whether it is launched on demand from the AI-console or explicitly via `start_tool.ps1 -StartCopilotSession`.

Automated tests have exactly two valid modes:

1. **Mock/injected mode**: backend, frontend and dev-E2E tests use injected host state and test queues under `tmp\copilot_admin_control_plane`.
2. **Real isolated mode**: full real-E2E starts or uses a hidden test Copilot engine with `COPILOT_ADMIN_RUNNER_STATE_DIR=tmp\copilot_admin_control_plane\real_visible_e2e\runner_state`.

An automated test must fail rather than silently fall back to `tmp\copilot_admin_runner_state`. Any test result is invalid if test prompts appear in `tmp\copilot_admin_runner_state\node-pty-copilot-input-queue`.

The guard for this rule is `runtime\test-copilot-admin-test-isolation.ps1`. It runs the backend and dev/browser-E2E suites while checking that no new files are created in the production Copilot input queue, and verifies that full real-E2E dry-run declares a hidden isolated Copilot helper plus a separate collaborative browser flow.

Development tests and browser DOM-harness tests must be safe and deterministic. They use injected host state and test queues under `tmp\copilot_admin_control_plane`; they must not read or write `tmp\copilot_admin_runner_state`, because that is the live production runner state used by the user's admin session.

Full real E2E must not reuse the production Copilot session. It must start or reuse only the isolated test runner state directory configured through `COPILOT_ADMIN_RUNNER_STATE_DIR`, with `hidden_window=true`, so the user's visible Copilot engine is not confused with test traffic.

Manual frontend work against Copilot-admin localhost is a third mode and must use the dedicated visible browser script `runtime\start-collaborative-copilot-admin-browser.ps1`, normally on debug port `9223`. Automated real-E2E must not treat that browser as its own singleton.

Real visible E2E is only valid when it preserves one shared user/agent workspace. A rehearsal exposed that starting separate real smoke tests and a full real-E2E sequence can create multiple Copilot windows and multiple browser windows, then close the wrong user-visible context.

Corrected acceptance rules:

- preflight existing host-runner-owned Copilot and browser state before starting anything
- reuse a running Copilot session unless a controlled restart is explicitly requested
- reuse the first collaborative browser window and open additional work in tabs through the existing debug port
- never run separate real-smoke startup and full real-E2E startup in the same sequence if they target the same visible session
- apply Copilot startup policy once per new session: `/permissions allow-all` and session-only folder trust approval when prompted; model badges must stay unverified unless the current model is actually observed from the session

Any future "passed" result for full real visible E2E is invalid unless it proves this singleton behavior.

## AI-console latency and badge requirements

Green means verified. Yellow means requested, pending or unknown. Red/gray means missing, disconnected or unavailable. The frontend must not show `Status`, `Motor`, `Modell` or `Permissions` as green from configuration intent alone.

Hard latency requirements:

- Copilot output produced by the owned node-pty/transcript path must be visible through the frontend's primary console stream within 200 ms.
- Input submitted from AI-konsolen must be accepted by backend and handed to host-runner or the isolated node-pty queue within 500 ms.
- AI-konsolen output must use SSE (`/api/ai-console/events`) as the primary live transport. Periodic polling may remain only as status/recovery fallback.
- The node-pty input queue poll interval must remain fast enough for the 500 ms path; the current regression-protected value is 50 ms.

Startup-policy requirements:

- If Copilot prompts for current-directory/session trust, the runner may automatically approve that current working directory for the active session. It must not silently grant permanent/global trust.
- `/permissions allow-all` must be requested automatically for a new controlled session, but the UI may show `Permissions: allow-all` as green only when runner/backend state says it was actually applied/sent for that session.
- Model state must remain `ej verifierad` unless the active Copilot session itself confirms the current model. A configured startup model, including `gpt-5-mini`, is only a request and must not turn the model badge green.
