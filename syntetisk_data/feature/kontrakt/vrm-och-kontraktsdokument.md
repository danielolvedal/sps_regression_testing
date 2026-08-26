# VRM och kontraktsdokument

## Dokument-ID

vrm-och-kontraktsdokument

## Syfte

Samlar funktioner för registreringsnummer, VRM-pooler, kontraktsdokument och mallar som är direkt knutna till kontrakt.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar VRM på kontrakt, VRM-pooler, dokumentgenerering och dokumentuppslag.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd – Teknisk & Jurid.txt`
- `raw_data\SPS_function_spec_en.xlsx`
- `raw_data\sps_vs_legacy_summary.md`

## Relaterade dokument

- `feature\kontrakt\andra-kontrakt.md`
- `feature\nycklar\nycklar-access-och-anpr.md`

## Funktioner i scope

- `Kontrakt\Lägg till/ta bort VRMer för ett kontrakt`
- `Kontrakt\Skapa kontrakt utfrån mall`
- `Admin\Skapa en ny VRM-pool för ett kontrakt`
- `Admin\Slå ihop VRM-poolerna för ett kontrakt`
- `Admin\Peka om ett kontrakt till en annan VRM-pool`
- `Admin\Se kontrakt på VRM-pool`
- `Admin\Hantera VRM-pooler på kund`
- `Dokument\Visa kontraktsdokument` (legacy)
- `Admin\Se dokumentsinformation` (legacy)

## Hur området fungerar

VRM är centralt både för avtal och access. Stage stödjer direkt uppdatering av VRM på kontrakt medan admin-menyn innehåller verktyg för mer avancerad poolhantering. Legacy tillför dessutom dokumentuppslag och dokumentmetadata, vilket gör det möjligt att koppla samman avtal, avisering och historiska dokument.

## Primära arbetsflöden

1. Uppdatera VRM på ett kontrakt
2. Bryt ut eller slå ihop VRM-pooler
3. Peka om kontrakt till annan pool vid omstrukturering
4. Skapa dokument från mall eller hämta existerande dokument

## Data, objekt och regler

- ett kontrakt kan ha flera VRM enligt funktionsmaterialet
- VRM-pooler verkar användas för samordning mellan flera kontrakt/kunder
- dokumentmallar används för kontraktspdf och sannolikt även avtalskommunikation

## UI, menyer och navigering

Stage har VRM-funktioner utspridda över `Kontrakt` och `Admin`. Legacy visar ytterligare dokumentfunktioner som inte syns i stage-menyn.

## Integrationer och beroenden

- access-/kamerasystem
- dokumentgenerering
- kund- och kontraktsregister

## Valideringar, fel och edge cases

- VRM-poolsammanslagning verkar uttryckligen svår att ångra
- dokumentfunktioner är mer synliga i legacy än i stage
- `Ej verifierat`: exakt skillnad mellan vanlig VRM-redigering och poolredigering

## Bilder och visuellt underlag

Saknas ännu.

## Kunskapsluckor / ej verifierat

- dokumentmodellen bakom kontraktsmallar
- exakt gräns mellan VRM-pool och kontraktsnivå

## Öppna frågor

- Behöver separat dokument tas fram för kontraktsdokument och avimetadata?
