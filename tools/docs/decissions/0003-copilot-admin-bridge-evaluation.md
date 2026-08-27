# 0003 - Utvärderingsprocess för Copilot-admin bridge-val

## Status

Proposed.

## Kontext

Copilot-admin behöver en brygga mellan en framtida Docker-control-plane och Windows host runnern. Bryggan får inte bedömas enbart teoretiskt, eftersom den måste fungera i den faktiska operatörsmiljön med:

- Copilot CLI i en gemensam Windows-terminal
- synlig browser där användaren kan logga in
- PowerShell-baserade runtime-skript
- lokal säkerhet och nätverksregler
- framtida web UI i Docker

De kandidater som ska jämföras är:

1. lokalt HTTP-API
2. filkö / jobbkatalog
3. named pipe / terminalnära Windows-brygga

## Beslutsprincip

Bridge-valet ska låsas först efter ett praktiskt test där alla kandidater bedöms mot samma case och samma acceptanskriterier.

Beslutet ska inte baseras på vilket alternativ som är mest elegant tekniskt, utan på vilket alternativ som bäst stödjer det gemensamma arbetsflödet:

1. användaren arbetar med Copilot i Windows-terminalen
2. användaren och Copilot delar en synlig browser
3. web UI visar status, rapporter, graf och standardkommandon
4. web UI kan initiera kommandon utan att skapa en isolerad Copilot-session i Docker

## Testcase för varje bridge-kandidat

Varje kandidat ska provas mot följande case.

| Case | Testfråga | Godkänt när |
| --- | --- | --- |
| Status | Kan web/klient läsa regressionstestkatalog, senaste rapport och kommandomallar? | Strukturerad JSON eller filresultat returneras utan manuell tolkning. |
| Mermaid | Kan web/klient hämta beroendegrafen? | Mermaid-källan från `testing\regression_test\regression-test-dependencies.mmd` kan visas eller returneras. |
| Learning Mode | Kan web/klient initiera ett standardiserat Learning Mode-kommando? | Ett kommandoobjekt skapas med testnyckel, läge och prompttext. |
| Regression Mode | Kan web/klient initiera `kör regressionstest` eller `kör regressionstest A`? | Ett kommandoobjekt eller jobb skapas och kan spåras till resultat/status. |
| Live-status | Kan användaren följa aktiv körning? | Bryggan kan visa aktivt jobb, vänteläge, senaste loggrad och slutstatus. |
| Browser-samband | Bryter bryggan den gemensamma synliga browsermodellen? | Browsern fortsätter ligga på Windows-värden och är observerbar via debug-port. |
| Copilot-samband | Hamnar kommandot i rätt Copilot-kontext? | Kommandot kan presenteras för eller skickas till den gemensamma Copilot CLI-sessionen, inte en separat Docker-session. |
| Drift | Är modellen begriplig att starta, stoppa och felsöka? | En operatör kan följa dokumenterade start-/felsökningssteg. |
| Säkerhet | Introduceras blockerande lokal risk? | Bryggan kan begränsas till lokal åtkomst och kräver inte bred nätverksexponering. |

## Särskilt test - samma Copilot-session

Det centrala bridge-testet är inte om control plane kan prata med host runnern. Det centrala testet är om ett kommando från control plane kan användas i **samma Copilot CLI-session** som operatören ser och samarbetar i.

HTTP-API, filkö och named pipe bevisar bara transporten mellan web/control plane och host runner. De bevisar inte automatiskt att kommandot hamnar i rätt Copilot-session.

För detta behövs ett separat sessionstest med tre nivåer.

### Nivå 1 - Manuell bekräftad handoff

Syfte: bevisa att webben kan skapa rätt kommando utan att riskera fel session.

Test:

1. Control plane genererar ett kommando, till exempel `kör regressionstest A`.
2. Kommandot visas med tydlig kontext: repo, miljö, test-ID, körläge och browserstatus.
3. Operatören kopierar eller bekräftar kommandot i den redan öppna Copilot CLI-sessionen.
4. Copilot utför en ofarlig verifieringsuppgift, till exempel att läsa status och skriva en verifieringsrad i `tmp`.

