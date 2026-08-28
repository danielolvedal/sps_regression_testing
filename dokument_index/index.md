# Dokumentindex

Detta index är den primära ingången för AI-agenter och människor som behöver hitta relevant material i SPS-repositoryts rotkatalog, oavsett var den ligger på disk.

## Läsordning för agenter

1. Läs `AGENTS.md`
2. Läs detta index
3. Gå sedan till relevanta dokument, datafiler, verktygsdokument eller runtime-skript för uppgiften

## Styrning och arbetssätt

- `AGENTS.md` - Övergripande agentinstruktioner för SPS-rotkatalogen; pekar vidare till detta index och fastställer arbetsordning.
- `tools\docs\katalogstruktur.md` - Fastlåser katalogstrukturen och reglerna för var olika typer av artefakter ska lagras.
- `tools\docs\raw-data-forandringsprocess.md` - Fastställer den obligatoriska processen när filer i `raw_data` tillkommer, ändras eller tas bort.
- `tools\docs\regressionstest-arbetsmodell.md` - Fastställer hur agenter ska tolka kommandon om regressionstest och hur UI-regressioner körs som instruktionsstyrda testfall.
- `tools\docs\regression-rapportering.md` - Defines the formal-English reporting standard for `test_reports`, including summaries and verified defect folders.
- `tools\docs\browser-samarbete-stage-session.md` - Beskriver standardmodellen för synlig browser-session med agent/användar-samarbete.
- `tools\docs\copilot-admin-browser-lagen.md` - Förtydligar skillnaden mellan synlig localhost-browser för manuellt Copilot-admin-arbete, stage-browsern och den isolerade automationsbrowsern för real-E2E.
- `tools\docs\copilot-admin-runner-poc.md` - Beskriver den första host-runner-POC:n för status, rapportläsning, Mermaid-graf och tre möjliga bryggspår mellan Windows och Docker-control-plane.
- `tools\docs\copilot-admin-host-runner-adapter.md` - Definierar Windows host-runner-kontraktet för backend/control-plane med Copilot-/browserstatus, start/stopp och säker inputkö.
- `tools\docs\copilot-admin-e2e-critical-coverage.md` - Maps Copilot-admin user stories to E2E/static/dry-run validations, documents the mandatory separation between production Copilot sessions and hidden isolated real-E2E sessions, and records remaining real-integration gaps.
- `tools\docs\copilot-admin-praktiskt-anvandarflode.md` - Beskriver den praktiska målprocessen för Copilot CLI, synlig browser och framtida Docker-control-plane samt vilka användarcase som ska valideras innan vidare implementation.
- `tools\docs\delad-browser-flikstyrning.md` - Beskriver hur agenten öppnar nya flikar i samma delade browserfönster för test och jämförelse mellan miljöer.
- `tools\docs\sps-regression-server-gapanalys-och-sammanslagning.md` - Sammanfattar externa `sps-regression-server`, jämför den mot nuvarande SPS-repo och beskriver rekommenderad sammanslagning och målarkitektur.
- `tools\docs\decissions\0001-session-bootstrap-via-browser.md` - Beslutsdokument som gör browserbootstrap till standard för UI-arbete.
- `tools\docs\decissions\0002-katalogstruktur.md` - Beslutsdokument som gör katalogstrukturen styrande.
- `tools\docs\decissions\0003-copilot-admin-bridge-evaluation.md` - Fastställer hur HTTP-API, filkö och named pipe ska testas mot samma praktiska case innan första Copilot-admin bridge-val låses.
- `tools\docs\road-map\README.md` - Beskriver vad framtida verktygs-roadmaps ska innehålla.
- `tools\docs\road-map\copilot-admin-control-plane.md` - Roadmap för en Docker-hostad control plane med Windows-runner, Copilot CLI och operativt stöd för SPS-regressioner.
- `tools\docs\road-map\ai-console-latency-layout-startup-plan.md` - Fleet-färdig plan för AI-konsolens startup-policy, latencykrav, layoutparitet, regressioner och integration.
- `tools\docs\decissions\README.md` - Beskriver vilka typer av verktygsbeslut som ska lagras i beslutskatalogen.

## Runtime och källkod för verktyg

