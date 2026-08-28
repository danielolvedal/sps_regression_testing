# Regressionstest - arbetsmodell

Detta dokument fastställer hur en AI-agent ska tolka, hitta och köra regressionstester i SPS-repositoryt.

## Triggerord

Om användaren ber om att köra regressionstest och meddelandet innehåller ordet `regression` eller en uppenbar felstavning av samma ord, ska agenten tolka det som en begäran om regressionstestning.

Exempel:

- `kör regressionstest`
- `kör regressions test`
- `kan du köra regresionstest`
- `regresions test`

## Standardtolkning

Om inget annat specificeras ska agenten:

1. läsa `testing\regression_test\README.md`
2. läsa `testing\regression_test\regression-test-catalog.md`
3. identifiera relevanta regressionstester i `testing\regression_test`
4. avgöra vilket körläge som gäller
5. köra dokumenterade teststeg direkt i browser/session eller via relevanta runtime-skript

UI-regressioner ska i första hand vara **instruktionsstyrda** och ligga som dokumenterade testfall i markdown, inte som hårdkodad browserautomation. Det gör testningen robustare när UI, handlers eller navigationsmönster ändras.

## Körlägen

Det finns två explicita körlägen för regressionstestning:

- **Learning Mode** - används när syftet är att utveckla, prova, förbättra eller förstå själva testet
- **Regression Mode** - används när syftet är att köra ett befintligt test skarpt

## Learning Mode

Agenten ska gå in i `Learning Mode` när användaren signalerar att målet är att:

- utveckla ett test
- uppdatera ett test
- förbättra ett test
- prova om ett test fungerar
- lära sig hur testet bör utformas

Exempel på uttryck som normalt ska tolkas som `Learning Mode`:

- `uppdatera regressionstest B`
- `vi håller på att utveckla tester`
- `prova att köra testet och se om det fungerar`
- `kör B i learning mode`
- `test development`

I `Learning Mode` ska agenten:

1. fokusera på att göra testet bättre, tydligare och snabbare att köra nästa gång
2. tillåtas iterera, backa och prova alternativa kandidater
3. uppdatera testfallet med observationer, exekveringsgenvägar, beslutspunkter och kända risker
4. uppdatera `regression-test-catalog.md` om testets syfte, beroenden eller identitet ändras
5. **inte** skapa rapporter i `test_reports`

## Regression Mode

`Regression Mode` används när användaren vill köra ett befintligt test som faktisk verifiering av systemets beteende.

I `Regression Mode` ska agenten:

1. följa det dokumenterade testfallet
2. uppdatera testfallet med återanvändbara lärdomar
3. skapa eller uppdatera rapporter i `test_reports` enligt rapporteringsstandarden, men bara när rapportering är tillåten

## Osäkerhetshantering

Om det är oklart om användaren vill:

- köra befintliga regressionstester
- få dem beskrivna
- eller skapa nya

ska agenten fråga exakt:

`Ska jag köra befintliga regressionstester?`

Om det är tydligt att användaren vill arbeta med testutveckling snarare än skarp körning ska agenten inte fråga om detta först, utan gå direkt in i `Learning Mode`.

## Var testerna finns

- körbara entrypoints finns i `runtime`
- testbeskrivningar finns i `testing\regression_test`
- testidentiteter, sammanfattningar och beroenden finns i `testing\regression_test\regression-test-catalog.md`
- renderbar Mermaid-kod för testberoenden finns i `testing\regression_test\regression-test-dependencies.mmd`
- testrapporter från utförda körningar finns i `test_reports`
- styrande regler finns i `AGENTS.md`

## Körsätt per testtyp

- **Dokumentations-/strukturregressioner** körs via specifika runtime-skript, exempelvis:
  - `.\runtime\test-document-index.ps1`
  - `.\runtime\test-kallinventering-coverage.ps1`
- **UI-regressioner** körs genom att agenten läser ett dokumenterat testfall i `testing\regression_test` och utför stegen i den delade browser-sessionen.

Om en UI-regression blockeras av att den delade sessionen står på Microsoft-inloggning ska agenten vänta minst **5 minuter** så att användaren hinner logga in innan testet markeras som blockerat eller som misslyckad inloggning.

## Kunskapsfångst efter körning

Efter varje körd UI-regression ska agenten uppdatera det relevanta testfallet när ny återanvändbar kunskap upptäcks. Syftet är att nästa agent ska kunna köra samma test snabbare utan att återupptäcka UI-detaljer.

Följande typer av lärdomar ska dokumenteras när de bedöms stabila och återanvändbara:

- vilket sökfält, knapp-id eller UI-element som faktiskt användes
- vilka kandidatdata som fungerade eller bör undvikas
- vilka sektioner som är kollapsade som standard och måste öppnas först
- vilka redirects eller mellan-URL:er som uppstår innan slutmålet laddas
- när browsern kräver riktig user gesture för popup eller ny flik
- vilka inloggningsstopp som kräver explicit väntetid för att inte misstolkas som blockerande fel
- vilka felmönster som observerades under första försöken

## Standardsektioner för UI-regressioner

Ett UI-regressionstest bör utöver vanliga teststeg också innehålla:

- `Exekveringsgenvägar`
- `Tekniska observationer`
- `Senast verifierad körning`

Där sparas den praktiska kunskap som gör framtida körningar snabbare.

## Körbarhet från Copilot-admin frontend

Ett regressionstest visas under Copilot-admins menyval `Regressioner` när backendens `GET /api/regression/tests` kan läsa det från `testing\regression_test\regression-test-catalog.md`. Frontend ska alltså inte söka fritt efter markdownfiler; katalogen är det körbara API-kontraktet.

För att ett nytt test ska vara körbart från Copilot-admin frontend ska följande vara uppfyllt:

1. Testfilen ska ligga direkt under `testing\regression_test`.
2. Testfilen ska börja med `# Regressionstest - ...`.
3. Testfilen ska innehålla sektionerna `## Test-ID`, `## Catalog Key`, `## Summary`, `## Dependencies` och `## Typ`.
4. `Test-ID` ska vara stabilt kebab-case och unikt.
5. `Catalog Key` ska vara en kort stabil nyckel, till exempel `H`, och ska matcha katalogposten exakt.
6. `Summary` i testfilen och katalogen ska vara identisk efter whitespace-normalisering.
7. `Dependencies` ska lista beroenden med catalog key, eller `- none` när testet är fristående.
8. `testing\regression_test\regression-test-catalog.md` ska ha en tabellrad med samma `Catalog Key`, `Test ID`, `Summary` och filväg.
9. `testing\regression_test\regression-test-dependencies.mmd` ska ha en nod för testet och pilar för eventuella beroenden.
10. `dokument_index\index.md` ska referera till testfilen eftersom den är ett beständigt dokument.
11. `testing\regression_test\README.md` bör lista testet så människor hittar det utanför frontend.

Backend normaliserar katalograden till ett testobjekt med bland annat `catalog_key`, `test_id`, `summary`, `file_path`, `test_type`, `dependency_keys`, `dependency_test_ids` och `dependency_mode`. Frontend använder `test_id` när användaren klickar `Kör valt test`, men visar även `catalog_key` och `file_path` så att körbarheten går att felsöka.

Efter att ett test har lagts till eller ändrats ska agenten köra:

```powershell
.\runtime\test-regression-dependencies.ps1
.\runtime\test-document-index.ps1
```

Om testet ändå inte syns i Copilot-admin frontend ska felsökningen börja med att öppna den kanoniska modulen via backendens versionsstyrda route, till exempel:

```powershell
Start-Process 'http://127.0.0.1:8765/regressioner'
```

Backend ska då redirecta till senaste `/regressioner/<version>`. Kontrollera därefter katalog-API:t:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/api/regression/tests'
```

Om API:t visar testet men webben inte gör det ska adminfrontendens browserflik hårduppdateras. Om API:t inte visar testet kör backend sannolikt mot fel repository, gammal process eller gammal container och adminstacken ska startas om via `.\stop_tool.ps1` följt av `.\start_tool.ps1`.

## Synkregel för namngivna tester

När ett namngivet regressionstest skapas, tas bort, byter namn, får nytt `Catalog Key`, ny sammanfattning eller nya beroenden ska agenten uppdatera:

1. testfilen
2. `testing\regression_test\regression-test-catalog.md`
3. `testing\regression_test\regression-test-dependencies.mmd`

Därefter ska agenten köra:

```powershell
.\runtime\test-regression-dependencies.ps1
```

## Before Creating a Report

In `Regression Mode`, for a failed UI regression, the agent must verify the defect through at least three reproductions before creating a developer-facing report in `test_reports`.

If the defect is not yet triple-verified, the agent must:

1. update the regression test case with the observed behavior
2. keep verification work in the test documentation
3. avoid creating a failed-test report package

In `Learning Mode`, the agent must not create run reports at all, regardless of pass or fail.

## Viktig princip

När användaren säger `kör regressionstest` ska agenten inte utgå från att allt måste vara kodifierat. Agenten ska i stället förstå att regressionstester i detta repository kan vara:

- körbara skript för stabila strukturkontroller
- dokumenterade AI-/browserstyrda testinstruktioner för verkliga användarflöden

Efter körningen ska agenten också skapa eller uppdatera en rapport i `test_reports\YYYYMMDDvN` enligt rapporteringsstandarden, men endast i `Regression Mode` och endast för passerade eller verifierade fallerade tester.
