# Regressionstest - DS-routinginventering SPS vs legacy

Detta regressionstest skapar och håller uppdaterad en gemensam lista över samtliga kända DS, deras DS-nummer, namn och om `Skapa kontrakt - steg 1` routar vidare inom nya SPS-stage eller till legacy-stage.

## Test-ID

regression-ds-routing-inventory-sps-vs-legacy

## Catalog Key

`J`

## Summary

Build and maintain the shared DS routing inventory by collecting all DS numbers/names and classifying each DS as SPS-stage or legacy-stage through Create New Contract step 1.

## Dependencies

- none

## Typ

Manuellt/shared-browser-test med stöd av browser-debugging och endpoint-inventering i synlig Kundtjänstportal-session.

## Miljö

- Kundtjänstportalen stage: `https://sps-stage.europark.local/CustomerService`
- Nytt kontrakt steg 1: `https://sps-stage.europark.local/CustomerService/CreateNewContract`
- Garageöversikt: `https://sps-stage.europark.local/CustomerService/GarageOverviewSelect`
- Migrate DS: `https://sps-stage.europark.local/Migration`
- Legacy stage: `https://sps-stage-legacy.europark.local`

## Förutsättningar

- Synlig delad browser ska vara startad via `.\runtime\start-collaborative-stage-browser.ps1`.
- Användaren ska vara inloggad i Kundtjänstportalen.
- Agenten ska kunna läsa och styra samma browser-session via debug-port `9222`.
- Testet får inte skapa, ändra, avsluta, importera eller pusha kontrakt. Endast DS-uppslag och navigation till nästa steg i skapaflödet får göras.

## Syfte

Skapa en komplett och återanvändbar DS-routingbaseline för alla regressionstester som behöver välja test-DS. Listan ska visa vilka DS som fortfarande routar till legacy och vilka som stannar i nya SPS-stage, så att framtida testfall kan välja rätt kandidat utan att gissa.

Den viktiga gemensamma listan ska sparas här:

- `raw_data\ds-routing-inventory.json`

En AI-/människoläsbar sammanfattning ska sparas här:

- `syntetisk_data\common\ds-routing-index.md`

Andra regressionstester ska använda `raw_data\ds-routing-inventory.json` som maskinläsbar källa när de behöver välja DS-kandidater. Testdokument får länka till `syntetisk_data\common\ds-routing-index.md` för snabb översikt, urval och kända avvikelser.

## Viktig källbegränsning

`Admin -> Migrate DS` (`/Migration`) innehåller inte alla DS. Den visar migrationsrelaterade DS från legacy och saknar DS som är upplagda direkt i SPS. Den får därför **inte** användas som primärkälla för den kompletta DS-listan.

Migrate DS får bara användas som stöddata för att:

- identifiera DS som ingår i legacy-/migreringsspåret
- läsa migrationsstatus för DS som finns där
- jämföra mot den kompletta DS-listan och upptäcka vilka DS som bara finns via SPS-källor
- prioritera legacy-/migreringskandidater vid felsökning

Den kompletta listan måste byggas från Kundtjänst-GUI:ts DS-val i SPS-vyer, i första hand fuzzy-dropdownen där direkt upplagda SPS-DS faktiskt förekommer.

## Rekommenderad effektiv metod

Baslinjemetoden är att söka `001` till `999` i fuzzy-dropdownen under `Kontrakt -> Översikt av garage`, samla alla träffar, deduplicera och därefter klassificera varje DS i `Skapa kontrakt - steg 1`.

Agenten ska först analysera sidan för att hitta om fuzzy-dropdownen använder en intern autocomplete-/lookup-endpoint som kan anropas direkt med samma parametrar som UI:t. Om en sådan endpoint finns ska den användas i stället för långsamma manuella dropdown-klick, men den måste vara samma källa som Kundtjänst-GUI:ts DS-val och måste visa direkt upplagda SPS-DS.

Effektiv förstahandsordning:

