# Prissattning, avisering och index

## Dokument-ID

prissattning-avisering-och-index

## Syfte

Samlar all syntetisk kunskap om prisjustering, KPI/CPI, avisering, moms och ekonomirelaterade kontraktsregler.

## Status

Initial syntetisk modell med delvis verifierade UI-entrypoints.

## Scope / avgränsning

Omfattar enskild prisändring, batchprisändring, KPI/CPI, moms/BC-koder och aviseringsprinciper.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd.txt`
- `raw_data\SPS Funktionsträd – Detaljerad Syst.txt`
- `raw_data\SPS Funktionsträd – Komplett System.txt`
- `raw_data\SPS_function_spec_en.xlsx`

## Relaterade dokument

- `feature\produkter\produkter-paket-och-tillstandstider.md`
- `crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`

## Funktioner i scope

- `Kontrakt\Ändra pris på ett kontrakt`
- `Garage\Ändra pris på flera kontrakt på ett DS`
- `Garage\Uppdatera KPI` (legacy)
- `Gemensamma inställningar\Uppdatera KPI` (stage)
- `Gemensamma inställningar\Skattesatser`
- `Gemensamma inställningar\BC-koder`

## Hur området fungerar

SPS verkar stödja både manuella och schemalagda prisändringar. I UI finns stöd för procentuell höjning, fast belopp, KPI-baserad höjning och nytt fast pris. Funktionsträden beskriver också momsseparation mellan H- och T-kontrakt, samavisering och nordiska aviseringsmetoder.

## Primära arbetsflöden

1. Identifiera kontrakt eller DS
2. Välj höjningsmetod
3. Ange datum, belopp eller KPI-år
4. Kontrollera moms- och BC-kodseffekter
5. Synka mot ekonomi och följ upp i loggar/processjobb

## Data, objekt och regler

- H-kontrakt kan vara momsfria eller momspliktiga beroende på upplägg
- T-kontrakt är enligt underlaget normalt momspliktiga
- KPI/CPI påverkar indexerade kontrakt och kan även köras batchvis
- aviseringsmetod och avgifter påverkar kundupplevelse och ekonomiutfall

## UI, menyer och navigering

Stage har separat sida för enskild prisändring och batchändring. Legacy har dessutom fungerande KPI-sida, medan motsvarande stage-sida för närvarande ger serverfel.

## Integrationer och beroenden

- Business Central/Navision
- Svea
- schemaläggare/backendprocesser

## Valideringar, fel och edge cases

- stage: `Uppdatera KPI` är trasig
- legacy: KPI-sidan visar historiska indexvärden och verkar fungera
- `Ej verifierat`: exakt samspel mellan BC-koder, produkttyper och prisändringsjobb

## Bilder och visuellt underlag

Saknas. Bör kompletteras med skärmbilder för prisändring, batchflöde och KPI-vy.

## Kunskapsluckor / ej verifierat

- exakt beslutslogik för när H/T delas upp i avisering
- fullständig lista över tillgängliga aviseringsmetoder i UI

## Öppna frågor

- Ska ekonomi/avisering få ett eget fördjupningsdokument utöver detta?
