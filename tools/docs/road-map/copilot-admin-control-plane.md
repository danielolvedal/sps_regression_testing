# Roadmap - Copilot-admin för SPS-regression

Detta roadmap-dokument beskriver hur SPS-repositoryt ska utvecklas till en administrerbar kontrollmiljö runt Copilot CLI, dokumentstyrda regressionstester, delad browser-session och en Docker-hostad backend/frontend.

## Målbild

Användaren ska kunna arbeta i samma grundflöde som idag, men med ett kompletterande administrativt lager som gör det lättare att:

- starta definierade regressioner
- välja miljö, roll och DS-scope
- visa loggar
- visa rapporter
- visa Mermaid-grafen för testberoenden
- skicka standardiserade kommandon till Copilot
- arbeta mot Copilot i en stabil frontend-konsol i stället för att skriva direkt i det råa CLI-fönstret
- följa körstatus och historik

Den gemensamma målbilden är att webbgränssnittet ska kunna initiera standardiserade Copilot-kommandon, till exempel `kör regressionstest`, utan att Copilot körs inne i Docker. Kommandot ska i stället gå via en Windows host runner till en runner-ägd Copilot CLI-session som startas från början genom `node-pty`. Därmed kan den synliga browsern, användarens inloggning, Copilot CLI och web control plane höra ihop samtidigt som runnern kan läsa output och skicka input utan Windows foreground, clipboard eller `SendKeys`.

## Teknisk POC-status 2026-08-27

`node-pty` är nu tekniskt bevisat som huvudspår för Copilot-admin:

- en synlig, gemensam Copilot CLI-session kan startas av runnern i ett eget fönster
- användaren kan skriva i samma fönster
- wrappern kan läsa användarinput och Copilot-output
- backend/agent kan skicka input asynkront via en lokal inputkö
- Copilot svarar i samma fönster
- admin-frontend har en tvåpanels AI-konsolen-yta: read-only transcript/output och separat inputruta som skickar till samma `node-pty`-session
- Copilot-motorns råa CLI-fönster är synligt som standard tills vidare, men frontend har en toggle som kan starta motorn dolt genom `hidden_window`
- backend- och host-runner-helperprocesser ska köras dolt; de är inte användarytor
- konsolens transcript hämtas med cursor-baserad polling och heartbeat-metadata, så långkörande sessioner kan följas utan att frontend läser om hela transcriptet
- Copilot-frågor som katalogtrust eller inloggning kan detekteras som `user_input_required` i stället för att feltolkas som häng
- real visible control-plane E2E har passerat med singleton-reuse: befintlig Copilot- och browser-session återanvändes utan att nya fönster öppnades
- standardpolicy för ny Copilot-session är `gpt-5-mini`, `/allow-all` och session-only folder trust-godkännande när Copilot frågar

Kända POC-begränsningar som ska hanteras i implementationen:

- sessionen måste startas genom node-pty-wrappern från början
- ren restart kräver att tidigare wrapperprocess/fönster upptäcks, stängs och verifieras; normal start ska i första hand återanvända en fungerande host-runner-ägd session
- inputloggning får bara användas som diagnostik eller med tydlig sekretesspolicy
- inputköfiler måste skrivas som UTF-8 utan BOM; Node-wrapperns `JSON.parse` avvisar BOM-prefixed JSON och strict real-E2E ska fånga detta
- output innehåller terminalsekvenser och behöver normaliseras för webben
- jobbkön måste bli robustare än POC:ens enkla filkö
- browsern ska vara singleton: återanvänd första collaborative browser-fönstret och öppna nya flikar via debugporten för att undvika ny Microsoft-inloggning i nya Incognito/InPrivate-fönster

## Arkitekturprincip

Adminmiljön ska delas i tre delar:

1. **Docker frontend** för operatörs-UI, Mermaid, rapportvyer, lägesval och körknappar
2. **Docker backend** för API, jobblager, status, historik och pollingkontrakt
3. **Windows host runner** för browser, PowerShell, runtime-skript och runner-ägd Copilot CLI via `node-pty`

Detta är den viktigaste avgränsningen i hela roadmapen.

Docker får aldrig försöka äga Copilot CLI direkt. Docker-backend skickar asynkrona jobb till host runnern och läser tillbaka status/resultat.

## Asynkron kommandomodell

Alla kommandon mot Copilot ska vara asynkrona:

1. Frontend skickar en åtgärd till backend.
2. Backend skapar ett jobb med `job_id`, läge, kommandomall, status och tidsstämplar.
3. Backend skickar jobbet till Windows host runnern.
4. Host runnern köar input till den node-pty-ägda Copilot-sessionen och markerar jobbet som aktivt.
5. Host runnern läser transcript/state/loggar och uppdaterar jobbstatus.
6. Frontend pollar backend för status och visar en enkel statusdiod.
7. Frontend väntar inte synkront på Copilot-svar.

Minsta jobbstatusar:

| Status | Betydelse |
| --- | --- |
| `queued` | Jobbet är skapat men ännu inte skickat till Copilot. |
| `running` | Copilot arbetar eller väntar på ett känt delsteg. |
| `user_input_required` | Copilot väntar på mänsklig återkoppling, till exempel trust eller inloggning. |
| `completed_unopened` | Jobbet är klart och användaren har ännu inte öppnat resultatet. |
| `completed_opened` | Jobbet är klart och resultatet har öppnats i UI:t. |
| `failed` | Jobbet föll med tydligt fel och logg-/transcriptlänk. |

Statusdiod i frontend:

| Färg | Betydelse |
| --- | --- |
| Röd | Inget jobb körs och inget oöppnat resultat finns. |
| Gul | Minst ett jobb är `queued`, `running` eller `user_input_required`. |
| Grön | Det finns ett `completed_unopened` jobb som användaren inte har öppnat. |

När användaren öppnar resultatet ska backend markera jobbet som `completed_opened`; om inget annat jobb är aktivt återgår dioden till röd.

## Praktisk målprocess

Den tänkta operatörsprocessen är:

1. Användaren öppnar SPS-repositoryt på Windows-värden.
2. Host runnern återanvänder befintlig node-pty-ägd Copilot CLI-session, eller startar exakt en ny session om ingen körs.
3. Användaren väljer i frontend om Copilot-motorfönstret ska vara synligt eller dolt; standard är synligt tills vidare.
4. Host runnern sätter ny Copilot-session till `gpt-5-mini`, aktiverar `/allow-all` och godkänner aktuell katalogtrust för sessionen när Copilot frågar.
5. Användaren eller Copilot återanvänder den synliga samarbetsbrowsern; nya arbetsytor öppnas som flikar i samma fönster.
6. Användaren startar Windows host runnern, eller låter host runnern starta node-pty-sessionen kontrollerat.
7. Användaren startar Docker-control-plane och öppnar dess webbsida.
8. Användaren använder webben för status, rapporter, Mermaid-graf, lägesval, AI-konsolen och standardiserade asynkrona åtgärder.
9. När användaren klickar på exempelvis `kör regressionstest` ska control plane skapa ett asynkront jobb som host runnern skickar till samma node-pty-ägda Copilot CLI-session.

