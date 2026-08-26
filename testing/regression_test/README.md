# Regressionstester

Den här katalogen ska innehålla testupplägg som säkerställer att tidigare fungerande flöden fortfarande fungerar efter förändringar.

Fokus:

- återkommande kärnflöden
- känsliga adminfunktioner
- rapport- och integrationsytor
- kända fel i stage som behöver följas upp över tid
- dokumentstyrning och indexkvalitet

## Aktiva regressionstester

- `regression-test-catalog.md` - huvudkatalog för namngivna regressionstester, deras sammanfattningar och beroenden, inklusive Mermaid-graf.
- `regression-test-dependencies.mmd` - fristående Mermaid-kod för regressionsflödenas beroenden; denna fil ska hållas synkad med katalogen och testfilerna.
- `kontrakt-sok-anna-serviceportal-login.md` - manuellt/shared-browser-test som verifierar kontraktssökning på Anna, att kontrakt öppnas i nya stage och att testet avslutas på kundens inloggade serviceportalsida via `Users -> Actions`.
- `serviceportal-nytt-kontrakt-migrated-ds.md` - manuellt/shared-browser-test som tar vid från slutläget i `A`, klickar på `Nytt kontrakt`, väljer ett DS med status `Migrated` via `Admin -> Migrate DS` och verifierar nytt kontrakt-flödet i serviceportalen.
- `serviceportal-checkout-verifiering-och-skapa-kontrakt.md` - manuellt/shared-browser-test som tar vid från slutläget i `B` och verifierar checkoutdata, priser, avgifter, avtalsgodkännande och kontraktsskapande.
- `serviceportal-nytt-kontrakt-non-migrated-ds.md` - manuellt/shared-browser-test som tar vid från slutläget i `A`, klickar på `Nytt kontrakt`, väljer ett DS som inte är migrerat via `Admin -> Migrate DS` och verifierar att en produkt kan köpas i serviceportalen.
- `document-index-coverage.md` - beskriver det obligatoriska testet som verifierar att alla beständiga dokument/datafiler finns i `dokument_index\index.md`.
- `kallinventering-coverage.md` - beskriver det obligatoriska testet som verifierar att `syntetisk_data\common\kallinventering.md` täcker aktuellt innehåll i `raw_data` och att påverkan spåras vidare till syntetiska dokument.
- `regression-dependency-coverage.md` - beskriver regressionstestet som verifierar att testmetadata, regressionskatalogen och den fristående Mermaid-filen är synkade.

## Testtyper

- **Instruktionsstyrda UI-regressioner**: agenten läser testfallet och utför stegen i delad browser-session.
- **Körbara strukturregressioner**: agenten kör specifika runtime-skript när testet är stabilt och inte känsligt för UI-förändringar.

## Körlägen

- **Learning Mode** - används när vi utvecklar, provar eller förbättrar testet självt. Då ska agenten uppdatera testdokumentationen men inte skapa rapporter i `test_reports`.
- **Regression Mode** - används när vi kör ett befintligt test som faktisk verifiering. Då gäller normal rapportering enligt `tools\docs\regression-rapportering.md`.

## Kunskapsåterföring

När ett UI-regressionstest körs och agenten lär sig något som gör nästa körning snabbare ska testfallet uppdateras. Varje viktigt UI-test bör därför innehålla:

- praktiska exekveringsgenvägar
- tekniska observationer som påverkar körningen
- en kort sektion för senast verifierad körning

För DS-drivna köp- eller kontraktsflöden gäller dessutom att en kandidat utan köpbar produkt eller ledig plats normalt ska dokumenteras och hoppas över, inte omedelbart klassas som ett regressionsfel.

Alla namngivna regressionstester ska dessutom hållas synkade mellan:

- respektive testfil
- `testing\regression_test\regression-test-catalog.md`
- `testing\regression_test\regression-test-dependencies.mmd`

## Testrapportering

Själva testrapporterna under `test_reports` ska skrivas på formell engelska.

En körning ska dokumenteras under `test_reports\YYYYMMDDvN` endast i `Regression Mode`, när utfallet är passerat eller när ett fel är verifierat.

Minimikrav:

- `summary.md` med en rad per test
- `RegressionErrorNN\report.md` för varje verifierat `failed`
- inget failed-test får rapporteras innan felet verifierats tre gånger

Om ett failed test ännu inte är trippelverifierat ska observationen stanna i testfallet tills verifieringen är klar.

Om körningen sker i `Learning Mode` ska observationen alltid stanna i testfallet och ingen rapport ska skapas i `test_reports`.

Full standard finns i `tools\docs\regression-rapportering.md`.

Rapporter under `test_reports` är körningsoutput och ska **inte** indexeras i `dokument_index\index.md`.

## Körbara strukturregressioner

```powershell
.\runtime\test-document-index.ps1
.\runtime\test-kallinventering-coverage.ps1
.\runtime\test-regression-dependencies.ps1
```

## Standardtolkning för AI-agenter

När en användare ber om att köra regressionstest ska agenten först läsa denna katalog och sedan välja rätt testtyp:

1. `testing\regression_test\regression-test-catalog.md` för att hitta rätt test och beroenden
2. relevanta markdown-baserade UI-testfall under `testing\regression_test`
3. relevanta runtime-baserade strukturtester under `runtime`

UI-regressioner ska som huvudregel **inte** hårdkodas som browserskript om syftet i stället kan uttryckas som stabila steg för agenten att utföra.

## Tolkning för AI-agenter

Om användaren skriver ett kommando eller önskemål som innehåller `regression` eller en uppenbar felstavning av ordet ska agenten tolka detta som en begäran om regressionstestning. Om avsikten är oklar ska agenten fråga:

`Ska jag köra befintliga regressionstester?`

Om användaren i stället tydligt signalerar att syftet är att utveckla, förbättra eller prova ett test ska agenten tolka detta som `Learning Mode`.