1. Öppna `Kontrakt -> Översikt av garage` (`/CustomerService/GarageOverviewSelect`) och `Kontrakt -> Sätt upp nytt kontrakt` (`/CustomerService/CreateNewContract`).
2. Inspektera autocomplete-/dropdown-komponentens nätverksanrop, JavaScript-konfiguration och DOM för DS-lookup.
3. Om en DS-lookup-endpoint hittas:
   - anropa den för prefix `001` till `999`, eller med annan dokumenterad parameter som returnerar hela DS-mängden
   - samla alla dropdownträffar
   - verifiera stickprov i själva GUI:t
4. Om ingen endpoint hittas eller om endpointen verkar ofullständig:
   - använd den synliga fuzzy-dropdownen i `GarageOverviewSelect`
   - sök prefix `001` till `999`
   - samla alla synliga dropdownträffar
5. Använd även motsvarande DS-dropdown i `CreateNewContract` som coverage-kontroll om den skiljer sig från `GarageOverviewSelect`.
6. Använd `Admin -> Migrate DS` endast som kompletterande referenskälla och markera rader som även finns i migrationsvyn.
7. Extrahera minst:
   - `dsNumber`
   - `name`
   - källa, till exempel `garage-overview-dropdown`, `create-contract-dropdown`, `migration-reference`
   - migrationsstatus om DS även finns i Migrate DS
8. Deduplicera på normaliserat DS-nummer.

Om Migrate DS och SPS-dropdownkällorna ger olika DS-mängder är det väntat. DS som bara finns i SPS-dropdownen får inte filtreras bort; de är sannolikt direkt upplagda SPS-DS och är centrala för testets syfte.

## Klassificeringsregel

Varje DS i den deduplicerade listan ska klassificeras genom `Skapa kontrakt - steg 1`:

1. Öppna `https://sps-stage.europark.local/CustomerService/CreateNewContract`.
2. Ange DS-numret i fältet `Välj ett DS-nummer`.
3. Välj rätt DS i dropdownen om flera träffar visas.
4. Klicka `Nästa steg`.
5. Läs URL efter navigation.
6. Klassificera:
   - `sps-stage` om URL:en fortsätter under `https://sps-stage.europark.local`
   - `legacy-stage` om URL:en routas till `https://sps-stage-legacy.europark.local`
   - `not-found` om DS inte kan väljas eller inte ger någon giltig träff
   - `blocked` om session, behörighet, serverfel eller annat tekniskt hinder stoppar klassificeringen
7. Gå tillbaka till `CreateNewContract` och fortsätt med nästa DS.

Testet får köras i batchar. En batch får dock inte ersätta den gemensamma listan förrän den är komplett eller tydligt markerad som partiell.

## Rådataformat

`raw_data\ds-routing-inventory.json` ska vara ett JSON-dokument med denna struktur:

```json
{
  "schemaVersion": 1,
  "capturedAt": "2026-08-31T00:00:00+02:00",
  "environment": {
    "sourceBaseUrl": "https://sps-stage.europark.local",
    "legacyBaseUrl": "https://sps-stage-legacy.europark.local"
  },
  "sources": {
    "primary": "GarageOverviewSelect/CreateNewContract DS dropdown lookup",
    "fallback": "Visible fuzzy search 001-999",
    "migrationReference": "Migration/GetLegacyCarparksForTable"
  },
  "totals": {
    "sourceRows": 0,
    "uniqueDs": 0,
    "classified": 0,
    "spsStage": 0,
    "legacyStage": 0,
    "notFound": 0,
    "blocked": 0
  },
  "items": [
    {
      "dsNumber": "47184",
      "dsName": "Malmen 14, Möllevångsgatan 42 garage A",
      "migrationStatus": "Migrated",
      "existsInMigrationReference": true,
      "activeContractCount": 42,
      "inactiveContractCount": 550,
      "source": ["garage-overview-dropdown", "create-contract-dropdown", "migration-reference"],
      "createContractSearchTerm": "47184",
      "selectedDropdownText": "47184 Malmen 14, Möllevångsgatan 42 garage A",
      "routing": "sps-stage",
      "landingUrl": "https://sps-stage.europark.local/...",
      "classifiedAt": "2026-08-31T00:00:00+02:00",
      "notes": ""
    }
  ]
}
```