Copilot CLI-terminalen, den synliga browsern och web control plane är alltså tre samverkande ytor. Web control plane ska vara primär användaryta för Copilot-input/output; den råa Copilot CLI-terminalen finns kvar som teknisk motor och felsöknings-/insynsyta men ska normalt inte användas för manuell textinmatning.

## Första containerfunktioner

Första Docker-baserade backend/frontend ska fokusera på fyra ytor:

| Yta | Funktion |
| --- | --- |
| Mermaid | Visa renderad beroendegraf från `testing\regression_test\regression-test-dependencies.mmd`. |
| Rapporter | Lista och öppna rapporter från `test_reports`, inklusive senaste körning och verifierade felrapporter. |
| AI-konsolen | Visa read-only Copilot-transcript, status, heartbeat och separat inputruta som skickar till samma `node-pty`-session. |
| Copilot-läge | Välja operativt läge: `learning mode` eller `testing mode`. |
| Regressioner | Starta alla regressionstester eller ett valt test via asynkront Copilot-jobb. |

Backend ska dessutom exponera health/status för:

- Docker backend
- Windows host runner
- node-pty Copilot-session
- senaste Copilot-output
- cursor-baserad Copilot-transcript polling för långkörande sessioner
- om Copilot väntar på användarinput
- senaste jobb och oöppnade resultat

## Första metadatamodell för regression och host-runner-jobb

Den första versionen ska använda en liten, explicit och maskinläsbar metadatamodell som backend kan skapa från `testing\regression_test\regression-test-catalog.md`, `testing\regression_test\regression-test-dependencies.mmd` och varje testfil. Modellen är ett kontrakt mellan frontend, backend och Windows host runner; den ersätter inte de mänskligt läsbara testdokumenten utan gör dem körbara från control plane.

### Regressionstest-identitet

Varje test som visas eller kan köras ska normaliseras till:

| Fält | Krav |
| --- | --- |
| `catalog_key` | Kort stabil referens från katalogen, till exempel `A`. Obligatoriskt för namngivna tester. |
| `test_id` | Unikt stabilt ID från testfilens `## Test-ID`. Obligatoriskt och ska vara kebab-case. |
| `summary` | Kort sammanfattning från katalogen. |
| `file_path` | Repositoryrelativ Windows-sökväg till testfilen, till exempel `testing\regression_test\serviceportal-nytt-kontrakt-migrated-ds.md`. |
| `test_type` | `ui-regression`, `structure-regression`, `report-review` eller framtida utökning. |
| `source_revision` | Git commit eller lokalt state-id när backend/runner kan ta fram det. |

Frontend ska visa `catalog_key`, `test_id`, sammanfattning och filväg i testlistan. Backend ska använda `test_id` som primär intern nyckel och `catalog_key` som användarvänlig genväg.

### Beroenden

Beroenden ska normaliseras till både nycklar och ID:n:

| Fält | Krav |
| --- | --- |
| `dependency_keys` | Lista med catalog keys som måste vara klara före valt test, exempelvis `["A"]`. |
| `dependency_test_ids` | Samma beroenden uppslagna till `test_id`. |
| `dependency_mode` | `required`, `recommended` eller `none`. För nuvarande katalog är UI-flödesberoenden `required`; strukturtester är `none`. |
| `start_state` | Kort text om vilket slutläge föregående test måste lämna efter sig, exempelvis inloggad serviceportal eller checkout-sida. |

Backend ska validera att varje beroende finns i både katalogen och Mermaid-grafen. Frontend ska visa beroenden som länkar och varna innan ett valt test körs utan sina `required`-beroenden.

### Körläge

Control plane ska skilja tydligt mellan modelläge och jobbtyp:

| Fält | Tillåtna värden | Betydelse |
| --- | --- | --- |
| `mode` | `learning`, `testing` | `learning` används för att utveckla/uppdatera testdefinitioner utan rapport i `test_reports`; `testing` används för faktisk regression med rapportering. |
| `job_type` | `set-mode`, `run-regression`, `review-report` | Vad host runnern ska skicka till Copilot. |
| `report_policy` | `forbidden`, `required_on_pass_or_verified_failure`, `read_only` | `learning` ger `forbidden`; `testing` ger `required_on_pass_or_verified_failure`; rapportgranskning ger `read_only`. |

Frontend ska visa aktuell `mode` i toppbaren och på regressionssidan. Backend ska avvisa regressionkörning om `mode` saknas eller inte är `learning`/`testing`.

### Miljö

Miljömetadata ska vara explicit för varje jobb:

| Fält | Exempel | Krav |
| --- | --- | --- |
| `environment.id` | `stage` | Stabil miljönyckel. |
| `environment.display_name` | `Stage` | Visningsnamn i UI. |
| `environment.base_urls` | `{"admin":"...","service_portal":"..."}` | Kända ingångar när de finns. |
| `environment.risk_level` | `safe-test`, `restricted`, `production` | Frontend ska visa risknivå; backend ska kunna blockera farliga kombinationer. |
| `environment.browser_required` | `true` | Anger om shared browser-session krävs. |

Första versionen får börja med `stage` som enda körbara miljö, men payloaden ska redan ha formen ovan så fler miljöer kan läggas till utan att ändra API-kontrakt.

### Roll och identitet

Rollmetadata ska beskriva vilken operativ identitet testet förutsätter utan att lagra hemligheter:

| Fält | Exempel | Krav |
| --- | --- | --- |
| `role.id` | `sps-admin-agent` | Stabil rollnyckel. |
| `role.display_name` | `SPS admin with assisted login access` | Visas i frontend. |
| `role.capabilities` | `["kundtjanstportal","assisted-login","serviceportal"]` | Backend matchar mot testkrav. |
| `role.login_model` | `shared-browser-manual-login` | Beskriver att användaren loggar in i synlig browser vid behov. |
| `role.secrets_policy` | `no-secrets-in-job-payload` | Jobbpayload får aldrig innehålla lösenord, tokens eller personliga autentiseringsuppgifter. |

Frontend ska visa vald roll och saknade capabilities innan körning. Host runnern ska bara få rollnyckel och instruktion, inte credentials.

### DS-scope

DS-scope ska göra datavalet tydligt för test som använder `Admin -> Migrate DS` eller serviceportalens parkeringssökning:

