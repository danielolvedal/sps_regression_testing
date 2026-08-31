# Runtime-struktur

`runtime` innehåller körbara entrypoints. Roten ska hållas liten och användarvänlig.

## Princip

| Plats | Syfte |
| --- | --- |
| `runtime\*.ps1` | Stabila root-wrappers för vanliga kommandon. |
| `runtime\windows\...` | Windows-specifika entrypoints och POC-skript. |
| `runtime\docker\...` | Docker-/control-plane-entrypoints. |


Docker-specific Copilot-admin entrypoints live under:

```text
runtime\docker\copilot-admin\
```

| Plats | Syfte |
| --- | --- |
| `runtime\docker\copilot-admin\start-backend.ps1` | Starts the local Python UI/API backend for the Copilot-admin control plane and serves the frontend. |
| `runtime\docker\copilot-admin\build-backend-image.ps1` | Builds the UI/API Docker image and prints a repository-mounted run command. |

Common root wrappers:

| Plats | Syfte |
| --- | --- |
| `runtime\install_tool.ps1` | Kor pre-flight och installerar saknade beroenden sa att `start_tool.ps1` kan starta Copilot-admin-flodet. |
| `runtime\start-collaborative-copilot-admin-browser.ps1` | Startar den synliga användar-/agentsessionen för Copilot-admins localhost-UI på separat debug-port. |

Common host-runner smoke wrappers:

| Plats | Syfte |
| --- | --- |
| `runtime\test-copilot-admin-host-runner-status-input.ps1` | Verifierar host-runnerns Copilot-status och torrkörda inputkö. |
| `runtime\test-copilot-admin-host-runner-browser-start.ps1` | Verifierar host-runnerns browserstatus och torrkörda browser-startkontrakt. |
| `runtime\test-copilot-admin-host-runner-real-copilot.ps1` | Startar, observerar och stoppar en verklig synlig node-pty-ägd Copilot-session för smoke-verifiering. |
| `runtime\test-copilot-admin-host-runner-real-browser.ps1` | Startar, observerar och stoppar en verklig synlig collaborative-browser-session på isolerad smoke-port. |

## Copilot-admin

Copilot-admins Windows-specifika entrypoints ligger under:

```text
runtime\windows\copilot-admin\
```

Undermappar:

| Plats | Syfte |
| --- | --- |
| `bridge` | HTTP, filkö, named pipe och status/graf-kommandon. |
| `terminal` | Fönsterbindning och Level 2-terminalinmatning. |
| `pty` | Python/ConPTY och runner-startad Copilot-session. |
| `node-pty` | Node-pty-baserad PTY-POC. |

Root-wrappers får finnas kvar för de kommandon användaren förväntas köra ofta.