- `start_tool.ps1` - Enkel rot-entrypoint som startar Regression tool suite: host-runner API samt backend/frontend, men låter AI-konsolen starta Copilot vid behov om inte `-StartCopilotSession` används.
- `restart_tool.ps1` - Enkel rot-entrypoint som först kör `stop_tool.ps1`, verifierar att stoppet lyckades utan blockerad status och startar därefter om tool suite via `start_tool.ps1`.
- `stop_tool.ps1` - Enkel rot-entrypoint som säkert stänger SPS-kontrollerade adminsessioner och servrar: projektets Copilot-sessioner, ägda browserinstanser, backend/webserver och host-runner när de matchar förväntade processer.
- `install_tool.ps1` - Enkel rot-entrypoint som kor pre-flight, installerar saknade beroenden och bara markerar installationen som klar nar `start_tool.ps1`-kraven ar uppfyllda.
- `runtime\README.md` - Beskriver runtime-strukturen med stabila root-wrappers samt Windows- och Docker-underkataloger.
- `runtime\install_tool.ps1` - Stabil root-wrapper som kor Windows-installern for `start_tool.ps1` med pre-flight forst.
- `runtime\start-collaborative-stage-browser.ps1` - Körklar entrypoint för att starta synlig InPrivate/Incognito-browser för SPS-sessioner.
- `runtime\start-collaborative-copilot-admin-browser.ps1` - Körklar entrypoint för att starta synlig browser för Copilot-admins localhost-UI på separat debug-port.
- `runtime\open-shared-browser-tab.ps1` - Körklar entrypoint för att öppna en ny flik i samma delade browserfönster.
- `runtime\inventory-kundtjanst-menus.ps1` - Körklar entrypoint för att extrahera Kundtjänstportalens menystruktur till rådata.
- `runtime\generate-kundtjanst-function-doc.ps1` - Körklar entrypoint som genererar CSC-manual från insamlad rådata.
- `runtime\start-copilot-admin-runner.ps1` - Stabil root-wrapper som startar HTTP-API-POC för lokal Windows-bunden host runner.
- `runtime\show-regression-status.ps1` - Returnerar strukturerad status från host-runner-POC:n med testkatalog, senaste rapport och tillgängliga kommandomallar.
- `runtime\render-regression-graph.ps1` - Returnerar Mermaid-källan för regressionsberoenden via host-runner-POC:n.
- `runtime\invoke-copilot-admin-host-runner.ps1` - Stabil root-wrapper för host-runner-adapterns status-, Copilot-, input- och browserkommandon.
- `runtime\start-copilot-admin-host-runner-api.ps1` - Stabil root-wrapper som startar host-runnerns HTTP API för backend/control-plane-integration på separat port.
- `runtime\test-copilot-admin-host-runner-status-input.ps1` - Säker smoke-testwrapper för Copilot-sessionstatus och torrkörd PTY-inputkö.
- `runtime\test-copilot-admin-test-isolation.ps1` - Regressionstest som verifierar att dev-/backend-/browser-E2E inte skriver till produktions-Copilot-kön och att full real-E2E använder dold isolerad testsession.
- `runtime\test-copilot-admin-host-runner-browser-start.ps1` - Säker smoke-testwrapper för browserstatus och torrkörd collaborative-browser-start.
- `runtime\test-copilot-admin-host-runner-real-copilot.ps1` - Real smoke-testwrapper som startar, observerar och stoppar en synlig node-pty-ägd Copilot-session.
- `runtime\test-copilot-admin-host-runner-real-browser.ps1` - Real smoke-testwrapper som startar, observerar och stoppar en synlig collaborative-browser-session på isolerad smoke-port.
- `runtime\bind-copilot-admin-terminal.ps1` - Binder ett synligt Copilot CLI-terminalfönster en gång per uppstart så Level 2-inmatning kan rikta sig till samma fönster även när andra fönster används.
- `runtime\test-copilot-admin-bridge-level2-http.ps1` - Hämtar verifieringsprompt via HTTP-bridge och skickar den vidare till terminal-input-adaptern för Level 2-test.
- `runtime\install-copilot-admin-node-pty-poc.ps1` - Stabil root-wrapper som installerar npm-beroenden för `node-pty`-baserad PTY-POC.
- `runtime\start-copilot-admin-node-pty-window.ps1` - Stabil root-wrapper som öppnar ett synligt PowerShell-fönster med en node-pty-ägd Copilot CLI-session.
- `runtime\send-copilot-admin-node-pty-input.ps1` - Stabil root-wrapper som köar text till den aktiva node-pty-ägda Copilot-sessionens inputkö.
- `runtime\windows\copilot-admin\bridge\submit-copilot-admin-queue-job.ps1` - Lägger ett standardiserat kommandoobjekt i filkö-POC:n.
- `runtime\windows\copilot-admin\bridge\process-copilot-admin-queue-once.ps1` - Processar ett enskilt köjobb i filkö-POC:n.
- `runtime\windows\copilot-admin\bridge\invoke-copilot-admin-pipe-request.ps1` - Skickar en klientförfrågan till named-pipe-POC:n.
- `runtime\windows\copilot-admin\terminal\invoke-copilot-admin-terminal-input.ps1` - Armerad Windows-adapter som kan torrköra eller klistra in ett verifieringskommando i terminalfönster.
- `runtime\windows\copilot-admin\terminal\test-copilot-admin-bridge-level2-queue.ps1` - Hämtar verifieringsprompt via filkö-bridge och skickar den vidare till terminal-input-adaptern.
- `runtime\windows\copilot-admin\terminal\test-copilot-admin-bridge-level2-pipe.ps1` - Hämtar verifieringsprompt via named-pipe-bridge och skickar den vidare till terminal-input-adaptern.
- `runtime\windows\copilot-admin\pty\start-copilot-admin-owned-terminal-poc.ps1` - Startar en synlig Copilot CLI-session från host runnern som POC för runner-startad samarbetsyta.
- `runtime\windows\copilot-admin\pty\test-copilot-admin-owned-stdio-poc.ps1` - Verifierar att host runnern kan äga stdout/stderr för icke-interaktiva Copilot CLI-kommandon.
- `runtime\windows\copilot-admin\pty\test-copilot-admin-conpty-probe.ps1` - Kör ett säkert Windows ConPTY-probe för att verifiera att host runnern kan äga en pseudo-terminal.
- `runtime\windows\copilot-admin\pty\test-copilot-admin-conpty-scripted.ps1` - Kör ett kommando genom Windows ConPTY med valfri scriptad input.
- `runtime\windows\copilot-admin\pty\start-copilot-admin-conpty-session.ps1` - Startar Copilot CLI i en runner-ägd ConPTY-wrapper.
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-probe.ps1` - Kör ett säkert `node-pty`-probe för att verifiera PTY-ägande utan Copilot.
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-version.ps1` - Kör `copilot --version` genom `node-pty`.
- `runtime\windows\copilot-admin\node-pty\test-copilot-admin-node-pty-copilot-prompt.ps1` - Testar ett icke-interaktivt `copilot -p`-kommando genom `node-pty`.
- `runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-session.ps1` - Startar Copilot CLI i en `node-pty`-ägd interaktiv wrapper.
- `runtime\windows\copilot-admin\node-pty\start-copilot-admin-node-pty-window.ps1` - Startar den interaktiva node-pty-wrappern i ett nytt synligt PowerShell-fönster för användar-/agent-samarbete.
- `runtime\windows\copilot-admin\node-pty\send-copilot-admin-node-pty-input.ps1` - Köar text till den aktiva interaktiva node-pty-wrappern utan att använda Windows foreground/SendKeys.
- `runtime\windows\copilot-admin\node-pty\Resolve-NodePtyTooling.ps1` - Hjälpfunktion som hittar `node` och `npm` via PATH eller standardinstallationsvägar.
- `runtime\docker\copilot-admin\start-backend.ps1` - Startar Copilot-admin control-plane UI/API direkt från repositoryt med Python stdlib HTTP-server.
- `runtime\docker\copilot-admin\build-backend-image.ps1` - Bygger Docker-image för Copilot-admin control-plane UI/API och visar körkommando med repo-mount.
- `runtime\docker\copilot-admin\test-e2e-dev.ps1` - Kör utvecklings-E2E för Copilot-admin mot riktig backend, statiskt frontendkontrakt, browser-E2E och injicerad säker host-state.
- `runtime\docker\copilot-admin\test-real-visible-e2e.ps1` - Kör real visible E2E genom att starta host-runner API, backend, dold isolerad Copilot-helper och separat collaborative browser för automation.
- `runtime\windows\copilot-admin\host-runner\invoke-copilot-admin-host-runner.ps1` - Windows-wrapper för backendvänliga host-runner-kommandon.
- `runtime\windows\copilot-admin\host-runner\start-copilot-admin-host-runner-api.ps1` - Startar Windows host-runnerns HTTP API för real-runner bridge från backend.
- `runtime\windows\copilot-admin\host-runner\test-copilot-admin-host-runner-status-input.ps1` - Verifierar maskinläsbar Copilot-sessionstatus och inputkö i torrkörning.
- `runtime\windows\copilot-admin\host-runner\test-copilot-admin-host-runner-browser-start.ps1` - Verifierar browserstatus och browser-start-kontrakt utan att starta ett nytt browserfönster.
- `runtime\windows\copilot-admin\host-runner\test-copilot-admin-host-runner-real-copilot.ps1` - Windows-implementation av real smoke för synlig node-pty Copilot-start, status, state/loggar och stopp.
- `runtime\windows\copilot-admin\host-runner\test-copilot-admin-host-runner-real-browser.ps1` - Windows-implementation av real smoke för synlig collaborative-browser-start, debugstatus, state/loggar och stopp.
- `runtime\windows\copilot-admin\install_tool.ps1` - Windows-entrypoint som delegerar till den faktiska install-logiken for `start_tool.ps1` och kor pre-flight innan atgarder.
- `runtime\test-document-index.ps1` - Körklar regressionstest som verifierar att alla beständiga dokument/datafiler är registrerade i detta index.
- `runtime\test-kallinventering-coverage.ps1` - Körklar regressionstest som verifierar att `syntetisk_data\common\kallinventering.md` täcker aktuellt innehåll i `raw_data`.
- `runtime\test-regression-dependencies.ps1` - Körklar regressionstest som verifierar att regressionstesternas metadata, katalog och Mermaid-beroenden är synkade.
- `tools\source\browser_collaboration\Start-CollaborativeBrowserSession.ps1` - Källkod för browserbootstrap med remote debugging.
- `tools\source\browser_collaboration\Start-CollaborativeCopilotAdminBrowserSession.ps1` - Källkod för den synliga Copilot-admin-localhost-browsern med separat debug-port och tydlig rollseparation mot stage och automation.
- `tools\source\browser_collaboration\Open-SharedBrowserTab.ps1` - Källkod för att öppna en ny flik i samma delade browserfönster via befintlig sidtarget.
- `tools\source\browser_collaboration\Invoke-KundtjanstMenuInventory.ps1` - Källkod för menyinventering via browser-debuggränssnittet.
- `tools\source\copilot_admin_runner\copilot_admin_runner.py` - Host-runner-POC som läser regressionstillgångar och provar HTTP-, filkö- och named-pipe-bryggor för en framtida Docker-control-plane.
- `tools\source\copilot_admin_runner\Bind-CopilotTerminalWindow.ps1` - Källkod för att binda ett synligt Copilot CLI-terminalfönster till en sparad window handle inför säker Level 2-inmatning.
- `tools\source\copilot_admin_runner\Invoke-TerminalInputAdapter.ps1` - Källkod för armerad terminal-input-adapter som loggar och testar om ett bridge-genererat kommando kan klistras in i aktiv Copilot CLI-terminal.
- `tools\source\copilot_admin_runner\Start-OwnedCopilotSessionPoc.ps1` - Källkod för POC kring runner-startad synlig Copilot-session och redirectad stdio-probe.
- `tools\source\copilot_admin_runner\Install-StartToolDependencies.ps1` - Install-logik som inventerar, rapporterar och atgardar beroenden sa att `start_tool.ps1` kan koras efter godkand pre-flight.
- `tools\source\copilot_admin_runner\project_session_registry.py` - Gemensamt sessionsregister för SPS-kontrollerade Copilot-sessioner som används för säker identifiering och avstängning i start-/stopflöden.
- `tools\source\copilot_admin_runner\owned_copilot_pty.py` - Python/ctypes-baserad Windows ConPTY-POC för runner-ägd pseudo-terminal utan externa beroenden.
- `tools\source\copilot_admin_runner\node_pty_poc\package.json` - Node.js-beroendemanifest för robustare `node-pty`-baserad PTY-POC.
- `tools\source\copilot_admin_runner\node_pty_poc\package-lock.json` - Låser installerade npm-beroenden för `node-pty`-baserad PTY-POC.
- `tools\source\copilot_admin_runner\node_pty_poc\node_pty_poc.mjs` - `node-pty`-baserad POC för runner-ägd stdin/stdout, Copilot-versionstest, Copilot-prompttest och interaktiv wrapper.
- `tools\source\copilot_admin_control_plane\backend\app.py` - Python stdlib-backend för Copilot-admin control plane med health/status, regression, rapport-, jobb-, logg- och E2E-control-API:er.
- `tools\source\copilot_admin_control_plane\backend\test_app.py` - Smoke-/unittest-svit för Copilot-admin backendens API-kontrakt och säkra rapportläsning.
- `tools\source\copilot_admin_control_plane\backend\Dockerfile` - Containerdefinition för backenddelen av Copilot-admin control plane.
- `tools\source\copilot_admin_control_plane\e2e\package.json` - Node-manifest för Playwright-baserad real-E2E mot Copilot-admin.
- `tools\source\copilot_admin_control_plane\e2e\package-lock.json` - Låser npm-beroenden för Playwright-baserad real-E2E mot Copilot-admin.
- `tools\source\copilot_admin_control_plane\e2e\real_visible_playwright_e2e.mjs` - Playwright-harness för verklig isolerad Copilot-admin-E2E med readiness-badges och latensartefakter.
- `tools\source\copilot_admin_control_plane\e2e\test_control_plane_dev_e2e.py` - Utvecklings-E2E som verifierar startup/API/UI-kontrakt, statusdiod, jobbcykel, rapporter, Mermaid, asynkronitet och loggkorrelation mot injicerad host-state.
- `tools\source\copilot_admin_control_plane\e2e\test_frontend_browser_e2e.py` - Browserbaserad E2E via Chrome/Edge CDP för Copilot-admin frontendens dashboard, statusdiod, modekontroller, regressionjobb, rapportläsare, loggar och Mermaid-interaktioner.
- `tools\source\copilot_admin_control_plane\frontend\index.html` - Frontendskal för Copilot-admin med dashboard, regressioner, Mermaid, rapporter, jobb och loggar.
- `tools\source\copilot_admin_control_plane\frontend\app.js` - Klientlogik för statuspolling, asynkrona jobb, rapportläsare och Mermaid-interaktioner.
- `tools\source\copilot_admin_control_plane\frontend\styles.css` - Visuell layout och statusdiod-/Mermaid-/rapportstilar för Copilot-admin.
- `tools\source\copilot_admin_control_plane\frontend\static-validate.ps1` - PowerShell-validering av frontendens kritiska test hooks, API-kopplingar och loggevents.
- `tools\source\copilot_admin_control_plane\frontend\static-validate.mjs` - Node.js-validering av frontendens kritiska test hooks, API-kopplingar och loggevents.
- `tools\source\documentation_generation\generate_kundtjanst_function_doc.py` - Källkod som omvandlar inventeringsdata till markdownmanual.
- `tools\source\document_index_validation\validate_document_index.py` - Validerar att dokument/datafiler i repositoryt finns refererade i detta index.
- `tools\source\document_index_validation\validate_kallinventering_coverage.py` - Validerar att `kallinventering.md` täcker alla spårade källor i `raw_data` och spårar dem till berörda syntetiska dokument.
- `tools\source\document_index_validation\validate_regression_dependencies.py` - Validerar att regressionstesternas metadata, katalogposter och Mermaid-beroenden hålls synkade.