| Fält | Tillåtna värden/exempel | Krav |
| --- | --- | --- |
| `ds_scope.kind` | `none`, `migrated`, `non-migrated`, `specific-ds`, `any-valid` | Obligatoriskt. Strukturtester använder `none`. |
| `ds_scope.selection_policy` | `document_candidate`, `discover_during_run`, `fixed` | Anger om testet har dokumenterad kandidat eller om agenten ska välja vid körning. |
| `ds_scope.required_status` | `Migrated`, `Not Migrated`, `null` | Matchas mot testets syfte. |
| `ds_scope.allowed_ds_ids` | `["47184"]` eller tom lista | Endast vid låst urval. |
| `ds_scope.record_selection` | `true` | UI-regressioner ska dokumentera vilket DS som valdes. |

Backend ska varna om ett DS-drivet test saknar DS-scope. Frontend ska visa DS-scope i testdetaljen och i kördialogen.

### Standardiserade kommandomallar

Alla Copilot-kommandon ska byggas från mall-ID, metadata och säkra parametrar. Första versionen ska stödja:

| `command_template_id` | Syfte | Promptmall |
| --- | --- | --- |
| `run-regression-all` | Kör alla befintliga regressionstester i Regression Mode. | `Kör befintliga regressionstester i Regression Mode enligt testing\regression_test\regression-test-catalog.md. Följ beroenden, skapa rapport under test_reports endast när utfallet är passerat eller ett fel är verifierat, och uppdatera testfall med återanvändbara lärdomar efter UI-körning.` |
| `run-regression-selected` | Kör ett valt test och dess nödvändiga beroenden i Regression Mode. | `Kör regressionstest {catalog_key} ({test_id}) i Regression Mode. Läs katalog, beroendegraf och testfil. Säkerställ required dependencies: {dependency_keys}. Använd miljö {environment_id}, roll {role_id} och DS-scope {ds_scope}. Rapportera enligt tools\docs\regression-rapportering.md.` |
| `enter-learning-mode` | Sätt Copilot i Learning Mode för ett valt eller nytt test. | `Gå in i Learning Mode för regressionstest {catalog_key_or_new}. Uppdatera testdefinitioner, katalog och beroendegraf vid behov. Skapa ingen rapport i test_reports. Kör obligatoriska dokument-/beroendetester efter dokumentändringar.` |
| `enter-testing-mode` | Sätt Copilot i Testing Mode utan att starta körning direkt. | `Gå in i Testing Mode för befintliga regressionstester. Följ testing\regression_test\README.md, katalogen och rapporteringsreglerna. Vänta på valt testkommando om inget test anges.` |
| `review-report` | Läs och sammanfatta befintlig rapport utan ny regression. | `Granska rapport {report_id} i test_reports som read-only. Sammanfatta utfall, blockerare, verifierade fel och föreslagna nästa steg utan att ändra rapporten.` |

Host runnern ska logga både `command_template_id` och den renderade prompten. Backend ska spara mall-ID, parametrar och renderingstidpunkt. Frontend ska visa den mänskligt läsbara prompten innan jobbet skickas när läget kräver bekräftelse eller när risknivån är hög.

### Jobbpayload

Backend ska skapa jobb med denna minsta form:

```json
{
  "job_id": "job-20260827-105144-001",
  "trace_id": "trace-20260827-105144-001",
  "job_type": "run-regression",
  "mode": "testing",
  "command_template_id": "run-regression-selected",
  "status": "queued",
  "created_at": "2026-08-27T08:51:44Z",
  "created_by": "frontend",
  "selection": {
    "scope": "selected",
    "catalog_keys": ["B"],
    "test_ids": ["regression-serviceportal-nytt-kontrakt-migrated-ds"],
    "include_dependencies": true
  },
  "environment": {
    "id": "stage",
    "risk_level": "safe-test",
    "browser_required": true
  },
  "role": {
    "id": "sps-admin-agent",
    "capabilities": ["kundtjanstportal", "assisted-login", "serviceportal"],
    "login_model": "shared-browser-manual-login"
  },
  "ds_scope": {
    "kind": "migrated",
    "selection_policy": "discover_during_run",
    "required_status": "Migrated",
    "record_selection": true
  },
  "validation": {
    "dependency_policy": "require-ready-or-include",
    "report_policy": "required_on_pass_or_verified_failure"
  },
  "rendered_prompt": "Kör regressionstest B ...",
  "result": {
    "report_id": null,
    "summary": null,
    "opened_at": null
  }
}
```

Payloaden får inte innehålla lösenord, cookies, tokens, personnummer utöver sådant som redan står i ett testdokument, eller annan hemlig sessionsdata.

### Valideringsregler

Backend ska validera innan jobb skapas:

1. `test_id` är unikt och finns i testfil, katalog och eventuell vald testlista.
2. `catalog_key` finns i katalogen och Mermaid-grafen.
3. Alla `dependency_keys` går att slå upp och saknar cykliska beroenden.
4. `mode` är `learning` eller `testing`.
5. `learning` får inte ha rapportpolicy som skriver till `test_reports`.
6. `testing` måste ha rapportpolicy enligt `tools\docs\regression-rapportering.md`.
7. `environment.id` finns i miljöregistret och är tillåtet för valt test.
8. `role.capabilities` täcker testets krav.
9. DS-drivna tester måste ha `ds_scope.kind` annat än `none`; strukturtester ska ha `none`.
10. `command_template_id` måste vara känd och alla platshållare måste kunna renderas.
11. Jobbpayload får inte innehålla hemligheter eller privata autentiseringsvärden.

Host runnern ska validera mottagen payload defensivt igen innan prompten köas till node-pty-sessionen. Om validering fallerar ska jobbet markeras `failed` med maskinläsbar orsak och utan att prompt skickas.

### Frontend- och backendanvändning

Frontend ska använda metadata för att:

- visa testlista med nyckel, ID, sammanfattning, beroenden, miljökrav, rollkrav och DS-scope
- rendera beroenden i både tabell och Mermaid-vy
- visa aktuell `learning`/`testing`-mode och rapportpolicy
- förhandsvisa standardprompten för kör alla, valt test, mode-byte och rapportgranskning
- visa varningar för saknade beroenden, fel roll, riskfylld miljö eller DS-scope som inte matchar testet
- länka klart jobb till rapport, testfil och transcript/logg

Backend ska använda metadata för att:

- bygga `GET /api/regression/tests` som maskinläsbar katalog
- bygga `GET /api/regression/mermaid` och kontrollera synk mot katalogen
- skapa och validera jobb för `POST /api/copilot/mode` och `POST /api/regression/run`
- rendera rätt kommandomall med samma `trace_id` som övriga loggar
- blockera eller varna vid otillåten miljö/roll/DS-kombination
- ge host runnern en komplett men sekretesssäker payload

Host runnern ska använda metadata för att:

- starta eller verifiera nödvändig shared browser när `environment.browser_required` är `true`
- skicka renderad prompt till den node-pty-ägda Copilot-sessionen
- märka transcript, loggar och resultat med `job_id`, `trace_id`, `test_id`, `mode`, `environment.id`, `role.id` och `ds_scope.kind`
- returnera status och resultatmetadata till backend utan att tolka hela regressionens sakutfall mer än nödvändigt

