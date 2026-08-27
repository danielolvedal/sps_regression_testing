# Copilot admin runner - POC för host-runner och bryggor

Detta dokument beskriver den första praktiska implementationen för att prova hur en framtida Docker-control-plane kan prata med en Windows-bunden host runner i SPS-repositoryt.

## Syfte

POC:n ska inte bevisa vilken brygga som är teoretiskt bäst. Den ska ge ett konkret sätt att testa vad som faktiskt fungerar i den lokala miljön med:

- PowerShell på Windows
- befintliga runtime-skript
- dokumentstyrda regressionstester
- delad synlig browser-session
- framtida Copilot-nära operatörsflöden

## Källkod

- `tools\source\copilot_admin_runner\copilot_admin_runner.py`

## Runtime-entrypoints

- `runtime\start-copilot-admin-runner.ps1`
- `runtime\show-regression-status.ps1`
- `runtime\render-regression-graph.ps1`
- `runtime\submit-copilot-admin-queue-job.ps1`
- `runtime\process-copilot-admin-queue-once.ps1`
- `runtime\invoke-copilot-admin-pipe-request.ps1`

## Vad POC:n kan idag

Host runnern kan:

- läsa regressionstestkatalogen
- läsa senaste körningsrapport under `test_reports`
- returnera Mermaid-källan för regressionsberoenden
- exponera standardiserade kommandomallar för Copilot-orienterade uppgifter
- prova tre olika bryggsätt:
  - lokalt HTTP-API
  - filkö / jobbkatalog
  - named pipe som terminalnära bryggspår

## Loggning

Alla bryggspår skriver strukturerade JSONL-händelser till:

```text
tmp\copilot_admin_runner_logs\runner-YYYYMMDD.jsonl
```

Loggen är temporär och ska inte indexeras. Den används för att kunna jämföra bryggorna efter praktiska tester.

Loggen innehåller bland annat:

- timestamp
- event-ID
- process-ID
- bridge-typ
- repository root
- mottagen action
- kommando-ID och catalog key när de finns
- sammanfattning av svar, till exempel rapport-ID, antal tester, command ID eller fel
- serverstart och serverstopp när processen fångar stoppet

Loggen ska inte användas för hemligheter eller fullständig siddata från browsern.

## Startup-policy för Copilot och browser

Den interaktiva `node-pty`-ägda Copilot-sessionen ska startas med explicit standardpolicy:

- modell: `gpt-5-mini`, som är valt som lågkostnadsstandard för kontrollplanet
- permissions: `/allow-all`, så regressionstest och verktygskörningar inte fastnar i onödiga permission-prompter
- folder trust: om Copilot visar `Confirm folder trust` ska wrappern välja `1. Yes` för aktuell session innan övriga startup-kommandon skickas

Policyn ska vara synlig i state/loggar och kunna överstyras med parametrar, men standarden ska vara att control-plane-starten inte lämnar modell eller permissions åt slumpen.

Browser-sessionen ska också behandlas som en singleton. Eftersom varje nytt InPrivate-/Incognito-fönster kan kräva ny Microsoft-inloggning ska host runnern i första hand återanvända den första collaborative browser-sessionen och öppna nya flikar i samma fönster via debugporten. Nya browserfönster ska bara startas när ingen återanvändbar session finns eller när ett explicit restart-/ny-session-flöde används.

Terminal-input-adaptern för Level 2-test skriver separat JSONL-logg till:

```text
tmp\copilot_admin_runner_logs\terminal-input-YYYYMMDD.jsonl
```

## Viktig avgränsning

POC:n exekverar ännu **inte** Copilot CLI automatiskt. Den returnerar i första hand:

- strukturerad status
- grafdata
- rapportpekare
- standardiserade promptar/kommandoobjekt
- enkla POC-resultat för respektive bryggspår

Detta är avsiktligt, eftersom första frågan är vilken integrationsmodell som fungerar i praktiken utan att bryta nuvarande samarbetsflöde.

## Standardiserade kommandomallar

POC:n exponerar i första versionen mallar för:

- `kor regressionstest`
- `kor regressionstest {catalog_key}`
- `ga in i learning mode for regressionstest {catalog_key}`
- `uppdatera regressionstest {catalog_key}`
- ofarlig verifiering av att ett bridge-genererat kommando når rätt Copilot CLI-session

Målen är:

- att göra dessa kommandon maskinläsbara
- att låta framtida UI-lager visa enhetliga åtgärder
- att ge host runnern ett tydligt kontrakt för vad den ska kunna returnera

## Bryggspår som ska provas

## 1. HTTP-API

Startas via:

```powershell
.\runtime\start-copilot-admin-runner.ps1
```

Om host-adressen behöver anges explicit används parameter `-HostAddress`, inte `-Host`, eftersom `$Host` är en reserverad/read-only PowerShell-variabel:

```powershell
.\runtime\start-copilot-admin-runner.ps1 -HostAddress 127.0.0.1 -Port 8765
```

Detta spår är tänkt att ge:

- health endpoint
- status endpoint
- graph endpoint
- kommandomallar via JSON

Det är det naturligaste spåret för en framtida Docker-control-plane, men måste verifieras mot lokal drift- och säkerhetsmiljö.

Minsta test:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/status
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/graph
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8765/commands/run-regression-by-key?catalog_key=A"
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8765/commands/verify-bridge-session?verification_id=manual-http-test"
```

## 2. Filkö / jobbkatalog

Exempel:

```powershell
.\runtime\windows\copilot-admin\bridge\submit-copilot-admin-queue-job.ps1 -CommandId run-regression-all
.\runtime\windows\copilot-admin\bridge\process-copilot-admin-queue-once.ps1
```

Detta spår används för att prova:

- hur enkelt jobb kan lämnas och hämtas
- hur status/resultat kan skrivas tillbaka
- om en filbaserad brygga känns tillräcklig i den faktiska operatörsmiljön

Efter körning ska resultat kontrolleras i:

```text
tmp\copilot_admin_queue\results
```

## 3. Named pipe / terminalnära brygga

Källskriptet stöder även:

- `pipe-server`
- `pipe-request`

Runtime-entrypoint finns för klientförfrågningar:

```powershell
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action status
```

Detta spår används för att bedöma om en mer Windows-/sessionnära kommunikation är mer realistisk än HTTP eller filkö.

Minsta test:

```powershell
cd <SPS-rot>
python .\tools\source\copilot_admin_runner\copilot_admin_runner.py pipe-server --pipe-name sps-copilot-admin-runner
```

Klientförfrågan körs i ett annat PowerShell-fönster. Även det fönstret ska stå i SPS-roten, eller använda absolut sökväg till runtime-skriptet:

```powershell
cd <SPS-rot>
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action health
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action status
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action graph
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action command-template -CommandId run-regression-by-key -CatalogKey A
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action command-template -CommandId verify-bridge-session -VerificationId manual-pipe-test
```

## Acceptance criteria för POC-fasen

Bryggspåren bör bedömas mot följande frågor:

1. Går det att använda modellen utan att bryta det nuvarande operatörsflödet med Copilot?
2. Går det att läsa status, loggar och resultat på ett användbart sätt?
3. Fungerar modellen tillsammans med host-bundna delar som PowerShell och synlig browser?
4. Skapar modellen omedelbara hinder i intern säkerhet eller lokal drift?
5. Är modellen tillräckligt enkel att bygga vidare på i en tunn Docker-control-plane?

## Level 2 - automatisk terminalinmatning

Level 2 testar om ett bridge-genererat kommando kan klistras in i den redan synliga Copilot CLI-terminalen.

Källkod:

- `tools\source\copilot_admin_runner\Invoke-TerminalInputAdapter.ps1`

Runtime:

- `runtime\bind-copilot-admin-terminal.ps1`
- `runtime\invoke-copilot-admin-terminal-input.ps1`
- `runtime\test-copilot-admin-bridge-level2-http.ps1`
- `runtime\test-copilot-admin-bridge-level2-queue.ps1`
- `runtime\test-copilot-admin-bridge-level2-pipe.ps1`

Säkerhetsmodell:

- `-DryRun` genererar prompt och logg men klistrar inte in något.
- Utan `-DryRun` krävs `-Arm`.
- Level 2-skripten använder som standard ett bundet Copilot-terminalfönster. Bindningen görs en gång per uppstart:

```powershell
.\runtime\bind-copilot-admin-terminal.ps1 -CountdownSeconds 8
```

- `-UseForegroundWindow` finns som diagnostiskt undantag och återgår till tidigare beteende där aktivt fönster efter nedräkning används.
- Standardleverans använder `ForegroundSendKeys`, vilket aktiverar det bundna Copilot-fönstret före inmatning. Det är stabilare men stör användaren visuellt.
- `-BackgroundWindow` testade experimentellt `BackgroundPostMessage`, där adaptern skickar tecken till det bundna fönstrets window handle utan att först lägga fönstret i foreground. Praktiskt test visade att detta inte fungerar tillförlitligt mot Copilot CLI/Windows Terminal och ska därför inte användas som normal väg.
- Som standard rensar adaptern aktiv inputrad med `Ctrl+U` och `Ctrl+K` precis före paste. Detta behövs eftersom Copilot CLI inte exponerar ett säkert lokalt API för att läsa om promptfältet redan innehåller text.
- `-PreserveExistingInput` finns för felsökning men ska inte användas för normala automatiserade Copilot-kommandon.
- Första verkliga testet ska köras utan `-Submit`, så adaptern bara klistrar in text och användaren trycker Enter manuellt.
- `-Submit` får endast användas efter att paste-only har verifierats mot rätt synlig Copilot-terminal.

Exempel:

```powershell
.\runtime\test-copilot-admin-bridge-level2-http.ps1 -DryRun
.\runtime\windows\copilot-admin\terminal\test-copilot-admin-bridge-level2-queue.ps1 -DryRun
.\runtime\windows\copilot-admin\terminal\test-copilot-admin-bridge-level2-pipe.ps1 -DryRun
```

Armerat paste-only-test:

```powershell
.\runtime\test-copilot-admin-bridge-level2-http.ps1 -Arm -CountdownSeconds 8
```

Experimentellt bakgrundstest, dokumenterat som icke godkänt:

```powershell
.\runtime\test-copilot-admin-bridge-level2-http.ps1 -Arm -Submit -BackgroundWindow -CountdownSeconds 8
```

För normal drift ska HTTP-spåret därför använda bundet fönster med foreground-aktivering, alternativt en framtida runner-ägd Copilot/PTY-session om foreground-störningen måste elimineras.

## Runner-ägd Copilot-session / PTY POC

För att utvärdera om foreground-störningen kan elimineras finns en separat POC:

- `tools\source\copilot_admin_runner\Start-OwnedCopilotSessionPoc.ps1`
- `tools\source\copilot_admin_runner\owned_copilot_pty.py`
- `runtime\start-copilot-admin-owned-terminal-poc.ps1`
- `runtime\test-copilot-admin-owned-stdio-poc.ps1`
- `runtime\test-copilot-admin-conpty-probe.ps1`
- `runtime\test-copilot-admin-conpty-scripted.ps1`
- `runtime\start-copilot-admin-conpty-session.ps1`

POC:n skiljer på två saker som ofta blandas ihop:

| Läge | Vad det bevisar | Begränsning |
| --- | --- | --- |
| Synligt runner-startat terminalfönster | Runnern kan starta en ny synlig Copilot CLI-yta i rätt repo, vilket kan vara kollaborativt för användaren. | Stdin/stdout ägs fortfarande av terminalfönstret, inte av runnern. Kommandon behöver terminal-input-adapter eller framtida PTY. |
| Redirected stdio-probe | Runnern kan äga stdout/stderr för icke-interaktiva Copilot CLI-kommandon. | Bevisar inte en synlig kollaborativ interaktiv session. |

Säkra tester:

```powershell
.\runtime\windows\copilot-admin\pty\test-copilot-admin-owned-stdio-poc.ps1
.\runtime\windows\copilot-admin\pty\start-copilot-admin-owned-terminal-poc.ps1 -DryRun
```

Synligt POC-test:

```powershell
.\runtime\windows\copilot-admin\pty\start-copilot-admin-owned-terminal-poc.ps1
```

Om ett nytt Copilot-fönster startas kan det därefter bindas med `runtime\bind-copilot-admin-terminal.ps1` och styras via HTTP Level 2. Detta ger en runner-startad kollaborativ yta, men är ännu inte en full PTY där runnern samtidigt äger interaktiv stdin/stdout.

Praktisk observation: när runnern startar ett synligt terminalfönster med `Start-Process` kan användaren se och använda Copilot-sessionen, men runnern kan inte läsa den löpande terminaloutputen. Loggen visar bara att fönstret/processen startades. För att web control plane ska kunna följa allt som sker i Copilot-sessionen krävs därför antingen:

- fortsatt foreground-/terminal-input-adapter plus separata status/loggar från runnern
- eller ett senare full-PTY-spår där runnern äger en interaktiv Copilot-process och samtidigt exponerar en synlig samarbetsyta

### ConPTY-spår

`owned_copilot_pty.py` använder Windows ConPTY via Python `ctypes` och kräver inga npm-paket. Det testar om host runnern kan äga en pseudo-terminal, läsa output och skriva input.

Säkert probe:

```powershell
.\runtime\windows\copilot-admin\pty\test-copilot-admin-conpty-probe.ps1
```

Scriptat kommando:

```powershell
.\runtime\windows\copilot-admin\pty\test-copilot-admin-conpty-scripted.ps1
```

Interaktiv Copilot-wrapper:

```powershell
.\runtime\windows\copilot-admin\pty\start-copilot-admin-conpty-session.ps1
```

Om ConPTY-wrappern fungerar med Copilot CLI ger den runnern stdin/stdout-ägande och en speglad terminalyta. Om Copilot CLI kräver terminalfunktioner som wrappern inte hanterar behöver nästa POC sannolikt använda en robustare PTY-runtime, exempelvis `node-pty`.

Praktiska observationer hittills:

- ConPTY-probe med `cmd.exe /c echo conpty-probe-ok` fungerar.
- Scriptat ConPTY-kommando via `cmd.exe` fungerar.
- `copilot --version` fungerar genom ConPTY och bevisar att runnern kan fånga stdout/stderr för ett enkelt Copilot CLI-kommando.
- `copilot -p "Svara exakt: owned-copilot-poc-ok"` slutförde inte inom POC-timeout och terminerades. Det betyder att full Copilot-kompatibilitet via den handskrivna ConPTY-wrappern inte är bevisad.

Slutsats just nu: ConPTY-spåret är tekniskt möjligt, men behöver mer arbete innan det kan ersätta HTTP + bundet terminalfönster. Nästa alternativa POC om detta spår ska fortsätta är en robustare PTY-runtime, exempelvis `node-pty`.

### Node-pty-spår

För att få en mer beprövad PTY-runtime än handskriven Python/ctypes-ConPTY finns ett separat `node-pty`-spår:

- `tools\source\copilot_admin_runner\node_pty_poc\package.json`
- `tools\source\copilot_admin_runner\node_pty_poc\package-lock.json`
- `tools\source\copilot_admin_runner\node_pty_poc\node_pty_poc.mjs`
- `runtime\install-copilot-admin-node-pty-poc.ps1`
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-probe.ps1`
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-version.ps1`
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-prompt.ps1`
- `runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-session.ps1`

