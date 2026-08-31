# Copilot admin host-runner adapter

This document defines the small Windows host-runner contract that a Docker/backend control plane can call without owning Copilot CLI or the browser directly.

## Runtime wrapper

Primary wrapper:

```powershell
.\runtime\invoke-copilot-admin-host-runner.ps1 -Action status
```

Windows implementation:

```powershell
.\runtime\windows\copilot-admin\host-runner\invoke-copilot-admin-host-runner.ps1 -Action status
```

## Supported actions

| Action | Purpose | Non-destructive option |
| --- | --- | --- |
| `status` | Full host status including regression metadata, Copilot session, browser session and status diode. | Always read-only. |
| `copilot-status` | Poll node-pty Copilot state, transcript tail, queue status and `user_input_required`. | Always read-only. |
| `copilot-start` | Start a visible node-pty-owned Copilot window. | Use only in operator startup flows. |
| `copilot-stop` | Stop the active wrapper/window PIDs recorded in state. | Use explicit operator action or restart flow. |
| `copilot-input` | Queue PTY input for the active Copilot session. | `-DryRun` validates payload without writing SQLite queue rows. |
| `browser-status` | Poll the collaborative browser debug endpoint. | Always read-only. |
| `browser-start` | Start/reuse the visible collaborative browser using `runtime\start-collaborative-stage-browser.ps1`. | `-DryRun` returns the planned command without launching a browser. |
| `browser-stop` | Stop the owned collaborative browser process recorded in state and verify the debug endpoint goes down. | Refuses to kill an unknown browser when no owned `processId` is recorded. |
| `session-start` | Start/reuse both the node-pty Copilot window and collaborative browser for admin startup. | `-DryRun` returns planned state without launching either surface. |
| `session-stop` | Stop both the node-pty Copilot session and the owned collaborative browser. | Uses only recorded process IDs. |

## HTTP adapter endpoints

When `.\runtime\start-copilot-admin-runner.ps1` is running, the same contract is exposed over HTTP:

- `GET /status` or `GET /api/status`
- `GET /copilot/status` or `GET /session/copilot`
- `POST /copilot/start`
- `POST /copilot/stop`
- `POST /copilot/input`
- `GET /browser/status`
- `POST /browser/start`
- `POST /browser/stop`
- `POST /api/session/start` starts both Copilot and browser; pass `"dry_run": true` for a non-destructive contract check.
- `POST /api/session/stop` stops the host-owned Copilot/browser session.

POST bodies are JSON objects. Example:

```json
{
  "text": "kor regressionstest",
  "no_submit": false,
  "dry_run": true
}
```

## State, session registry and logs

Machine-readable node-pty state is written under `tmp\copilot_admin_runner_state` or another explicit runner-state directory such as the isolated real-E2E state. The same state directory now also contains `copilot-admin-transport.sqlite`, which stores the PTY input queue and time-stamped cross-layer trace events with transactional ordering. SPS-controlled Copilot start paths also register their project-owned process IDs and state directories in `tmp\copilot_admin_control_plane\project-controlled-copilot-sessions.json`, so `stop_tool.ps1` can stop only project-controlled sessions without touching unrelated user Copilot windows. JSONL logs are still written under `tmp\copilot_admin_runner_logs` for operator readability, while SQLite is the primary machine-readable source for queue state and latency correlation.

## Smoke tests

Safe smoke tests:

```powershell
.\runtime\test-copilot-admin-host-runner-status-input.ps1
.\runtime\test-copilot-admin-host-runner-browser-start.ps1
```

The input smoke test uses dry-run mode and does not write to the PTY queue. The browser smoke test uses dry-run mode and does not launch or close a browser.

Real visible smoke tests:

```powershell
.\runtime\test-copilot-admin-host-runner-real-copilot.ps1
.\runtime\test-copilot-admin-host-runner-real-browser.ps1
```

The real Copilot smoke wrapper starts a visible node-pty-owned Copilot window when none is running, verifies machine-readable state/transcript/log paths, then stops only the session it started. The real browser smoke wrapper uses port `9322` by default to avoid the normal collaborative port, verifies the debug endpoint and state file, then stops only the browser process recorded in state.
