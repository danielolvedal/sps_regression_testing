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
- följa körstatus och historik

Den gemensamma målbilden är att webbgränssnittet ska kunna initiera standardiserade Copilot-kommandon, till exempel `kör regressionstest`, utan att Copilot körs inne i Docker. Kommandot ska i stället gå via en Windows host runner till en runner-ägd Copilot CLI-session som startas från början genom `node-pty`. Därmed kan den synliga browsern, användarens inloggning, Copilot CLI och web control plane höra ihop samtidigt som runnern kan läsa output och skicka input utan Windows foreground, clipboard eller `SendKeys`.

## Teknisk POC-status 2026-08-27

`node-pty` är nu tekniskt bevisat som huvudspår för Copilot-admin:

- en synlig, gemensam Copilot CLI-session kan startas av runnern i ett eget fönster
- användaren kan skriva i samma fönster
- wrappern kan läsa användarinput och Copilot-output
- backend/agent kan skicka input asynkront via en lokal inputkö
- Copilot svarar i samma fönster
- Copilot-frågor som katalogtrust eller inloggning kan detekteras som `user_input_required` i stället för att feltolkas som häng

Kända POC-begränsningar som ska hanteras i implementationen:

- sessionen måste startas genom node-pty-wrappern från början
- ren start kräver att tidigare wrapperprocess/fönster upptäcks, stängs och verifieras
- inputloggning får bara användas som diagnostik eller med tydlig sekretesspolicy
- output innehåller terminalsekvenser och behöver normaliseras för webben
- jobbkön måste bli robustare än POC:ens enkla filkö

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
2. Användaren startar den gemensamma Copilot CLI-sessionen via node-pty-wrappern, inte genom ett manuellt separat Copilot-fönster.
3. Användaren eller Copilot startar den synliga samarbetsbrowsern vid UI-testning.
4. Användaren startar Windows host runnern, eller låter host runnern starta node-pty-sessionen kontrollerat.
5. Användaren startar Docker-control-plane och öppnar dess webbsida.
6. Användaren använder webben för status, rapporter, Mermaid-graf, lägesval och standardiserade asynkrona åtgärder.
7. När användaren klickar på exempelvis `kör regressionstest` ska control plane skapa ett asynkront jobb som host runnern skickar till samma node-pty-ägda Copilot CLI-session.

Copilot CLI-terminalen, den synliga browsern och web control plane är alltså tre samverkande ytor. Web control plane ska inte ersätta Copilot CLI-terminalen; den ska administrera jobb, visualisera status och skicka standardiserad input till den runner-ägda sessionen.

## Första containerfunktioner

Första Docker-baserade backend/frontend ska fokusera på fyra ytor:

| Yta | Funktion |
| --- | --- |
| Mermaid | Visa renderad beroendegraf från `testing\regression_test\regression-test-dependencies.mmd`. |
| Rapporter | Lista och öppna rapporter från `test_reports`, inklusive senaste körning och verifierade felrapporter. |
| Copilot-läge | Välja operativt läge: `learning mode` eller `testing mode`. |
| Regressioner | Starta alla regressionstester eller ett valt test via asynkront Copilot-jobb. |

Backend ska dessutom exponera health/status för:

- Docker backend
- Windows host runner
- node-pty Copilot-session
- senaste Copilot-output
- om Copilot väntar på användarinput
- senaste jobb och oöppnade resultat

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
