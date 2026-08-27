# Copilot-admin E2E critical coverage analysis

## Scope and validation level

This analysis covers the E2E ownership for the Copilot-admin control plane. The current development E2E suites are `tools\source\copilot_admin_control_plane\e2e\test_control_plane_dev_e2e.py` and `tools\source\copilot_admin_control_plane\e2e\test_frontend_browser_e2e.py`, both runnable through `runtime\docker\copilot-admin\test-e2e-dev.ps1`.

The development suite runs against the real Python backend, the real repository regression catalog, the real Mermaid source, real report files, the real frontend static files, real backend JSONL logs, a browser DOM harness, and injected safe host state. It must not dispatch to the user's live Copilot session. Full real integration is covered by `runtime\docker\copilot-admin\test-real-visible-e2e.ps1`, which starts backend and host-runner API on isolated ports and uses a separate runner state directory for its Copilot input queue, transcript and state.

Real Copilot E2E must use an isolated hidden Copilot engine session, not the production/user Copilot session. The isolated runner state directory is under `tmp\copilot_admin_control_plane\real_visible_e2e\runner_state`, and the test browser uses its own debug port by default. This keeps the tests meaningful while preventing test prompts from being injected into the user's active production session.

## Release evidence 2026-08-27

| Evidence | Result |
| --- | --- |
| Backend unit/API suite | Passed, 10 tests including Copilot console input and cursor-based transcript polling. |
| Development E2E | Passed, 4 backend/control-plane tests plus 1 browser DOM-harness test through `test-e2e-dev.ps1`. |
| Frontend static validation | Passed. |
| Frontend Copilot console | Passed in browser E2E: user input is entered in frontend, queued to the same node-pty session, and transcript/status/user-input-required state is shown without using the raw CLI as input surface. |
| Copilot engine visibility control | Passed in browser E2E: the engine window is visible by default, and the frontend toggle sends `hidden_window=true` only when the user chooses hidden mode before session start. |
| Real isolated control-plane E2E | Uses an isolated hidden Copilot engine session and separate runner state directory; the strict console check verifies `/api/copilot/input` through host-runner and the exact node-pty input file `.done` marker. |
| Copilot startup policy | Applied to the active session: `/model gpt-5-mini` changed the session model and `/allow-all` enabled all permissions. |
| Browser singleton | Verified through debug-port reuse on port `9222`; real-E2E did not start a second browser when the existing session was running. |
| Regression B | Passed in Regression Mode and produced `test_reports\20260827v1`. |
| Regression G | Verified failed in Regression Mode after B; report created at `test_reports\20260827v1\RegressionError01\report.md`. |

## User story coverage

| User story | Test coverage | Validation level |
| --- | --- | --- |
| Start the admin tool. | `test_startup_api_and_frontend_static_contract` verifies backend health and session-start API; `runtime\docker\copilot-admin\start-backend.ps1` is the documented startup command. | Real backend integration plus static frontend contract. |
| Automatically start a shared visible Copilot window/session. | `test_startup_api_and_frontend_static_contract` injects a running node-pty state and verifies `/api/session/start` creates an asynchronous session job dispatched to the input queue. `runtime\test-copilot-admin-host-runner-status-input.ps1` verifies safe Copilot status and dry-run input queue behavior. `runtime\test-copilot-admin-host-runner-real-copilot.ps1` starts, observes and stops a real visible node-pty Copilot window for manual smoke validation. `runtime\docker\copilot-admin\test-real-visible-e2e.ps1` verifies full backend/runner integration through a hidden isolated test Copilot session. | Real backend integration, host-runner dry-run, real visible smoke and full real isolated E2E. |
| Work with Copilot without typing in the unstable raw CLI window. | `GET /api/copilot/console` exposes status, heartbeat, input queue and cursor-based transcript deltas. `POST /api/copilot/input` queues direct console input asynchronously. `test_copilot_console_contract_input_and_logs` verifies backend behavior and log correlation; `test_frontend_in_real_browser` verifies the two-panel frontend console. | Real backend integration plus browser DOM-harness E2E; real visible E2E includes console input observation. |
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
| Can a long-running Copilot session be observed without repeatedly re-reading the whole transcript? | Yes. The console API supports `cursor` and `limit`, returns transcript `next_cursor`, size and heartbeat metadata, and backend tests verify tail-then-delta polling. Frontend keeps a bounded local transcript buffer. |
| Is the Windows input queue JSON safe for node-pty over long runs? | Yes. The queue writer uses UTF-8 without BOM because Node `JSON.parse` rejected PowerShell's BOM-prefixed UTF-8 files during strict real-E2E. |

## Remaining product blocker

The control-plane implementation is usable, but the SPS business regression `G` is currently a verified product defect rather than a control-plane gap. Checkout still reproduces `SEK NaN`, an empty notification-method dropdown, missing clear setup/service fee presentation and failure to create a contract; the developer-facing report is `test_reports\20260827v1\RegressionError01\report.md`.

## Test isolation and real-window correction

### Non-negotiable rule for future agents

Do **not** run automated validation against the user's production Copilot engine session. The production session is the one used by `start_tool.ps1` and stored under `tmp\copilot_admin_runner_state`.

Automated tests have exactly two valid modes:

1. **Mock/injected mode**: backend, frontend and dev-E2E tests use injected host state and test queues under `tmp\copilot_admin_control_plane`.
2. **Real isolated mode**: full real-E2E starts or uses a hidden test Copilot engine with `COPILOT_ADMIN_RUNNER_STATE_DIR=tmp\copilot_admin_control_plane\real_visible_e2e\runner_state`.

An automated test must fail rather than silently fall back to `tmp\copilot_admin_runner_state`. Any test result is invalid if test prompts appear in `tmp\copilot_admin_runner_state\node-pty-copilot-input-queue`.

The guard for this rule is `runtime\test-copilot-admin-test-isolation.ps1`. It runs the backend and dev/browser-E2E suites while checking that no new files are created in the production Copilot input queue, and verifies that full real-E2E dry-run declares a hidden isolated Copilot session.

Development tests and browser DOM-harness tests must be safe and deterministic. They use injected host state and test queues under `tmp\copilot_admin_control_plane`; they must not read or write `tmp\copilot_admin_runner_state`, because that is the live production runner state used by the user's admin session.

Full real E2E must not reuse the production Copilot session. It must start or reuse only the isolated test runner state directory configured through `COPILOT_ADMIN_RUNNER_STATE_DIR`, with `hidden_window=true`, so the user's visible Copilot engine is not confused with test traffic.

Real visible E2E is only valid when it preserves one shared user/agent workspace. A rehearsal exposed that starting separate real smoke tests and a full real-E2E sequence can create multiple Copilot windows and multiple browser windows, then close the wrong user-visible context.

Corrected acceptance rules:

- preflight existing host-runner-owned Copilot and browser state before starting anything
- reuse a running Copilot session unless a controlled restart is explicitly requested
- reuse the first collaborative browser window and open additional work in tabs through the existing debug port
- never run separate real-smoke startup and full real-E2E startup in the same sequence if they target the same visible session
- apply Copilot startup policy once per new session: `gpt-5-mini`, `/allow-all`, and session-only folder trust approval when prompted

Any future "passed" result for full real visible E2E is invalid unless it proves this singleton behavior.