Godkänt när:

- kommandot körs i den terminalsession användaren redan ser
- Copilot arbetar i rätt SPS-repository
- inga separata Copilot-processer skapas
- användaren kan se och avbryta arbetsflödet

Detta är lägsta acceptabla modell för första versionen.

### Nivå 2 - Kontrollerad inmatning till aktiv terminal

Syfte: bevisa att host runnern kan föra in ett kommando i den befintliga Copilot CLI-terminalen utan manuell copy/paste.

Test:

1. Operatören startar Copilot CLI i en identifierbar Windows-terminal.
2. Host runnern får ett webbgenererat kommando.
3. Host runnern för in kommandot i den aktiva terminalen på ett kontrollerat sätt.
4. Copilot skapar samma verifieringsartefakt som i nivå 1.

Godkänt när:

- texten hamnar i den redan synliga Copilot CLI-sessionen
- ingen ny Copilot CLI-session startas
- användaren ser kommandot innan eller när det skickas
- fel terminal kan inte väljas tyst
- metoden fungerar efter omstart av runner/control plane

Om detta kräver osäker tangentbordsautomation eller riskerar fel fönster ska nivån inte godkännas för första versionen.

### Nivå 3 - Runner-ägd Copilot-session med synlig operatörsyta

Syfte: utvärdera en senare modell där host runnern startar och äger Copilot CLI-processen från början, men fortfarande gör sessionen synlig och samarbetsbar för användaren.

Test:

1. Host runnern startar Copilot CLI i en kontrollerad terminal-/PTY-modell.
2. Web control plane kan skicka kommando till samma process.
3. Operatören kan fortfarande läsa, skriva, avbryta och förstå sessionen.
4. Browsern är fortfarande den synliga Windows-browsern, inte en Docker-browser.

Godkänt när:

- både web UI och operatör har åtkomst till samma Copilot-process
- sessionen är synlig och begriplig för operatören
- Copilot arbetar i rätt repository och kan använda samma runtime/browsermodell
- inga viktiga CLI-funktioner bryts av PTY-/terminalmodellen

Detta är en möjlig målmodell, men ska inte krävas för första versionen.

### Verifieringsartefakt för sessionstest

För att undvika subjektiv bedömning ska Copilot i sessionstestet skapa eller uppdatera en temporär verifieringsfil under:

```text
tmp\copilot_admin_bridge_verification\
```

Filen ska innehålla:

- timestamp
- kommando-ID
- valt test-ID eller catalog key
- repository root som Copilot ser den
- om browser-debugporten är nåbar när testet kräver browser
- om kommandot kom via manuell handoff, terminalinmatning eller runner-ägd session

Filen är temporär och ska inte indexeras.

## Praktisk testordning

### Steg 1 - Baseline

1. Öppna SPS-repositoryt på Windows-värden.
2. Starta Copilot CLI i den gemensamma terminalen.
3. Starta vid behov den synliga browsern:

```powershell
.\runtime\start-collaborative-stage-browser.ps1
```

4. Kontrollera att grundstatus fungerar:

```powershell
.\runtime\show-regression-status.ps1
.\runtime\render-regression-graph.ps1
```

### Steg 2 - HTTP-API

1. Starta host runnern:

```powershell
.\runtime\start-copilot-admin-runner.ps1
```

Alternativt med explicit adress:

```powershell
.\runtime\start-copilot-admin-runner.ps1 -HostAddress 127.0.0.1 -Port 8765
```

