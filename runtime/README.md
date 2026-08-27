# Runtime-struktur

`runtime` innehåller körbara entrypoints. Roten ska hållas liten och användarvänlig.

## Princip

| Plats | Syfte |
| --- | --- |
| `runtime\*.ps1` | Stabila root-wrappers för vanliga kommandon. |
| `runtime\windows\...` | Windows-specifika entrypoints och POC-skript. |
| `runtime\docker\...` | Framtida Docker-/control-plane-entrypoints. |

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