## Syntetisk data

- `syntetisk_data\index.md` - Huvudindex för det syntetiska kunskapslagret och ingång till feature-, lifecycle- och tvärgående dokument.
- `syntetisk_data\kundtjanst-menykarta.md` - AI-optimerad sammanfattning av menyinventeringen och de viktigaste stage-problemen.
- `syntetisk_data\kundtjanst-menykarta-legacy.md` - AI-optimerad sammanfattning av menyinventeringen för stage legacy samt dess viktigaste skillnader mot nya stage.
- `syntetisk_data\common\syntetisk-data-standard.md` - Fastställer obligatorisk struktur, sektioner och underhållsregler för alla syntetiska dokument.
- `syntetisk_data\common\kallinventering.md` - Beskriver värdet, begränsningarna och rekommenderad användning för varje källa i `raw_data`.
- `syntetisk_data\common\ordlista-och-namnstandard.md` - Normaliserar begrepp, förkortningar och språk-/namnvariationer mellan miljöer.
- `syntetisk_data\lifecycle\kontraktets-livscykel.md` - Beskriver kontraktets hela livscykel från skapande till avslut och efterarbete.
- `syntetisk_data\feature\kontrakt\skapa-kontrakt.md` - Normaliserar skapaflödet för kontrakt och korttidsavtal.
- `syntetisk_data\feature\kontrakt\andra-kontrakt.md` - Beskriver hur befintliga kontrakt söks upp och ändras.
- `syntetisk_data\feature\kontrakt\prissattning-avisering-och-index.md` - Samlar prisändring, KPI/CPI, avisering, moms och ekonomilogik.
- `syntetisk_data\feature\kontrakt\uppsagning-och-avslut.md` - Beskriver uppsägningsprocess, massavslut, nyckeluppföljning och efterarbete.
- `syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md` - Samlar VRM-hantering, VRM-pooler och kontraktsdokument.
- `syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md` - Normaliserar kölistor, erbjudanden, manuell köläggning och importflöden.
- `syntetisk_data\feature\garage\garage-ds-setup-och-platser.md` - Beskriver DS, garage, zoner, platser, GK och anläggningsadministration.
- `syntetisk_data\feature\produkter\produkter-paket-och-tillstandstider.md` - Beskriver produktmallar, paket, tillståndsscheman och ekonomiska kodningar.
- `syntetisk_data\feature\nycklar\nycklar-access-och-anpr.md` - Samlar fysisk nyckelhantering, digital access, ANPR och accessberoenden.
- `syntetisk_data\feature\loggar\loggar-audit-och-drift.md` - Beskriver loggar, audit trails, backendprocesser och driftsövervakning.
- `syntetisk_data\feature\rapporter\rapporter-och-powerbi.md` - Beskriver operativa rapporter, Power BI och kända rapportproblem.
- `syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md` - Samlar kunder, fastighetsägare, CPS och Third Party Sales.
- `syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md` - Samlar de kundnära kanalerna och SaaS-/B2B-perspektivet.
- `syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md` - Beskriver tvärgående juridik, ekonomi och integrationsramar.
- `syntetisk_data\assets\images\README.md` - Fastställer hur bilder och visuella artefakter ska lagras för syntetiska dokument.