2. Testa från Windows-värden:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/status
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/graph
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8765/commands/run-regression-by-key?catalog_key=A"
```

3. Testa från en lokal container när Docker-control-plane finns:

```powershell
docker run --rm curlimages/curl http://host.docker.internal:8765/health
```

4. Bedöm om detta kan bli primärt API för webben.

### Steg 3 - Filkö / jobbkatalog

1. Skicka ett jobb:

```powershell
.\runtime\windows\copilot-admin\bridge\submit-copilot-admin-queue-job.ps1 -CommandId run-regression-by-key -CatalogKey A
```

2. Processa ett jobb:

```powershell
.\runtime\windows\copilot-admin\bridge\process-copilot-admin-queue-once.ps1
```

3. Kontrollera att jobb, resultat och fel kan läsas under `tmp\copilot_admin_queue`.
4. Bedöm om modellen är tillräcklig som primär brygga eller bör vara fallback/audit-spår.

### Steg 4 - Named pipe

1. Starta pipe-servern från host runnern:

```powershell
cd <SPS-rot>
python .\tools\source\copilot_admin_runner\copilot_admin_runner.py pipe-server --pipe-name sps-copilot-admin-runner
```

2. Testa klientförfrågningar:

```powershell
cd <SPS-rot>
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action health
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action status
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action graph
.\runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1 -Action command-template -CommandId run-regression-by-key -CatalogKey A
```

3. Bedöm om terminalnärheten väger upp svagare Docker-/webbkompatibilitet.

### Steg 5 - Copilot-kommandotest

Detta är det avgörande testet och ska köras sist.

För varje kandidat ska vi prova om ett genererat kommando kan bli praktiskt användbart i den gemensamma Copilot-sessionen:

1. Generera kommandot `kör regressionstest A`.
2. Visa hur kommandot presenteras för operatören eller förs in i Copilot CLI.
3. Säkerställ att Copilot arbetar i samma repository, samma Windows-session och samma browsermodell.
4. Säkerställ att användaren kan se och avbryta/förstå vad som händer.

Om direkt inmatning i Copilot CLI inte kan bevisas säkert ska första versionen använda manuell bekräftelse: webben visar kommandot och operatören skickar det i Copilot CLI.

## Beslutsmall

När testerna är körda ska beslutet dokumenteras med följande format:

| Kandidat | Status | Styrkor | Svagheter | Rekommenderad roll |
| --- | --- | --- | --- | --- |
| HTTP-API |  |  |  |  |
| Filkö |  |  |  |  |
| Named pipe |  |  |  |  |

Rekommenderade roller kan vara:

- primär bridge
- fallback/audit bridge
- senare terminalintegration
- avvisad för första versionen

## Preliminär hypotes före test

HTTP-API är sannolikt bäst som primär bridge för Docker-control-plane eftersom webben behöver läsa status, rapporter och graf interaktivt.

Filkö är sannolikt bäst som fallback och audit-spår eftersom den är enkel, synlig och robust.

Named pipe är sannolikt bäst att behålla som senare terminalnära experiment, särskilt om direkt Copilot CLI-inmatning visar sig kräva en Windows-specifik lösning.

Denna hypotes ska inte betraktas som beslut förrän testfallen ovan är genomförda.

## Observerade POC-resultat

### 2026-08-27 - Level 1 same-session handoff

Följande resultat är observerade i den faktiska Windows-/Copilot-miljön:

| Kandidat | Resultat | Observation |
| --- | --- | --- |
| Filkö | Level 1 godkänd | `verify-bridge-session` skapades som filköjobb, processades till resultatfil och prompten kunde kopieras in i den aktiva Copilot CLI-sessionen. Copilot skapade `tmp\copilot_admin_bridge_verification\queue-20260827-083342.json` i rätt repository. |
| HTTP-API | Level 1 godkänd | HTTP-runnern startade på `127.0.0.1:8765`, `/commands/verify-bridge-session` returnerade prompt och Copilot skapade `tmp\copilot_admin_bridge_verification\http-20260827-083947.json` i rätt repository efter manuell handoff. |
| Named pipe | Level 1 godkänd | Pipe-server kunde startas och lyssna på `\\.\pipe\sps-copilot-admin-runner`, klienten returnerade `verify-bridge-session`-prompt och Copilot skapade `tmp\copilot_admin_bridge_verification\pipe-20260827-084611.json` i rätt repository efter manuell handoff. |

Viktig slutsats: HTTP, filkö och named pipe har nu alla bevisat **manuell bekräftad handoff till samma Copilot-session**. De har inte bevisat automatisk inmatning i den aktiva Copilot CLI-terminalen.

### Level 1-jämförelse efter verifiering

| Kandidat | Level 1-status | Praktisk roll efter test |
| --- | --- | --- |
| HTTP-API | Godkänd | Starkast kandidat som primär bridge för framtida Docker-control-plane, eftersom web UI enkelt kan läsa status, rapporter, graf och kommandomallar via HTTP. |
| Filkö | Godkänd | Stark kandidat som fallback/audit-spår eftersom jobb och resultat är synliga som filer och enkla att felsöka. |
| Named pipe | Godkänd | Fungerar för Windows-nära klient/server-kommunikation, men bör främst utvärderas vidare för Level 2-terminalinmatning eftersom den är mindre naturlig för Docker/webb än HTTP. |

Nästa beslutsfråga är Level 2: om någon brygga säkert kan föra in ett kommando i den redan synliga Copilot CLI-sessionen utan manuell copy/paste och utan risk att träffa fel terminal.

### Level 2-test - automatisk inmatning i aktiv Copilot-terminal

Level 2 ska inte blandas ihop med HTTP, filkö eller named pipe. De tre bryggorna kan skapa och transportera kommandoobjekt, men automatisk inmatning kräver dessutom en **host-side terminal input adapter** på Windows.

Testet ska därför delas i två delar:

1. vald brygga genererar samma `verify-bridge-session`-prompt som i Level 1
2. en lokal Windows-adapter försöker mata in prompten i den redan synliga Copilot CLI-terminalen

#### Säkerhetsregler för testet

Level 2 får bara testas med `verify-bridge-session`, aldrig direkt med ett destruktivt eller långkörande kommando.

Testet är bara godkänt om:

- användaren uttryckligen armerar testet
- Copilot-terminalen är synlig
- prompten visas eller kan granskas före Enter
- adaptern kan identifiera eller kräva rätt aktivt terminalfönster
- fel fönster inte kan väljas tyst
- ingen ny Copilot CLI-session startas
- verifieringsfilen skapas i rätt SPS-root

Om testet kräver blind tangentbordsautomation utan säker målidentifiering ska Level 2 underkännas för första versionen.

#### Rekommenderad praktisk testmetod

Första Level 2-testet bör vara en armerad, användarövervakad adapter:

1. Användaren startar den befintliga Copilot CLI-sessionen i SPS-roten.
2. Bryggan genererar `verify-bridge-session` med unikt verification ID.
3. Host runner/adaptern visar prompten och startar en kort nedräkning, exempelvis 5-10 sekunder.
4. Användaren fokuserar den synliga Copilot CLI-terminalen under nedräkningen.
5. Adaptern klistrar in prompten, men första versionen bör inte trycka Enter automatiskt förrän målidentifiering är bevisad.
6. Användaren trycker Enter.
7. Copilot skapar verifieringsfilen.

Detta testar automatisk inmatning av text utan att direkt riskera att ett kommando exekveras i fel fönster.

Implementerade runtime-entrypoints för detta test:

- `runtime\bind-copilot-admin-terminal.ps1`
- `runtime\test-copilot-admin-bridge-level2-http.ps1`
- `runtime\test-copilot-admin-bridge-level2-queue.ps1`
- `runtime\test-copilot-admin-bridge-level2-pipe.ps1`
- `runtime\invoke-copilot-admin-terminal-input.ps1`

Terminal-input-adaptern stöder `-DryRun`, kräver `-Arm` för verklig inklistring och använder `-Submit` först när paste-only-test har godkänts.

#### Bound window mode

För tillförlitlig drift ska Copilot-terminalen bindas en gång per uppstart:

```powershell
.\runtime\bind-copilot-admin-terminal.ps1 -CountdownSeconds 8
```

Bindningen sparar window handle, process-ID och fönstertitel i:

```text
tmp\copilot_admin_runner_state\bound-copilot-terminal.json
```

Level 2-testskripten använder därefter bound-window mode som standard. Vid körning verifierar adaptern att fönsterhandtaget fortfarande är giltigt, försöker aktivera det bundna fönstret och loggar både startfönster och mål-/send-fönster.

`-UseForegroundWindow` finns endast som diagnostiskt fallbackläge och ska inte användas i normal automatisering.

#### Background window mode

Efter att bound-window mode visade sig fungera, men visuellt stör användaren genom att Copilot-fönstret läggs i foreground, införs ett experimentellt läge:

```powershell
.\runtime\test-copilot-admin-bridge-level2-http.ps1 -Arm -Submit -BackgroundWindow -CountdownSeconds 8
```

Detta använder `BackgroundPostMessage` mot det bundna window handle i stället för foreground-baserad `SendKeys`.

Godkänt endast om:

- Copilot-fönstret inte läggs i foreground
- prompten ändå tas emot av rätt Copilot CLI-session
- eventuell befintlig input rensas eller inte kan störa kommandot
- verifieringsfilen skapas i rätt SPS-root
- loggen visar `delivery_mode=BackgroundPostMessage`

2026-08-27 testades bakgrundsläget praktiskt och fungerade inte mot den aktiva Copilot CLI-/Windows Terminal-miljön.

Detta betraktas inte som ett fel i HTTP-bridgen. Beslutspunkt efter test:

- `BackgroundPostMessage` ska inte användas som normal väg.
- HTTP-bridge + bundet fönster + foreground-aktivering är den fungerande Level 2-vägen i nuläget.
- Om foreground-störningen måste elimineras krävs ett senare arkitekturspår där host runnern äger Copilot-processen via en kontrollerad terminal-/PTY-modell.

#### Runner-ägd Copilot-process / PTY POC

För att testa nästa arkitekturspår finns en separat POC:

- `runtime\start-copilot-admin-owned-terminal-poc.ps1`
- `runtime\test-copilot-admin-owned-stdio-poc.ps1`
- `runtime\test-copilot-admin-conpty-probe.ps1`
- `runtime\test-copilot-admin-conpty-scripted.ps1`
- `runtime\start-copilot-admin-conpty-session.ps1`

Testet delar upp frågan i två separata egenskaper:

1. Synlig kollaborativ session: runnern startar ett nytt PowerShell-fönster i SPS-roten och kör `copilot`.
2. Ägd stdio: runnern kör ett icke-interaktivt Copilot CLI-kommando med redirectad stdout/stderr.

Godkänd full målbild kräver båda samtidigt, det vill säga en synlig samarbetsyta där runnern samtidigt har säker programmatisk stdin/stdout. Den nuvarande POC:n kan visa om respektive halva är möjlig, men en full gemensam PTY-lösning kräver sannolikt ytterligare implementation om båda egenskaperna behövs i samma process.

Praktisk observation efter synligt terminaltest: runnern kan starta ett nytt synligt Copilot-fönster i rätt repository, men eftersom processen körs i ett separat terminalfönster via `Start-Process` äger runnern inte den löpande interaktiva stdin/stdout-strömmen. Därmed kan runnern inte själv "se" allt som sker i fönstret. Detta är en kollaborativ synlig session, men inte en full PTY-lösning.

Nästa PTY-spår implementeras därför med Windows ConPTY via Python `ctypes`. Det ska först bevisa en ofarlig echo-probe och scriptad stdin/stdout, därefter testas med Copilot CLI. Om stdlib/ctypes-spåret inte är tillräckligt robust ska ett `node-pty`-baserat alternativ övervägas.

Praktiskt resultat:

- `cmd.exe /c echo conpty-probe-ok` fungerar via ConPTY.
- Scriptat `cmd.exe`-kommando fungerar via ConPTY.
- `copilot --version` fungerar via ConPTY.
- `copilot -p "Svara exakt: owned-copilot-poc-ok"` slutförde inte inom POC-timeout och behövde termineras.

Beslutspunkt: handskriven Python/ctypes-ConPTY är tillräcklig för att bevisa att host runnern kan äga en pseudo-terminal, men ännu inte tillräcklig för att ersätta den fungerande HTTP + bound-window + foreground-modellen för Copilot CLI. Om PTY-spåret ska prioriteras vidare bör nästa implementation sannolikt använda en etablerad PTY-runtime, till exempel `node-pty`, och jämföras mot den nu fungerande HTTP-modellen.

#### Node-pty POC

För att följa PTY-spåret vidare finns ett `node-pty`-baserat POC-spår:

- `runtime\install-copilot-admin-node-pty-poc.ps1`
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-probe.ps1`
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-version.ps1`
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-prompt.ps1`
- `runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-session.ps1`
- `runtime\start-copilot-admin-node-pty-window.ps1`