Förutsättning: Node.js LTS och npm måste vara installerat. Skripten söker först i PATH och därefter i standardinstallationsvägar för Node.js på Windows. Om `npm` saknas kan Node.js LTS installeras med:

```powershell
winget install OpenJS.NodeJS.LTS
```

Öppna därefter helst ett nytt PowerShell-fönster så PATH uppdateras. Om agentprocessen redan körs kan installeraren ändå hitta `C:\Program Files\nodejs`.

Installera beroendet:

```powershell
.\runtime\install-copilot-admin-node-pty-poc.ps1
```

Kör tester:

```powershell
.\runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-probe.ps1
.\runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-version.ps1
.\runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-prompt.ps1
```

Starta interaktiv wrapper:

```powershell
.\runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-session.ps1
```

Starta samma wrapper i ett nytt synligt användarfönster:

```powershell
.\runtime\start-copilot-admin-node-pty-window.ps1
```

Om en tidigare wrapper-session finns måste den stängas och verifieras innan en ny POC körs. Launchern blockerar därför när statefilen pekar på en aktiv wrapperprocess. För en kontrollerad omstart:

```powershell
.\runtime\start-copilot-admin-node-pty-window.ps1 -RestartExisting
```

För diagnostik av om runnern ser användarens tangentinput kan fönstret startas med explicit inputloggning:

```powershell
.\runtime\start-copilot-admin-node-pty-window.ps1 -LogInput
```

Använd endast icke-känslig testtext i detta läge. Input skrivs då till `tmp\copilot_admin_runner_state\node-pty-copilot-session-input.txt` och `last_input_tail` i statefilen.

Skicka in text programatiskt till den aktiva node-pty-ägda Copilot-sessionen:

```powershell
.\runtime\send-copilot-admin-node-pty-input.ps1 -Text "dra ett skämt"
```

Detta använder wrapperns lokala inputkö under `tmp\copilot_admin_runner_state\node-pty-copilot-input-queue` och skriver direkt till Copilot-processens PTY. Det använder inte Windows foreground, clipboard eller `SendKeys`.

Målet med detta spår är att avgöra om en robust PTY-runtime kan ge både runner-ägd stdin/stdout och en användbar speglad samarbetsyta. Om det fungerar bättre än Python/ctypes-ConPTY kan detta bli nästa arkitekturspår för att eliminera foreground-aktivering.

Praktiskt resultat 2026-08-27:

- `node-pty` installerades lokalt efter att installeraren kompletterats med explicit Node/npm-resolver.
- Echo-probe passerade.
- `copilot --version` passerade genom `node-pty` när Copilot CLI anropades via absolut WinGet-sökväg.
- `copilot -p "Svara exakt: node-pty-copilot-prompt-ok"` passerade och output fångades via runner-ägd PTY.

