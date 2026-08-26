# SPS stage vs legacy - sammanfattning

Detta dokument sammanfattar en snabb regressionsjämförelse mellan:

- `https://sps-stage.europark.local/CustomerService`
- `https://sps-stage-legacy.europark.local/CustomerService`

Jämförelsen bygger på de sparade råinventeringarna i:

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`

## Funktioner som fungerar i legacy men inte i stage

- `\CustomerService\UpdateCpi` - fungerar i legacy, ger serverfel i stage
- `\Garage\BAInformationDS` - fungerar i legacy, ger serverfel i stage
- `\Key` - fungerar i legacy, ger serverfel i stage
- `\Scheduler` - fungerar i legacy, ger serverfel i stage
- `\CPS\FileImportList` - fungerar i legacy, ger 404/serverfel i stage

## Funktioner som finns i legacy men saknas som motsvarande funktion i stage

### Garage och administration

- `Administrera Område/zoner i ett garage`
- `Administrera platser i ett garage`
- `Administrera fysiska egenskaper för platser`
- `Administrera garageadresser`
- `Skapa hyresprodukter`
- `Hantera hyresprodukter`
- `Hantera tilläggsprodukter/tjänster`
- `Skapa tilläggsprodukter`
- `Sätt standardvärden per DS`
- `Aktiva pågående sessioner`
- `Pusha alla contract i ett DS till Park&GO`
- `API Response Check`
- `Se dokumentsinformation`

### Dokument, kö och rapporter

- `Visa kontraktsdokument`
- `Lägg till kund i kölista`
- `Standardmallar`
- `Förvaltarrapport`
- `Kundunderhållsrapport`
- `Noll-priskontrakt`
- `KPI-baserade kontrakt`
- `Procenthöjda kontrakt`
- `Produkttyper i ett DS`

## Samma funktion men olika namn eller placering

- `Verifieringskedja` i legacy motsvarar `Audit trail - Contract parking` i stage
- `SysDaemons` i legacy motsvarar `Running microservices and scheduled task` i stage
- `Uppdatera KPI` ligger under `Garage` i legacy men under `Gemensamma inställningar` i stage
- `Administrera fastighetsägare/hyresvärd/operatör för ett DS` ligger under `Garage` i legacy men under `Gemensamma inställningar` i stage
- STP-funktioner ligger under `Kontrakt` i legacy men under `STP-tjänster` i stage
- `Notification Templates` finns under `Templates` i legacy men både under `Templates` och `Gemensamma inställningar` i stage

## Språk och översättning

Allt är inte översatt till svenska. Både stage och legacy innehåller en tydlig blandning av svenska och engelska i menyer, sidtitlar och knappar.

Exempel:

- `Old Search Method`
- `Key Inventory`
- `Manage Key Types`
- `CarPark Key Settings`
- `Notification Templates`
- `API Users Settings`
- `Company Administrator`
- `Customers`
- `Audit`
- `Power BI Reports`
- `Running microservices and scheduled task`

## Slutsats

Legacy framstår som funktionellt rikare och stabilare på flera administrativa ytor. Nya stage har en renare och mer uppdelad struktur, men innehåller fler brutna funktioner och tydliga inkonsekvenser i både språk och benämningar.