Detta spår kräver npm-installation av `node-pty` i `tools\source\copilot_admin_runner\node_pty_poc`.

Acceptansordning:

1. `node-pty` kan installeras lokalt. Status 2026-08-27: passerat.
2. Echo-probe passerar. Status 2026-08-27: passerat.
3. `copilot --version` passerar. Status 2026-08-27: passerat via absolut Copilot CLI-sökväg.
4. `copilot -p` passerar eller ger tydlig, loggad begränsning. Status 2026-08-27: passerat med verifierad output.
5. Interaktiv wrapper kan starta Copilot och spegla output/input på ett sätt som användaren upplever som kollaborativt.

Först om dessa passerar bör `node-pty` jämföras affärsmässigt mot HTTP + bound-window + foreground-modellen.

Den interaktiva wrappern ska i användartest startas via `runtime\start-copilot-admin-node-pty-window.ps1`, eftersom det öppnar ett separat synligt PowerShell-fönster där användaren kan skriva samtidigt som node-pty-wrappern äger och loggar Copilot-processens PTY.

Praktiskt användartest 2026-08-27 visade en avgörande begränsning: det nya fönstret är en ny Copilot CLI-process, medan agenten fortfarande arbetar i den ursprungliga Copilot-sessionen. `node-pty` kan alltså äga stdin/stdout för en Copilot-process den själv startar, men det flyttar inte den befintliga agentkonversationen till det nya fönstret och tar inte över en redan körande Copilot-session.

