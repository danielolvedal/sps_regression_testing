# Loggar, audit och drift

## Dokument-ID

loggar-audit-och-drift

## Syfte

Samlar loggning, audit trail, backendprocesser, schemaläggning och driftsövervakning i ett dokument för felsökning och driftmanualer.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar loggar, audit, process events, scheduler/daemon-status, API-responsverktyg och kontraktssynkloggar.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\sps_vs_legacy_summary.md`
- `raw_data\System & länkar.xlsx`

## Relaterade dokument

- `feature\rapporter\rapporter-och-powerbi.md`
- `crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`

## Funktioner i scope

- `Loggar\Oktavius valideringslogg`
- `Loggar\Kontraktssynkroniseringsloggar`
- `Loggar\Audit trail - Contract parking` / `Verifieringskedja`
- `Loggar\Backend Process Events`
- `Admin\Schemaläggaren`
- `Admin\Konfigurationer för schemalagda uppgifter`
- `Admin\Running microservices and scheduled task` / `SysDaemons`
- `Admin\API Response Check` (legacy)
- `Garage\Audit trail - Garage informations`
- `Produkt\Audit trail - Products and packages`

## Hur området fungerar

SPS har flera överlappande sätt att observera systemets beteende: audit trails för domänobjekt, synkloggar mot externa system, backendprocesslistor och driftstatus för mikrotjänster/schemalagda jobb. Legacy innehåller dessutom ett explicit API-responstestverktyg.

## Primära arbetsflöden

1. Identifiera funktionsproblem
2. Kontrollera relevant audit trail eller sync-logg
3. Kontrollera backendprocess/event eller scheduler
4. Kontrollera driftstatus för berörda tjänster
5. Dokumentera fel och eventuell stage/legacy-skillnad

## Data, objekt och regler

- audit trail finns på kontrakt, garage och produkter
- process events visar status, progress och färdigställande
- driftstatus visar tjänst, adress, port, heartbeat och senaste fel

## UI, menyer och navigering

Stage och legacy delar mycket här, men stage har brutna sidor för vissa driftverktyg:

- `Schemaläggaren` fungerar i legacy men inte i stage
- `Running microservices and scheduled task` i stage motsvarar `SysDaemons` i legacy

## Integrationer och beroenden

- Business Central
- EPMP
- Octavius
- interna mikrotjänster och schemalagda jobb

## Valideringar, fel och edge cases

- flera administrativa problem i stage går att bekräfta via jämförelse med fungerande legacy-sidor
- samma funktion kan ha olika namn i miljöerna

## Bilder och visuellt underlag

Saknas. Bör kompletteras med loggskärmbilder och driftöversikt.

## Kunskapsluckor / ej verifierat

- fullständig tolkning av varje backendjobb
- exakt ansvarsfördelning per mikrotjänst

## Öppna frågor

- Behöver driftverktyg delas upp i ett eget dokument skilt från audit/loggar?