## Genomgående acceptanstester

Följande case ska kunna användas för att avgöra om arkitekturen fungerar praktiskt:

| Case | Acceptanskriterium |
| --- | --- |
| Lära Copilot ett nytt test | Användaren kan välja Learning Mode i control plane, få ett standardiserat Copilot-kommando och Copilot uppdaterar testdefinition/katalog utan att skapa rapport i `test_reports`. |
| Visa Mermaid-beroenden | Webben kan visa renderad graf från `testing\regression_test\regression-test-dependencies.mmd` via host runnern. |
| Följa testning i webbfönster | Webben visar aktivt test, status, vänteläge, senaste loggrad och länkar till rapport/felrapport utan att användaren behöver läsa all terminaloutput. |
| Gemensam browser för inloggning | Användaren kan logga in i den synliga browsern och Copilot kan fortsätta styra/läsa samma session via debug-port. |
| Starta regression från webben | En knapp i webben kan skapa ett asynkront jobb som hamnar i rätt node-pty-ägda Windows-/Copilot-kontext, inte i en isolerad Docker-session. |
| Statusdiod | Dioden är röd utan aktivt/oöppnat jobb, gul under arbete eller `user_input_required`, och grön när ett klart jobb ännu inte öppnats. |

## User stories för första färdiga version

Första färdiga versionen är inte klar förrän dessa user stories är implementerade, testade och verifierade i E2E:

| User story | Verifieringskrav |
| --- | --- |
| Som en användare kan jag starta upp adminverktyget. | Ett dokumenterat runtime-kommando startar backend, frontend och nödvändiga host-runner-delar. Frontend öppnas eller visar URL. Backend health är OK. |
| Som en användare startar adminverktyget automatiskt ett gemensamt synligt Copilot-fönster och en Copilot-session. | Startflödet startar node-pty-wrappern, state visar Copilot-session `running`, och fönstret är synligt för användaren. |
| Som en användare startar adminverktyget automatiskt ett gemensamt synligt webbfönster där jag och Copilot kan arbeta tillsammans. | Startflödet startar collaborative browser via befintlig runtime, backend visar browserstatus och debug-port, och användaren kan logga in i samma fönster. |
| Som en användare kan jag se alla regressionstester i frontend och hur de hänger samman i ett Mermaid-diagram. | Frontend visar testkatalogen och renderad Mermaid från repositoryts riktiga regressionstestkälla. |
| Som en användare kan jag zooma, scrolla och panorera i ett mycket stort Mermaid-diagram. | Mermaid-vyn har zoom in/ut, pan, scroll, fit-to-screen, reset view och fungerar med hela beroendegrafen. |
| Som en användare kan jag sätta Copilot-sessionens status till `learning mode` eller `testing mode` från frontend. | Mode-väljaren skapar asynkront jobb, backend sparar valt läge och Copilot får motsvarande standardiserad instruktion. |
| Som en användare kan jag välja att genomföra regressionstestning från frontend. | Frontend skapar asynkront regressionstestjobb; backend returnerar direkt; statusdioden blir gul; Copilot får kommando via node-pty. |
| Som en användare kan jag välja vilken rapport jag vill läsa och få den snyggt formaterad i frontend. | Rapportlistan visar tillgängliga rapporter och rapportläsaren renderar vald Markdown-rapport med rubriker, metadata och läsbar layout. |

## Fleet-genomförande

Arbetet ska planeras så att flera agenter kan arbeta parallellt utan att blockera varandra. Varje agent ska äga ett tydligt kontrakt och får inte ändra andra agenters område utan samordning.

| Fleet-agent | Huvudansvar | Primära filer/områden | Klar när |
| --- | --- | --- | --- |
| Roadmap/kontrakt | Arkitektur, API-kontrakt, testmatris och definition of done. | `tools\docs\road-map\copilot-admin-control-plane.md`, eventuell kompletterande docs under `tools\docs`. | Roadmapen beskriver implementation, loggning, E2E, API:er och ansvar tillräckligt för övriga agenter. |
| Backend/API | Containeriserad backend, jobbmodell, API:er och backendloggning. | Ny katalog under `tools\source` för control plane backend, runtime under `runtime\docker\copilot-admin`. | Backend kan startas, returnera data, skapa jobb och logga maskinläsbart. |
| Host runner | Stabil Windows-adapter runt node-pty och browserstart. | `tools\source\copilot_admin_runner`, `runtime\windows\copilot-admin`, root-wrappers. | Backend kan starta/statusläsa Copilot och browser via host runner. |
| Frontend/UX | Visuellt UI, Mermaid, rapportläsare, lägesval, jobbvy och frontendloggning. | Ny frontendkatalog under control plane-källan. | Alla user-story-flöden finns som UI med test hooks och trevlig layout. |
| E2E/observability | E2E-svit, kritisk täckningsanalys, loggkorrelation och DoD-verifiering. | Testkatalog för control plane, runtime-testkommandon, dokumenterad E2E-matris. | Alla user stories är verifierade och brister är dokumenterade eller fixade. |

Rekommenderad parallell ordning:

1. Roadmap/kontrakt låser API- och loggkontrakt.
2. Backend och host runner bygger parallellt mot kontraktet.
3. Frontend bygger mot mockad backend och växlar sedan till riktig backend.
4. E2E-agenten bygger först mockade tester, därefter riktiga host-runner-tester.
5. Alla agenter kör relevanta tester och rapporterar blockerare innan sammanslagning.

## Backend-API för första versionen

Backend ska exponera stabila HTTP/JSON-API:er. Exakta paths får justeras vid implementation, men funktionerna är obligatoriska.

| API | Syfte |
| --- | --- |
| `GET /api/health` | Backend health, version, uptime och konfiguration. |
| `GET /api/status` | Samlad status för backend, host runner, Copilot-session, browser-session och statusdiod. |
| `POST /api/session/start` | Startar eller säkerställer host runner, node-pty Copilot-session och collaborative browser. |
| `GET /api/session/copilot` | Returnerar Copilot-sessionens state, inklusive `running`, `user_input_required`, transcript-tail och senaste jobb. |
| `GET /api/session/browser` | Returnerar browser-sessionens state, debug-port och eventuell startinstruktion. |
| `GET /api/regression/tests` | Returnerar regressionstestkatalogen maskinläsbart. |
| `GET /api/regression/mermaid` | Returnerar Mermaid-källa och metadata för beroendegrafen. |
| `POST /api/copilot/mode` | Skapar asynkront jobb för `learning mode` eller `testing mode`. |
| `POST /api/regression/run` | Skapar asynkront jobb för att köra alla eller valda regressionstester. |
| `GET /api/jobs` | Listar jobb med filtrering på status, typ och tid. |
| `GET /api/jobs/{job_id}` | Returnerar jobbstatus, loggpekare, output-tail och resultatmetadata. |
| `POST /api/jobs/{job_id}/open` | Markerar ett klart jobb som öppnat och uppdaterar statusdioden. |
| `GET /api/reports` | Listar rapporter från `test_reports` med datum, status och typ. |
| `GET /api/reports/{report_id}` | Returnerar rapportinnehåll som renderbar Markdown/HTML-data och metadata. |
| `POST /api/frontend/events` | Tar emot frontendloggar som maskinläsbara event. |
| `POST /api/test/reset` | Test-/kontroll-API för E2E: återställer teststate i utvecklingsläge. |
| `POST /api/test/inject-host-state` | Test-/kontroll-API för E2E: simulerar host-runner-state när riktig Copilot inte ska användas. |