Beslutsimplikation: `node-pty` är ett möjligt huvudspår endast om den operativa Copilot-sessionen alltid startas genom wrappern från början. För befintliga sessioner är det inte ett ersättningsspår för samma-session-styrning.

Korrigerad POC-regel: före omstart måste testet upptäcka befintlig wrapper-session, avsluta den, verifiera att processen/fönstret är stängt och blockera med tydligt meddelande om stängning inte lyckas. Annars riskerar testet att blanda gammal session, ny wrapper och fel fönster.

Godkänt POC-resultat 2026-08-27: efter ren start med `-RestartExisting` och `-LogInput` kunde användaren skriva i det gemensamma node-pty-fönstret, wrappern kunde läsa input/output, och agenten kunde skicka `dra ett skämt i samma fönster` via node-pty-inputkön. Copilot svarade i samma fönster. Detta bevisar tvåvägskommunikation för en runner-ägd Copilot-session utan foreground-aktivering, clipboard eller `SendKeys`.

Beslutsimplikation: node-pty är nu det starkaste spåret för en framtida operativ modell där Copilot-sessionen startas genom runnern från början. HTTP + bound-window kvarstår som fungerande reservspår för befintliga manuellt startade Copilot-sessioner.

För att bevisa att wrappern faktiskt ser användarens tangentinput finns ett explicit diagnostikläge: `runtime\start-copilot-admin-node-pty-window.ps1 -LogInput`. Det ska endast användas med icke-känslig testtext eftersom det skriver input till lokal tmp-state.

