# Juridik, efterlevnad, ekonomi och integrationer

## Dokument-ID

juridik-efterlevnad-ekonomi-och-integrationer

## Syfte

Samlar de tvärgående regler och beroenden som påverkar flera funktioner: lagstiftning, kontraktstyper, moms/ekonomi, externa system och operativa beroenden.

## Status

Initial syntetisk modell baserad på konceptuellt källmaterial.

## Scope / avgränsning

Omfattar inte enskilda klickflöden utan de ramar som styr hur flera funktionsområden fungerar.

## Källor

- `raw_data\SPS Funktionsträd – Detaljerad Syst.txt`
- `raw_data\SPS Funktionsträd – Komplett System.txt`
- `raw_data\SPS Funktionsträd – Teknisk & Jurid.txt`
- `raw_data\SPS Funktionsträd – Utökad Specifik.txt`
- `raw_data\SPS_function_spec_en.xlsx`
- `raw_data\System & länkar.xlsx`
- `raw_data\ANPR.docx`

## Relaterade dokument

- `common\ordlista-och-namnstandard.md`
- `feature\kontrakt\prissattning-avisering-och-index.md`
- `feature\nycklar\nycklar-access-och-anpr.md`
- `feature\organisation\kunder-fastighetsagare-cps-tps.md`

## Funktioner i scope

- juridiska regler för kontrakt
- H/T/Q/R-kontrakt
- moms/avisering/bokföring
- externa integrationer och systemlandskap

## Hur området fungerar

Källmaterialet beskriver SPS som en avtals- och driftmotor där juridik och ekonomi är inbyggda i funktionerna. Svenska hyres- och arrenderegelverk påverkar kontraktets utformning, H/T-uppdelning påverkar moms och ekonomi, och flera externa system används för betalning, access, tillsyn och rapportering.

## Primära arbetsflöden

1. Välj korrekt affärsmodell och kontraktstyp
2. Säkerställ rätt moms-/ekonomilogik
3. Synka till externa system
4. Följ upp fel i loggar och driftverktyg

## Data, objekt och regler

- **Hyreslagen**: relevant för specifika parkeringsplatser/inomhus
- **Arrendelagen**: relevant för mark-/utomhusupplägg
- **H-kontrakt**: huvudhyresdel
- **T-kontrakt**: tilläggs- och servicelogik
- **Q-kontrakt**: kölogik
- **R-kontrakt/STP**: korttids- eller specialflöden
- **Konkluderant handlande / BankID**: två olika sätt att stödja avtalsingående

## UI, menyer och navigering

Tvärgående regler exponeras fragmentariskt i UI, exempelvis via prisändring, termination reasons, BC-koder, skattesatser, rapporter och adminverktyg.

## Integrationer och beroenden

- Business Central / Navision
- Svea
- EPMP
- HOJAB / Octavius
- Accessy
- Parakey
- Flowbird / Cale
- Power BI
- Active Directory

## Valideringar, fel och edge cases

- stage och legacy skiljer sig i tillgängliga verktyg för att hantera samma tvärgående regler
- flera engelska systemnamn behöver behållas oförändrade i dokumentation

## Bilder och visuellt underlag

Ej verifierat.

## Kunskapsluckor / ej verifierat

- detaljerade API-kontrakt
- full datamodell för ekonomisynk
- fullständig behörighetsmodell mellan systemen

## Öppna frågor

- Behöver ett separat integrationskatalogdokument skapas i syntetisk data, eller räcker `System & länkar.xlsx` som råkälla?