Test-/kontroll-API:er ska vara avstängda eller skyddade utanför utvecklings-/testläge.

## Host-runner-kontrakt för node-pty-spåret

Windows host runnern är den enda komponent som får äga lokala Windows-resurser: synligt Copilot CLI-fönster, `node-pty`-process, collaborative browser, PowerShell-runtime och åtkomst till SPS-repositoryt. Docker-backend betraktar runnern som en asynkron, idempotent adapter och får aldrig anta att ett lyckat HTTP-anrop betyder att Copilot-arbetet är klart.

### Transport och backend-interaktion

För första riktiga implementationen ska backend prata med host runnern över ett lokalt HTTP/JSON-kontrakt bundet till loopback eller ett uttryckligen konfigurerat privat host-interface. Transporten ska vara lätt att byta senare, men semantiken nedan ska vara stabil även om implementationen ersätts av named pipe, filkö eller annan lokal IPC.

Grundantaganden:

- Backend skapar `trace_id` och `job_id`; host runnern återanvänder dem i status, transcript och loggar.
- Alla muterande anrop ska vara idempotenta när samma `request_id` skickas igen.
- Backend skickar kommandon till runnern, men runnern äger faktisk processlivscykel och kan vägra riskabla eller inkonsistenta kommandon.
- Runnern svarar snabbt med accepterad/avvisad status; långkörande Copilot-arbete följs genom polling.
- Backend pollar runnern för session-, browser-, jobb- och transcriptstatus och normaliserar resultat till frontend-API:et.
- Transporten ska skyddas mot oavsiktlig nätverksexponering med bindning till localhost, explicit allowlist och ingen publik autentisering-by-default.

Minsta host-runner-endpoints:

| Endpoint | Syfte |
| --- | --- |
| `GET /runner/health` | Runnerstatus, version, repo-root, capabilities och starttid. |
| `POST /runner/session/start` | Säkerställer ren node-pty-ägd Copilot-session. |
| `POST /runner/session/stop` | Stoppar node-pty-wrappern och verifierar att process/fönster är stängda. |
| `GET /runner/session/status` | Returnerar Copilot-sessionens process-, PTY-, mode-, transcript- och väntestatus. |
| `POST /runner/browser/start` | Startar eller säkerställer collaborative browser via befintlig runtime. |
| `GET /runner/browser/status` | Returnerar browserprocess, debug-port, profilkatalog och startfel. |
| `POST /runner/copilot/input` | Köar standardiserad input till aktiv node-pty-session. |
| `GET /runner/copilot/transcript` | Returnerar transcript-tail eller intervall sedan offset/sekvensnummer. |
| `GET /runner/jobs/{job_id}` | Returnerar runnerns jobbstatus, resultatpekare, senaste output och felmodell. |
| `GET /runner/logs` | Returnerar JSONL-loggintervall filtrerat på tid, `trace_id`, `session_id` eller `job_id`. |

### Session start, stop och status

`POST /runner/session/start` ska ta:

| Fält | Krav |
| --- | --- |
| `request_id` | Idempotensnyckel för startförsök. |
| `trace_id` | Korrelations-ID från backend/frontend. |
| `repo_root` | Förväntad SPS-root, normalt `C:\Copilot_projects\sps`. |
| `profile` | Exempelvis `default`, `test` eller annan framtida runnerprofil. |
| `clean_start` | Om `true`: upptäck befintlig wrapper, stoppa den och verifiera ren ny session. |
| `visible_window` | Ska vara `true` för ordinarie adminflöde. |
| `initial_mode` | Valfritt: `learning`, `testing` eller `unset`. |

Svaret ska minst innehålla `accepted`, `session_id`, `state`, `pid`, `window_title`, `started_at`, `capabilities`, `warnings` och eventuell `error`.

`POST /runner/session/stop` ska ta `request_id`, `trace_id`, `session_id`, `reason` och `timeout_ms`. Runnern ska försöka stänga kontrollerat, därefter rapportera `stopped`, `blocked` eller `failed`. Om fönster/process inte kan stängas säkert ska status bli `blocked` och backend får inte starta en ny session ovanpå den gamla.

`GET /runner/session/status` ska returnera:

- `state`: `not_started`, `starting`, `running`, `stopping`, `stopped`, `user_input_required`, `blocked`, `failed`
- `session_id`, `pid`, `pty_pid`, `window_title`, `started_at`, `last_activity_at`
- `current_mode`: `learning`, `testing` eller `unset`
- `active_job_id`
- `input_queue_depth`
- `transcript_seq`, `transcript_tail`, `last_output_at`
- `user_input_required`: boolean
- `user_input_reason`: `trust`, `login`, `confirmation`, `unknown` eller `none`
- `health`: `ok`, `degraded` eller `error`
- `error` enligt felmodellen nedan

### Browser start och status

`POST /runner/browser/start` ska ta `request_id`, `trace_id`, `repo_root`, `environment`, `visible_window`, `reuse_existing` och valfri `start_url`. Runnern ska använda `runtime\start-collaborative-stage-browser.ps1` som stabil entrypoint när stage-browsern behövs.

`GET /runner/browser/status` ska returnera:

- `state`: `not_started`, `starting`, `running`, `stopped`, `blocked`, `failed`
- `browser_id`, `pid`, `debug_port`, `profile_dir`, `start_url`
- `environment`, `last_checked_at`, `last_error`
- `user_visible`: boolean
- `requires_login`: boolean när runnern kan se att operatören behöver logga in manuellt

Browserstatus får inte innehålla cookies, tokens, persondata eller sidinnehåll utöver diagnostiska metadata.

### Copilot input-dispatch

`POST /runner/copilot/input` ska endast acceptera strukturerade kommandoobjekt, inte fri backendgenererad shell-exekvering.

Minsta inputfält:

| Fält | Krav |
| --- | --- |
| `request_id` | Idempotensnyckel för dispatch. |
| `trace_id` | Korrelation från frontend/backend. |
| `session_id` | Aktiv node-pty-session. |
| `job_id` | Backendjobb som inputen hör till. |
| `command_type` | Exempel: `set_mode`, `run_regression`, `update_regression_test`, `freeform_safe_prompt`. |
| `mode` | `learning`, `testing` eller `unset` när relevant. |
| `payload` | Strukturerad data, exempelvis test-ID, scope och promptmall-ID. |
| `rendered_input` | Den slutliga text som ska skickas till Copilot efter mallrendering. |
| `sensitivity` | `normal`, `contains_user_text` eller `diagnostic_only`. |
| `newline` | Om runnern ska avsluta input med Enter. |

Runnern ska validera att sessionen är `running`, att `session_id` matchar aktiv PTY och att `command_type` är tillåten. Vid accept ska runnern lägga input i PTY-kön och returnera `accepted`, `queued_at`, `input_seq` och uppdaterad jobbstatus `running`.

### Transcript och statuspolling

Transcript ska vara sekvensbaserat så backend kan polla utan att läsa om allt:

| Fält | Betydelse |
| --- | --- |
| `session_id` | Aktiv Copilot-session. |
| `from_seq` | Första önskade sekvensnummer. |
| `limit` | Max antal transcriptposter. |
| `include_ansi` | Bara `true` vid felsökning; webben ska normalt använda normaliserad text. |

Transcriptposter ska innehålla `seq`, `timestamp`, `stream` (`stdout`, `stderr`, `stdin`, `system`), `text`, `normalized_text`, `job_id`, `trace_id`, `is_user_input`, `redaction_applied` och valfri `markers`.

Runnern ska sätta `user_input_required=true` när transcript/status indikerar att Copilot väntar på trust, login, explicit confirmation eller annan mänsklig åtgärd. Det är ett vänteläge, inte ett fel, tills timeout eller operatörsavbrott inträffar.

### Jobb- och resultatstatus

Host-runner-status mappas till backendens jobbmodell enligt:

| Runnerstatus | Backendstatus | Kommentar |
| --- | --- | --- |
| `accepted` | `queued` | Input mottagen men inte skickad till PTY än. |
| `dispatched` | `running` | Input har skrivits till node-pty. |
| `active` | `running` | Copilot producerar output eller väntar inom normal körning. |
| `waiting_for_user` | `user_input_required` | Trust/login/confirmation kräver människa. |
| `succeeded` | `completed_unopened` | Resultat klart men inte öppnat i frontend. |
| `opened` | `completed_opened` | Backendstatus efter `POST /api/jobs/{job_id}/open`; runnern behöver bara logga detta om backend meddelar det. |
| `cancelled` | `failed` | Avbrutet jobb redovisas som failed med `error.code=cancelled`. |
| `timed_out` | `failed` | Timeout med transcript- och loggpekare. |
| `rejected` | `failed` | Validering eller policy stoppade dispatch. |
| `runner_error` | `failed` | Process-, PTY-, transport- eller runtimefel. |

Resultatmetadata ska minst innehålla `result_type`, `summary`, `report_path`, `artifact_paths`, `completed_at`, `opened_at`, `transcript_range` och `log_range`. Runnern skapar inte rapportstatusen `completed_opened`; det är en backend-/frontendmarkering.

### Felmodell

Alla runnerfel ska vara maskinläsbara:

| Fält | Krav |
| --- | --- |
| `code` | Stabil kod, exempelvis `session_not_running`, `session_conflict`, `browser_start_failed`, `input_rejected`, `copilot_timeout`, `user_input_timeout`, `transport_error`, `process_exit`, `permission_denied`, `invalid_request`, `internal_error`. |
| `message` | Kort operatörsläsbar text utan hemligheter. |
| `severity` | `info`, `warning`, `error`, `fatal`. |
| `retryable` | Boolean. |
| `user_action_required` | Boolean. |
| `details` | Strukturerad, sekretessgranskad metadata. |
| `trace_id` | Korrelations-ID. |
| `session_id` | När relevant. |
| `job_id` | När relevant. |
| `transcript_range` | När felet kan kopplas till terminaloutput. |
| `log_range` | Pekare till JSONL-loggar. |

Fel som kräver mänsklig handling men där sessionen är frisk ska i första hand bli `user_input_required`, inte `failed`. Exempel: Copilot ber användaren godkänna workspace trust eller logga in.

### JSONL-loggfält

Host runnern ska skriva JSONL med samma basfält som övrig observability och följande tillägg när relevant:

| Fält | Krav |
| --- | --- |
| `timestamp` | UTC ISO-8601. |
| `level` | `debug`, `info`, `warn`, `error`. |
| `component` | `host-runner`, `node-pty`, `browser`, `transport`, `runtime-script`. |
| `event` | Stabilt eventnamn. |
| `trace_id` | Korrelation genom frontend/backend/runner. |
| `session_id` | Aktiv Copilot-session. |
| `browser_id` | Aktiv browser-session när relevant. |
| `job_id` | Jobb-ID när relevant. |
| `request_id` | Idempotensnyckel från anropet. |
| `status` | Aktuell session-, browser- eller jobbstatus. |
| `seq` | Transcript- eller inputsekvens när relevant. |
| `pid` | Process-ID när relevant. |
| `duration_ms` | För avslutade operationer. |
| `error` | Felobjekt enligt felmodellen. |
| `details` | Strukturerad metadata utan hemligheter. |

Minsta runner-events är `runner_started`, `runner_health_checked`, `session_start_requested`, `session_started`, `session_stop_requested`, `session_stopped`, `browser_start_requested`, `browser_started`, `input_queued`, `input_dispatched`, `transcript_received`, `user_input_required_detected`, `job_status_changed`, `job_result_detected`, `runner_error` och `security_redaction_applied`.

### Säkerhetsbegränsningar

Detta kontrakt gör lokal automation kraftfull men inte isolerad:

- Runnern kör på Windows-värden med användarens rättigheter och ska betraktas som ett lokalt administrationsverktyg, inte som en säker multi-tenant-tjänst.
- Docker-backend får endast exponera kontrollerade kommandoobjekt; godtycklig shell, PowerShell eller clipboardstyrning ska inte ingå i kontraktet.
- Loggar och transcript kan innehålla känslig användarinput. Standardläge ska redigera eller utelämna hemligheter, tokens, cookies och persondata där de kan identifieras.
- Inputloggning av `rendered_input` ska kunna stängas av eller maskeras; diagnostikläge ska markeras tydligt.
- Browserstatus får inte exportera session cookies, lokal lagring, access tokens eller fullständigt sidinnehåll.
- Loopback-HTTP är bara acceptabelt för lokal utveckling/hostintegration. Om endpointen exponeras utanför localhost krävs explicit autentisering, auktorisation och nätverksbegränsning innan användning.
- Runnern ska blockera start om den upptäcker okänd befintlig wrapper/session i samma arbetsyta och inte kan verifiera ägarskap.
- Production/stage-policy ska hanteras av backend innan dispatch, men runnern ska ändå logga miljö och kunna avvisa uppenbart otillåtna riskkommandon.