För att bevisa agentstyrd input utan foreground används `runtime\send-copilot-admin-node-pty-input.ps1 -Text "<kommando>"`. Kommandot lägger en JSON-fil i wrapperns lokala inputkö och wrappern skriver själv texten till Copilot-processens PTY. Det är den kritiska skillnaden mot tidigare `SendKeys`-spår.

Viktig acceptansregel: PTY-spåret måste kunna exponera när Copilot väntar på mänsklig återkoppling, till exempel katalogtrust, inloggning eller annan bekräftelse. Ett sådant läge ska rapporteras som `user_input_required`, inte som en anonym timeout eller "hängd" Copilot-process. Detta är nödvändigt för att en framtida control plane ska kunna instruera användaren att svara i den speglade terminalen.

#### Edge case - befintlig text i Copilot-prompten

Copilot CLI exponerar inget säkert lokalt API för att läsa om promptfältet redan innehåller text. Level 2-adaptern ska därför inte försöka tolka fältets innehåll.

Standardbeteendet är i stället att göra inputläget deterministiskt:

1. användaren armerar testet
2. användaren fokuserar rätt Copilot CLI-terminal
3. adaptern skickar `Ctrl+U` och `Ctrl+K` för att rensa aktiv inputrad
4. adaptern klistrar in den genererade prompten
5. adaptern skickar Enter endast om `-Submit` används