Kvar att verifiera innan arkitekturval: den interaktiva wrappern måste provas som samarbetsyta, alltså att användaren kan skriva i den synliga wrapperterminalen samtidigt som runnern äger stdin/stdout och kan spegla/logga händelser.

Viktig begränsning från praktiskt användartest 2026-08-27: `node-pty`-wrappern startar en ny Copilot CLI-process. Den är därför inte samma konversation eller samma agentprocess som den redan pågående Copilot-sessionen där användaren och agenten arbetar. Agenten som kör detta arbete fortsätter svara i den ursprungliga sessionen, även om ett nytt synligt `node-pty`-fönster finns bredvid. Detta betyder att `node-pty`-spåret är lovande för en framtida runner-ägd Copilot-session som startas från början, men inte som drop-in-övertagande av en redan startad Copilot-session.

Konsekvens: för att `node-pty` ska bli huvudspår måste användarflödet starta med wrappern från början. Om kravet är att styra den befintliga Copilot-sessionen kvarstår HTTP + bound-window + foreground-modellen som det fungerande spåret.

Korrigerad testprincip: innan node-pty POC startas om ska pågående wrapperprocess upptäckas, avslutas, fönstret stängas/verifieras och först därefter ska ny wrapper startas med aktuell kod. Om processen inte stängs ska testet blockera och be användaren stänga fönstret manuellt.

Slutligt POC-resultat 2026-08-27:

- Ett rent, synligt node-pty-fönster startades med `.\runtime\start-copilot-admin-node-pty-window.ps1 -LogInput -RestartExisting`.
- Användaren accepterade Copilots katalogtrust och skrev i samma fönster.
- Wrappern fångade användarens input och Copilots output i transcript/state.
- Agenten skickade därefter `dra ett skämt i samma fönster` via `.\runtime\send-copilot-admin-node-pty-input.ps1`.
- Texten hamnade i samma node-pty-ägda Copilot-fönster och Copilot svarade med ett skämt.

Bedömning: node-pty-POC:n är godkänd för tvåvägskommunikation i ett runner-ägt Copilot-fönster. Den kan både ta emot användarens input i det gemensamma fönstret och injicera agentstyrd input utan Windows foreground, clipboard eller `SendKeys`.

Den synliga wrappern skriver state och transcript till:

- `tmp\copilot_admin_runner_state\node-pty-copilot-session.json`
- `tmp\copilot_admin_runner_state\node-pty-copilot-session-output.txt`
- `tmp\copilot_admin_runner_state\node-pty-copilot-session-input.txt` endast när diagnostikläget `-LogInput` används
- `tmp\copilot_admin_runner_state\node-pty-copilot-input-queue` för programatisk input till den aktiva wrappern

Statefilen innehåller bland annat `user_input_required`, `user_input_reason`, `last_output_tail` och `last_injected_text`, så en framtida control plane kan visa om Copilot väntar på användarens svar och vilken icke-känslig testinput som senast injicerades.

Viktigt edge case: Copilot CLI kan vid första körning eller ny katalog fråga efter mänsklig bekräftelse, exempelvis om katalogen ska litas på, eller kräva inloggning/auktorisering. PTY-spåret får därför inte tolka utebliven promptrespons som ett vanligt häng. Scriptade `node-pty`-tester detekterar interaktiva frågor i fångad output och rapporterar `user_input_required=true` med skäl, så att host runner/control plane kan visa att Copilot väntar på användaren i stället för att bara timea ut.

## Rekommenderad användning i nästa steg

1. Starta och prova varje bryggspår lokalt
2. Dokumentera faktiska hinder och styrkor
3. Lås först därefter den primära bryggstrategin
4. Bygg vidare host runnern till faktisk exekveringsmotor för runtime-skript och Copilot-kommandon

## Härdad host-runner-adapter

Det härdade Windows-kontraktet för nästa backendsteg finns i:

- `tools\docs\copilot-admin-host-runner-adapter.md`

Adaptern lägger ett maskinläsbart lager ovanpå POC:n för:

- ren Copilot-start/stopp med befintlig node-pty-sessiondetektion
- statuspolling för Copilot, transcript-tail, inputkö och `user_input_required`
- synlig collaborative-browser-start och stopp via befintligt runtime-skript och sparat state
- torra smoke-tester för session/input och browser-start utan destruktiv sidoeffekt
- real smoke-wrappers som startar, observerar och stoppar en host-ägd node-pty Copilot-session respektive en host-ägd synlig browser-session med JSON-state och JSONL-loggar