## Sammanfattningsformat

`syntetisk_data\common\ds-routing-index.md` ska innehålla:

- datum och källa för senaste inventering
- totalt antal unika DS
- antal `sps-stage`, `legacy-stage`, `not-found` och `blocked`
- tabell med minst `DS`, `Namn`, `Migration status`, `Routing`, `Landing URL`, `Kommentar`
- separat avsnitt för kandidater som är särskilt användbara i test, till exempel:
  - migrerade DS som stannar i SPS
  - migrerade DS som routar till legacy
  - DS med köpbar produkt eller kända platser
  - DS som bör undvikas i regressioner

## Teststeg

1. Starta eller anslut till delad stage-browser enligt förutsättningarna.
2. Öppna `https://sps-stage.europark.local/CustomerService`.
3. Om Microsoft-inloggning visas, låt användaren slutföra inloggningen och vänta minst **5 minuter** innan testet klassas som blockerat.
4. Hämta DS-listan via SPS-dropdownkällan i `GarageOverviewSelect` och/eller `CreateNewContract`.
5. Om en intern dropdown-endpoint finns ska den användas för prefixinsamling; annars ska den synliga fuzzy-dropdownen användas.
6. Sök prefix `001` till `999` och samla samtliga DS-träffar.
7. Hämta Migrate DS-listan via `/Migration/GetLegacyCarparksForTable` som referens, inte som komplett källa.
8. Om SPS-dropdownkällan misslyckas eller verkar ofullständig:
   - öppna `Kontrakt -> Översikt av garage`
   - sök fuzzy-prefix `001` till `999`
   - samla alla dropdownträffar
   - deduplicera på DS-nummer
9. Normalisera DS-listan:
   - trimma namn
   - behåll ledande nollor i DS-nummer om UI:t visar sådana
   - deduplicera på exakt DS-nummer
   - spara källor per DS
   - markera om DS även fanns i Migrate DS-referensen
   - markera DS som bara hittades i SPS-dropdownen som `sps-direct-candidate`
10. För varje DS:
   - öppna `Kontrakt -> Sätt upp nytt kontrakt`
   - ange DS-numret
   - välj matchande dropdownrad
   - klicka `Nästa steg`
   - klassificera routing enligt klassificeringsregeln
   - dokumentera landnings-URL och eventuell feltext
11. Spara komplett rålista till `raw_data\ds-routing-inventory.json`.
12. Skapa eller uppdatera `syntetisk_data\common\ds-routing-index.md`.
13. Uppdatera `dokument_index\index.md` om nya beständiga filer skapas.
14. Kör obligatoriska tester:
    - `.\runtime\test-document-index.ps1`
    - `.\runtime\test-kallinventering-coverage.ps1`
    - `.\runtime\test-regression-dependencies.ps1`

## Förväntat resultat

- Alla DS som kan hittas via Kundtjänst-GUI:ts SPS-dropdownar ska finnas i `raw_data\ds-routing-inventory.json`.
- DS som bara finns i Migrate DS men inte i SPS-dropdownarna ska inte användas för att begränsa listan, men ska dokumenteras som referensavvikelse.
- Listan ska normalt innehålla ungefär 500 eller fler unika DS-rader om stage-data är komplett.
- Varje DS ska ha DS-nummer, namn och routingklassificering.
- Alla framtida tester som behöver välja SPS- eller legacy-DS ska kunna använda listans `routing`-fält.
- `syntetisk_data\common\ds-routing-index.md` ska göra det lätt att välja testkandidater utan att läsa hela JSON-filen.

## Felutfall

Testet ska markeras som underkänt om något av följande inträffar:

- ingen DS-lista kan hämtas från Kundtjänst-GUI:ts SPS-dropdownar
- listan innehåller uppenbart för få DS utan dokumenterad orsak
- testet använder Migrate DS som enda källa för komplett DS-lista
- dedupliceringen tappar DS-nummer eller blandar ihop olika DS
- routingklassificering saknas för någon DS utan att raden är markerad `blocked` med orsak
- `raw_data\ds-routing-inventory.json` saknas efter en fullständig körning
- `syntetisk_data\common\ds-routing-index.md` saknas efter en fullständig körning
- dokumentindex eller källinventering inte uppdateras efter att rådata/syntetisk data ändrats

## Bevis / dokumentation

Dokumentera minst:

- kördatum och miljö
- om dropdown-endpoint, synlig fuzzy-dropdown, Migrate DS-referens eller flera källor användes
- antal råa källrader
- antal DS från SPS-dropdownkälla
- antal DS från Migrate DS-referens
- antal DS som bara finns i SPS-dropdownkälla
- antal DS som bara finns i Migrate DS-referens
- antal unika DS efter deduplicering
- antal klassificerade DS
- antal `sps-stage`, `legacy-stage`, `not-found` och `blocked`
- exempel på minst fem SPS-routade och fem legacy-routade DS om båda kategorier finns
- path till `raw_data\ds-routing-inventory.json`
- path till `syntetisk_data\common\ds-routing-index.md`

## Senast verifierad körning

- **Datum:** 2026-08-31
- **Körläge:** Regression Mode
- **Status:** Passed. Full körning skapade `raw_data\ds-routing-inventory.json` och `syntetisk_data\common\ds-routing-index.md`.
- **Utfall:** 999 prefix söktes via SPS-autocomplete, 8 211 råa dropdownrader deduplicerades till 2 348 unika DS, och alla 2 348 klassificerades utan `blocked` eller `not-found`.
- **Routingfördelning:** 136 `sps-stage`, 2 212 `legacy-stage`, 0 `not-found`, 0 `blocked`.
- **Referensjämförelse:** 1 959 DS fanns även i Migrate DS-referensen, 389 fanns bara i SPS-dropdownkällan och 5 fanns bara i Migrate DS-referensen.

## Återanvändbara körlärdomar

- Använd inte Migrate DS DataTables-endpointen som primärkälla för komplett DS-lista. Den innehåller migrerings-/legacyrelaterade DS och saknar DS som är upplagda direkt i SPS.
- Fuzzy-dropdownen i `GarageOverviewSelect` eller dess underliggande lookup-endpoint ska vara primärkälla, eftersom målet är samtliga DS som testare kan välja i Kundtjänst-GUI:t.
- `GarageOverviewSelect` och `CreateNewContract` använder samma autocomplete-konfiguration: `autocompleteAjaxPostRequest("#DS", "/CustomerService/GetCarParkDSNumbers")`. Endpointen ska anropas med POST och formfältet `input`, inte `term`.
- Prefixinsamling `001` till `999` via `/CustomerService/GetCarParkDSNumbers` gav 8 211 råa träffar och 2 348 unika DS vid körningen 2026-08-31.
- Migrate DS ska användas som referens för att markera legacy-/migreringsspår, inte för att utesluta direkt upplagda SPS-DS.
- Routing kan klassificeras utan att skapa kontrakt genom att POST:a `DS`, `GoogleMaps`, `FilterValue` och `__RequestVerificationToken` till `/CustomerService/CreateNewContract` med redirect avstängd. Location-headern visar om steg 2 ligger kvar i SPS-stage eller går till legacy-stage.
- Routing ska verifieras i `CreateNewContract`, inte antas från migrationsstatus. Ett DS kan vara `Migrated` men ändå routa eller blockera oväntat.
- Den färdiga listan är testinfrastruktur och ska behandlas som delad testdata, inte som körningsrapport.

## Relaterade dokument

- `testing\regression_test\regression-test-catalog.md`
- `testing\regression_test\regression-test-dependencies.mmd`
- `tools\docs\browser-samarbete-stage-session.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `tools\docs\raw-data-forandringsprocess.md`