Detta loggas med `clear_existing_input=true`. `-PreserveExistingInput` finns endast för felsökning och ska inte användas i normal automatisering.

#### Nästa nivå efter säker klistring

Om armerad klistring fungerar kan ett andra test tillåta `paste-and-submit`, där adaptern även skickar Enter. Det ska bara godkännas om fönsteridentifiering och användarbekräftelse är tillräckliga.

#### Observerat Level 2-resultat

2026-08-27 verifierades `file-queue` med armerad paste-only-körning:

- `runtime\test-copilot-admin-bridge-level2-queue.ps1 -Arm -CountdownSeconds 8` genererade `queue-level2-20260827-085632`.
- Terminal-input-adaptern klistrade in prompten i den redan synliga Copilot CLI-sessionen.
- Skärmobservation visade prompten i Copilot CLI:s inputrad utan att Enter hade skickats automatiskt.
- Ett wrapperfel uppstod efter inklistringen eftersom armeringsmeddelanden blandades med JSON på stdout och `ConvertFrom-Json` försökte tolka texten `Copilot-admin...` som JSON.
- Felet korrigerades genom att armerings-/nedräkningsmeddelanden skrivs till stderr, medan stdout reserveras för maskinläsbar JSON.

Slutsats: `file-queue` är Level 2 paste-only-godkänd för terminalinmatning. `paste-and-submit` är ännu inte godkänd.

2026-08-27 verifierades även `HTTP-API` med armerad paste-only-körning:

- `runtime\test-copilot-admin-bridge-level2-http.ps1 -Arm -CountdownSeconds 8` genererade `http-level2-20260827-085940`.
- HTTP-runnern loggade `/commands/verify-bridge-session` och returnerade kommandoprompten.
- Terminal-input-loggen visar `terminal_input_requested` med `bridge=http-api`, `armed=true`, `submit=false` och `foreground_window_title_at_start=Windows PowerShell`.
- Terminal-input-loggen visar därefter `terminal_input_sent` med `foreground_window_title_at_send=Create Copilot Admin Bridge Directory - GitHub Copilot`.
- Skärmobservation visade prompten i Copilot CLI:s inputrad utan att Enter hade skickats automatiskt.

Slutsats: `HTTP-API` är Level 2 paste-only-godkänd för terminalinmatning. `paste-and-submit` är ännu inte godkänd.

#### Förväntad roll per brygga i Level 2

| Brygga | Level 2-roll |
| --- | --- |
| HTTP-API | Mest relevant om web control plane ska skapa kommandot och host runner ska anropa terminal input-adaptern. |
| Filkö | Relevant som audit/fallback där kommandot först skrivs som jobb och därefter plockas upp av adaptern. |
| Named pipe | Relevant om terminal input-adaptern ska vara Windows-nära och långkörande i samma host-session. |

### Identifierade korrigeringar

- `runtime\start-copilot-admin-runner.ps1` använde tidigare parametern `$Host`, vilket krockade med PowerShells read-only `$Host`. Parametern är ändrad till `-HostAddress`.
- Verifieringsprompten ska hållas ASCII-säker eftersom vissa PowerShell-/terminalvägar återgav `Ändra` som `??ndra` eller mojibake. Prompten använder därför `Andra` i stället.
