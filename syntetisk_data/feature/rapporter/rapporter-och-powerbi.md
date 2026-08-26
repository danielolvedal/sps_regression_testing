# Rapporter och Power BI

## Dokument-ID

rapporter-och-powerbi

## Syfte

Ger en samlad modell för operativa rapporter, Power BI-rapporter och kända problem i rapportytan.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar både klassiska rapporter i legacy och Power BI-baserade rapporter i stage/legacy.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS---Rulla-ut-statistik-för-fastighetsägare.pdf`
- `syntetisk_data\kundtjanst-menykarta-legacy.md`
- `raw_data\sps_vs_legacy_summary.md`

## Relaterade dokument

- `feature\loggar\loggar-audit-och-drift.md`
- `common\ordlista-och-namnstandard.md`

## Funktioner i scope

- Power BI-rapporter under `Rapporter`
- legacyrapporter som `Förvaltarrapport`, `Kundunderhållsrapport`, `Noll-priskontrakt`, `KPI-baserade kontrakt`, `Procenthöjda kontrakt`, `Produkttyper i ett DS`

## Hur området fungerar

Rapportområdet består av två huvudtyper:

- **inbyggda operativa rapportvyer**, tydligast i legacy
- **Power BI-länkar**, tydliga i både stage och legacy

Legacy ger bredare täckning av operativa rapporter, medan stage i större grad fungerar som startyta för Power BI-containerlänkar.

Underlaget om statistik för fastighetsägare pekar dessutom på att rapportområdet inte bara är internt operativt, utan även används i kund- och fastighetsägarkommunikation.

## Primära arbetsflöden

1. Välj rapport utifrån affärsfråga
2. Om det är operativ rapport: kör direkt i sidan
3. Om det är Power BI: öppna rapportcontainer och validera att ReportID/workspace fungerar
4. Dokumentera eventuella trasiga länkar

## Data, objekt och regler

- vissa rapporter är DS-baserade
- vissa rapporter är kontrakts- eller prisbaserade
- Power BI-nycklar administreras via `Admin\PBI Reports`

## UI, menyer och navigering

Kända rapportproblem i både stage och legacy:

- `OP - 1A - Occupancy Rate Repot NEW`
- `SPS- 1F - Kontraktsöversikt med kontaktuppgifter`
- `Report to audit the payments and events from EPMP`
- `OP - 8D - Park & Go Statistik`
- `OP - 8xd - Park & Go beläggningsgrad`
- `OP - 7 - Uppföljning Kontrollavgifter`

## Integrationer och beroenden

- Power BI workspace/report-id
- underliggande SPS-data
- EPMP/ekonomi/kontrakt beroende på rapport

## Valideringar, fel och edge cases

- flera rapportnamn är delvis engelska
- Power BI-container kan öppnas även när rapporten bakom är trasig
- legacy innehåller rapporter som saknas helt i stage-menyn

## Bilder och visuellt underlag

Saknas. Bör kompletteras med exempel på fungerande och trasig rapportlänk.

## Kunskapsluckor / ej verifierat

- fullständig datadefinition per rapport
- ägarskap och ansvar per rapport

## Öppna frågor

- Ska operativa rapporter och Power BI delas upp i två dokument?