## Frontend-layout och UX-krav

Frontend ska vara visuellt trevlig och tydlig nog för daglig drift. Första versionen ska ha:

- toppbar med produktnamn, aktuell miljö, Copilot-läge, host-runner-status och röd/gul/grön statusdiod
- vänsternavigation med Dashboard, Regressioner, Mermaid, Rapporter, Jobb och Loggar
- dashboard med kort för Copilot-session, browser-session, senaste jobb, senaste rapport och senaste fel
- Mermaid-sida med:
  - stor canvas
  - zoom in/ut
  - pan/drag
  - scroll
  - fit-to-screen
  - reset view
  - sök/filter för test-ID
  - tydlig loading/error-state
- Regressioner-sida med testlista, beroenden, kör alla och kör valt test
- Copilot-läge som tydlig växlare mellan `learning mode` och `testing mode`
- Rapporter-sida med lista, filter och snygg Markdown-rendering
- Jobbvy med status, timestamps, transcript-tail, logglänkar och öppna-resultat-knapp
- frontend test hooks, exempelvis `data-testid`, för samtliga user-story-kritiska kontroller

Frontend får aldrig anta att ett Copilot-jobb är klart bara för att HTTP-anropet som skapade jobbet lyckades. UI:t ska poll:a status-API:t.

## Uniform loggning och observability

All loggning ska vara maskinläsbar JSONL eller JSON-event med samma basfält:

| Fält | Krav |
| --- | --- |
| `timestamp` | UTC ISO-8601. |
| `level` | `debug`, `info`, `warn`, `error`. |
| `component` | Exempel: `frontend`, `backend`, `host-runner`, `node-pty`, `e2e`. |
| `event` | Stabilt eventnamn, exempelvis `job_created`. |
| `trace_id` | Skapas i frontend eller backend och följer hela flödet. |
| `session_id` | Aktiv admin-/Copilot-session. |
| `job_id` | Obligatoriskt för jobbrelaterade events. |
| `user_action` | Valfritt men rekommenderat för frontendhändelser. |
| `status` | Jobb-/sessionstatus när relevant. |
| `details` | Strukturerad metadata utan hemligheter. |

Obligatoriska frontend-events:

- `page_view`
- `api_request_started`
- `api_request_completed`
- `api_request_failed`
- `button_clicked`
- `mode_changed`
- `job_created`
- `job_opened`
- `report_opened`
- `mermaid_zoom_changed`
- `mermaid_pan_changed`
- `status_diode_changed`

Obligatoriska backend-/runner-events:

- `backend_started`
- `host_runner_health_checked`
- `copilot_session_start_requested`
- `copilot_session_started`
- `browser_session_start_requested`
- `browser_session_started`
- `job_created`
- `job_dispatched`
- `job_status_changed`
- `copilot_user_input_required`
- `job_completed`
- `job_failed`
- `frontend_event_received`

Loggarna ska vara felsökningsbara över hela kedjan: ett knapptryck i frontend ska kunna följas via samma `trace_id` till backendjobb, host-runner-dispatch, node-pty-input och resultat.

## E2E-strategi och kritisk testanalys

E2E-sviten ska innehålla både mockade och riktiga tester:

1. **Mockad snabb svit**: kör mot backend med simulerad host runner och verifierar UI, API, statusdiod och rapport-/Mermaid-rendering deterministiskt.
2. **Riktig host-runner-svit**: kör mot faktisk Windows host runner, node-pty-session och collaborative browser.
3. **Kritisk täckningsanalys**: dokumenterar vilka user stories som verifierats med riktig integration och vilka som endast är mockade.

Minsta E2E-matris:

| Test | Måste verifiera |
| --- | --- |
| `admin-startup` | Runtime/compose startar backend/frontend, health OK, dashboard synlig. |
| `copilot-window-startup` | Adminverktyget startar synligt node-pty Copilot-fönster och backend visar `running`. |
| `browser-window-startup` | Adminverktyget startar synlig collaborative browser och backend visar debug-port/status. |
| `mermaid-large-graph-navigation` | Alla regressionstester visas, Mermaid renderas, zoom/pan/scroll/reset fungerar. |
| `mode-learning` | Frontend väljer learning mode, asynkront jobb skapas, Copilot får instruktion, UI visar läge. |
| `mode-testing` | Frontend väljer testing mode, asynkront jobb skapas, Copilot får instruktion, UI visar läge. |
| `run-regression-async` | Frontend startar regression, HTTP-request returnerar direkt, statusdiod blir gul, jobb syns i jobblistan. |
| `job-completed-unopened` | När jobb är klart blir status `completed_unopened` och dioden grön. |
| `job-opened` | När användaren öppnar resultatet blir status `completed_opened`; dioden återgår till röd om inget annat jobb körs. |
| `report-reader` | Användaren väljer rapport och ser formaterad, läsbar rendering. |
| `user-input-required` | Copilot trust/login/confirmation visas som `user_input_required` och gul diod, inte som häng. |
| `frontend-logging` | Frontendhändelser skickas till backend och kan korreleras med backendloggar via `trace_id`. |
| `backend-frontend-log-correlation` | En user action kan följas från UI-event till backendjobb till host-runner-event. |

Arbetet är inte klart förrän E2E-agenten uttryckligen har svarat på:

- Täcker testerna varje user story?
- Är minst ett test kört mot riktig node-pty-session?
- Är minst ett test kört mot riktig collaborative browser?
- Finns det någon user story som bara är mockad?
- Visar loggarna vad som händer i frontend?
- Kan felsökare korrelera frontend, backend och runner med samma ID?
- Är Mermaid-vyn verifierad med ett stort diagram?
- Är asynkroniteten verifierad, alltså att frontend inte väntar på Copilot-resultat?

## Fas 1 - Normalisera dokument och metadata

### Mål

Göra nuvarande SPS-repo till tydlig primär källa för regressionstestning.

### Leverabler

- sammanslagen dokumentation från `sps-regression-server`
- en enhetlig modell för:
  - test-ID
  - beroenden
  - körläge
  - miljö
  - roll
  - DS-scope
- identifiering av vilka promptmallar och operatörskommandon som ska stödjas

### Utfall

En stabil informationsmodell som adminlagret kan bygga vidare på.

### Acceptanstest

- Testkatalogen, beroendegrafen och metadata kan läsas maskinellt.
- Minst ett Learning Mode-kommando kan genereras för ett valt test.
- Dokumentindexet passerar efter nya eller ändrade styrdokument.

## Fas 2 - Node-pty-baserad Windows runner och kommandobrygga

### Mål

