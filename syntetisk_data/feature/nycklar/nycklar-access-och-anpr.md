# Nycklar, access och ANPR

## Dokument-ID

nycklar-access-och-anpr

## Syfte

Samlar fysisk nyckelhantering, digital access, VRM-baserad access och ANPR/Park & Go i ett sammanhängande underlag.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar `Key Inventory`, nyckeltyper, DS-nyckelinställningar, ANPR/Park & Go och relaterade accessintegrationer.

## Källor

- `raw_data\ANPR.docx`
- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd – Teknisk & Jurid.txt`
- `raw_data\Uthyrning Upplärning.docx`

## Relaterade dokument

- `feature\kontrakt\vrm-och-kontraktsdokument.md`
- `feature\kontrakt\uppsagning-och-avslut.md`
- `crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`

## Funktioner i scope

- `Nyckelhantering\Key Inventory`
- `Nyckelhantering\Manage Key Types`
- `Nyckelhantering\CarPark Key Settings`
- ANPR/Park & Go-processer i källdokument

## Hur området fungerar

SPS hanterar både fysiska och digitala accessmedel. Legacy visar en fungerande nyckelinventarie medan stage för närvarande ger serverfel på samma sida. Funktionsträden beskriver även digital access via Accessy/Parakey och VRM/LPR-baserad access till bom- eller kamerasystem.

## Primära arbetsflöden

1. Registrera/klassificera nyckeltyp
2. Knyt nyckel- eller accessregler till DS
3. Dela ut nyckel eller digital behörighet
4. Vid avslut: följ upp återlämning och debitera vid utebliven retur
5. För ANPR: hantera in-/utfartslogik och betalningsflöde

## Data, objekt och regler

- nyckeltyper inkluderar exempelvis fjärrkontroll, fysisk nyckel, tagg eller kort
- VRM kan fungera som accessbärare i ANPR- eller LPR-scenarier
- utebliven nyckelretur kan medföra engångsavgift enligt utbildningsmaterial

## UI, menyer och navigering

Stage och legacy har samma huvudingångar men olika stabilitet:

- `Key Inventory` fungerar i legacy men är trasig i stage
- `Manage Key Types` fungerar i båda
- `CarPark Key Settings` fungerar som DS-baserad startvy

## Integrationer och beroenden

- Accessy
- Parakey
- EPMP
- Flow/EasyPark/Parkster
- Svea för fakturering vid utebliven betalning i ANPR-scenarier

## Valideringar, fel och edge cases

- stage: nyckelinventarie trasig
- ANPR-flöden innehåller flera betalvägar och fakturafallback
- `Ej verifierat`: exakt UI-samband mellan kontrakt, nyckelobjekt och digital accessgrupp

## Bilder och visuellt underlag

Saknas. Bör kompletteras med nyckelinventarie, nyckeltyper och ANPR-flödesskiss.

## Kunskapsluckor / ej verifierat

- fullständig modell för digital behörighetsprovisionering
- detaljerad relation mellan VRM-pooler och accessmotor

## Öppna frågor

- Ska ANPR/Park & Go brytas ut till ett eget syntetiskt dokument?