## Färdiga manualer

### Kundtjänst / CSC

- `manuals\csc_user_manuals\Kundtjänst - funktioner.md` - Fullständig meny-för-meny-genomgång av Kundtjänstportalen med syfte, UI-element och stage-status.

### Serviceportalen / slutanvändare

- `manuals\user_manuals\` - Målplats för färdiga manualer för användare i serviceportalen.

### Klienter / företag / SaaS

- `manuals\client_manuals\` - Målplats för färdiga manualer för klienter, företag och SaaS-kunder.

## Testdokumentation

- `testing\funktional_test\README.md` - Beskriver vad som ska täckas av funktionella tester och hur sådana testfall ska struktureras.
- `testing\funktional_test\shared-browser-session-notes.md` - Dokumenterar testnyttan med att öppna flera SPS-flikar i samma synliga browserfönster.
- `testing\regression_test\README.md` - Beskriver vad som ska täckas av regressionstester och hur återkommande verifiering ska organiseras.
- `testing\regression_test\regression-test-catalog.md` - Katalog över namngivna regressionstester med kortreferenser, sammanfattningar och Mermaid-baserade beroenden.
- `testing\regression_test\regression-test-dependencies.mmd` - Fristående Mermaid-kod för regressionsflödenas beroendegraf.
- `testing\regression_test\kontrakt-sok-anna-serviceportal-login.md` - Första manuella/shared-browser-regressionstestet för kontraktssökning på Anna och vidare login till serviceportalen i ny stage-flik.
- `testing\regression_test\serviceportal-nytt-kontrakt-migrated-ds.md` - Manuellt/shared-browser-regressionstest som efter `A` använder `Admin -> Migrate DS` för att välja ett DS med status `Migrated` och verifiera nytt kontrakt-flödet i serviceportalen.
- `testing\regression_test\serviceportal-checkout-verifiering-och-skapa-kontrakt.md` - Manuellt/shared-browser-regressionstest som efter `B` verifierar checkoutdata, priser, avgifter, avtalsgodkännande och skapande av kontrakt.
- `testing\regression_test\serviceportal-nytt-kontrakt-non-migrated-ds.md` - Manuellt/shared-browser-regressionstest som efter `A` använder `Admin -> Migrate DS` för att välja ett DS som inte är migrerat och verifiera köpbar produkt i serviceportalen.
- `testing\regression_test\document-index-coverage.md` - Fastställer regressionstestet som kontrollerar att alla beständiga dokument/datafiler finns med i `dokument_index\index.md`.
- `testing\regression_test\kallinventering-coverage.md` - Fastställer regressionstestet som kontrollerar att `kallinventering.md` hålls synkad med `raw_data`.
- `testing\regression_test\regression-dependency-coverage.md` - Fastställer regressionstestet som kontrollerar att testmetadata, regressionskatalogen och den fristående Mermaid-koden hålls synkade.

## Rådata och referensmaterial

- `raw_data\kundtjanst-funktioner-data.json` - Rå browserextraktion av menyer och sidor från Kundtjänstportalen stage.
- `raw_data\kundtjanst-funktioner-legacy-data.json` - Rå browserextraktion av menyer och sidor från Kundtjänstportalen stage legacy.
- `raw_data\sps_vs_legacy_summary.md` - Sammanfattar regressionsjämförelsen mellan nya stage och legacy, inklusive funktionsgap, stabilitet och språk-/namninkonsekvenser.
- `raw_data\251203 Manual Hyra.apcoa.se.docx` - Extern/manualrelaterad referens för hyra.apcoa.se.
- `raw_data\ANPR.docx` - Referensdokument om ANPR-relaterad funktionalitet.
- `raw_data\Bokstavsfonetik, förkortningar.docx` - Referensdokument för fonetik och förkortningar.
- `raw_data\DS Grundinformation Garagekommentarer.docx` - Referens om DS-grundinformation och garagekommentarer.
- `raw_data\Features.txt` - Enkel rå anteckningsfil om funktioner.
- `raw_data\SAAS services.txt` - Rå anteckningsfil om SaaS-tjänster.
- `raw_data\Serviceportalen Digitala tillstånd guide .pdf` - PDF-guide för serviceportalens digitala tillstånd.
- `raw_data\SPS Funktionsträd.txt` - Översiktligt funktionsträd för SPS.
- `raw_data\SPS Funktionsträd – Detaljerad Syst.txt` - Detaljerad systemorienterad funktionsträdsanteckning.
- `raw_data\SPS Funktionsträd – Komplett System.txt` - Komplett systemöversikt i textform.
- `raw_data\SPS Funktionsträd – Teknisk & Jurid.txt` - Funktionsträd med tekniskt och juridiskt fokus.
- `raw_data\SPS Funktionsträd – Utökad Specifik.txt` - Utökad specifikation av funktionsträd.
- `raw_data\SPS_function_spec_en.xlsx` - Engelsk funktionsspecifikation i Excel-format.
- `raw_data\SPS---Rulla-ut-statistik-för-fastighetsägare.pdf` - Referens-PDF om utrullning/statistik för fastighetsägare.
- `raw_data\System & länkar.xlsx` - System- och länksammanställning i Excel-format.
- `raw_data\Uthyrning Upplärning.docx` - Upplärningsmaterial för uthyrning.

## Huvudregler för framtida tillägg

- Nya dokument ska läggas i rätt katalog enligt `tools\docs\katalogstruktur.md`.
- Nya beständiga dokument ska registreras här med kort sammanfattning, utom körningsoutput under `test_reports`.
- Temporära filer ska aldrig indexeras här; de ska ligga i `tmp`.
- `runtime\test-document-index.ps1` är ett obligatoriskt test och ska alltid köras när beständiga dokument/datafiler skapas, ändras, flyttas eller tas bort.
- När `raw_data` ändras ska `runtime\test-kallinventering-coverage.ps1` också köras och `syntetisk_data\common\kallinventering.md` hållas uppdaterad.
- När ett namngivet regressionstest, `testing\regression_test\regression-test-catalog.md` eller `testing\regression_test\regression-test-dependencies.mmd` ändras ska `runtime\test-regression-dependencies.ps1` också köras.