Skapa ett host-side kontrakt som kan starta och äga Copilot CLI via `node-pty`, samtidigt som användaren kan använda samma synliga fönster.

### Leverabler

- Windows-runner för:
  - start av browser-session
  - start av runtime-skript
  - läsning av rapporter
  - start/stopp/verifiering av node-pty-ägd Copilot CLI-session
  - asynkron input till Copilot via PTY-kö
  - transcript/state för Copilot-output
- standardiserade kommandoobjekt för exempelvis:
  - `kör regressionstest`
  - `kör regressionstest A`
  - `gå in i learning mode`
  - `uppdatera regressionstest B`
- loggformat för körning, stdout/stderr, transcript, `user_input_required` och status
- ren start-logik:
  - upptäck befintlig wrapperprocess
  - avsluta och verifiera stängning
  - blockera om fönster/process inte stängs
- fallback-dokumentation för HTTP + bound-window om befintlig manuell Copilot-session måste användas

### Utfall

Control plane kan starta arbete utan att själv äga browsern eller köra Copilot i Docker. Windows runnern äger Copilot-sessionens PTY.

### Acceptanstest

- Host runnern kan returnera status, senaste rapport och Mermaid-källa.
- Host runnern kan skapa ett standardiserat kommando för `kör regressionstest` och `gå in i learning mode`.
- Host runnern kan starta node-pty-sessionen rent, läsa output och skicka input till samma fönster.
- `user_input_required` rapporteras när Copilot väntar på trust, inloggning eller bekräftelse.

## Fas 3 - Docker backend med asynkrona jobb

### Mål

Bygga backenddelen i containern som pratar med Windows host runnern och exponerar status till frontend.

### Leverabler

- containeriserad backend
- API för testkatalog, Mermaid-källa och rapportlista
- API för Copilot-sessionstatus
- API för jobb:
  - skapa jobb
  - lista jobb
  - hämta jobbstatus
  - hämta jobbresultat
  - markera resultat som öppnat
- intern jobblagring för `queued`, `running`, `user_input_required`, `completed_unopened`, `completed_opened` och `failed`
- adapter till Windows host runner
- pollingvänligt kontrakt för frontend

### Utfall

Frontend kan vara tunn och aldrig vänta synkront på Copilot-kommandon.

### Acceptanstest

- Backend returnerar Mermaid-källa och rapportlista från SPS-repot.
- Backend kan skapa ett jobb för `dra ett skämt i samma fönster` eller motsvarande ofarlig testprompt och se det slutföras via node-pty-state.
- Backend returnerar gul status medan jobbet kör och grön status när resultatet är klart men oöppnat.
- Backend markerar jobbet som öppnat när frontend begär resultat.

## Fas 4 - Första administrativa frontend

### Mål

Leverera ett minimalt men praktiskt gränssnitt för daglig användning.

### Leverabler

- startsida/dashboard med statusdiod
- Mermaid-sida med renderad regressionsgraf
- rapportsida för `test_reports`
- Copilot-lägessida med val mellan:
  - `learning mode`
  - `testing mode`
- regressionstest-sida med:
  - kör alla regressionstester
  - kör valt test
  - visa beroenden och förutsättningar
- enkel jobbvy med senaste output, status och länkar till rapporter

### Utfall

Operatören får en webbyta som kan se, välja och starta arbete utan att blockera på Copilot.

### Acceptanstest

- Webben visar testkatalog, senaste rapport och Mermaid-graf.
- Webben kan välja Copilot-läge och skapa rätt asynkront jobb.
- Webben kan starta regressionstest utan att vänta på resultat i samma HTTP-request.
- Statusdioden följer backendstatus: röd/gul/grön.
- Webben visar tydligt om Copilot väntar på manuell återkoppling i det synliga node-pty-fönstret.

## Fas 5 - Miljöer, roller och körpolicy

### Mål

Göra det möjligt att välja och validera rätt kontext före körning.

### Leverabler

- miljöregister
- roll-/identitetsregister
- DS-policyer
- tydlig märkning av production/stage
- regler för vilka tester som får köras var

### Utfall

Adminlagret blir säkrare och mindre beroende av manuell kunskap.

### Acceptanstest

- Användaren kan se vald miljö, roll och DS-scope innan körning.
- Production/stage-risker visas tydligt innan kommandon tillåts.
- Ett test kan spärras eller varnas om vald miljö/roll inte uppfyller dess policy.

## Fas 6 - Delat testbibliotek och synk

### Mål

Stödja återanvändbara testdefinitioner över flera installationer.

### Leverabler

- katalogmodell för delat testbibliotek
- import/synk till lokal körmiljö
- revisionshantering för testdefinitioner
- visning av lokala kontra delade versioner

### Utfall

Samma test kan underhållas centralt och användas lokalt med spårbar revision.

### Acceptanstest

- Lokal installation kan visa version/revision för ett test.
- Skillnad mellan lokalt test och delad version kan identifieras.
- Import eller uppdatering kräver tydlig bekräftelse och lämnar spårbar ändring.

## Fas 7 - Utökad analys och stödytor

### Mål

Komplettera den operativa körningen med bättre analys- och reviewstöd.

### Leverabler

- filtrerbar körhistorik
- bättre felsummering
- artefaktöversikt för rapporter och skärmdumpar
- sammanställning av återkommande felmönster
- eventuell AI-assisterad sammanfattning av körresultat

### Utfall

Plattformen blir ett faktiskt driftverktyg, inte bara en samling skript.

### Acceptanstest

- Användaren kan filtrera tidigare körningar och se återkommande felmönster.
- Felrapporter och artefakter kan öppnas från webben.
- Sammanfattning av senaste körning kan visas utan att öppna markdownfiler manuellt.

## Fas 8 - Avancerade framtidssteg

Följande är möjliga senare steg, men ska inte blockera de tidigare faserna:

- API-regressioner
- schemalagda körningar
- djupare security administration
- avancerad AI-planering
- AI-baserad visuell analys
- bredare multi-role-orkestrering

## Första rekommenderade implementation

Om arbetet ska börja direkt är den bästa första leveransen:

1. härda den node-pty-baserade Windows runnern från POC till stabil host runner
2. skapa Docker-backend med asynkron jobblagring och adapter mot host runnern
3. skapa Docker-frontend med:
   - Mermaid-graf
   - regressionsrapporter
   - Copilot-läge: `learning mode` eller `testing mode`
   - knapp för att köra regressionstester
   - röd/gul/grön statusdiod
4. lägga till första end-to-end-testet:
   - starta node-pty-session
   - skapa jobb från frontend/backend
   - skicka kommando till Copilot
   - pollad status blir gul
   - Copilot svarar/skapar resultat
   - status blir grön tills resultatet öppnas

Det ger hög nytta tidigt och passar den arbetsmodell som redan fungerar i praktiken.
