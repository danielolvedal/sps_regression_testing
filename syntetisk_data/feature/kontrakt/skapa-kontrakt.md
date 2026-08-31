# Skapa kontrakt

## Dokument-ID

skapa-kontrakt

## Syfte

Beskriver hur kontrakt skapas i SPS, vilka objekt som väljs och vilken information som krävs för att flödet ska kunna dokumenteras som manual.

## Status

Initial syntetisk modell, steg 1 verifierad i UI.

## Scope / avgränsning

Omfattar framför allt `Sätt upp nytt kontrakt`, `Skapa nytt korttidsavtal` och närliggande flöden i stage och legacy.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\ds-routing-inventory.json`
- `raw_data\251203 Manual Hyra.apcoa.se.docx`
- `raw_data\SPS_function_spec_en.xlsx`
- `raw_data\SPS Funktionsträd – Utökad Specifik.txt`

## Relaterade dokument

- `lifecycle\kontraktets-livscykel.md`
- `feature\garage\garage-ds-setup-och-platser.md`
- `feature\produkter\produkter-paket-och-tillstandstider.md`

## Funktioner i scope

- `Kontrakt\Sätt upp nytt kontrakt`
- `Kontrakt\Skapa nytt korttidsavtal` (legacy)
- `STP-tjänster\Skapa nytt korttidsavtal` (stage)

## Hur området fungerar

Skapaflödet ser ut att börja med **val av DS/anläggning**. Därefter förväntas användaren välja parkeringsform, plats- eller paketalternativ och mata in kunduppgifter. Extern manual för hyra.apcoa.se visar dessutom att skapaflödet innefattar personnummer, namn, adress och aviseringsmetod.

`raw_data\ds-routing-inventory.json` är den aktuella verifierade källan för vilka DS som i stage går vidare i nya SPS-flödet respektive routas till legacy efter `Skapa kontrakt` steg 1. Den ska användas vid val av test-DS innan djupare kontraktssteg körs.

## Primära arbetsflöden

1. Välj DS eller anläggning
2. Välj plats-/produkt-/paketkonfiguration
3. Ange kunduppgifter
4. Ange startdatum och eventuellt aviserings-/betalningssätt
5. Slutför skapandet och distribuera kontraktsinformation

## Data, objekt och regler

- DS är första styrande objektet
- kontrakt kan enligt funktionsspec generera H- och T-delar i bakgrunden
- korttidsflöden använder R-/STP-logik
- digital kanal kan skicka kontrakt och inloggningsuppgifter via e-post

## UI, menyer och navigering

- stage: `Kontrakt > Sätt upp nytt kontrakt`
- legacy: samma, men STP-skapande ligger under `Kontrakt`
- första verifierade steget visar endast DS-val; djupare steg är ännu `Ej verifierat`

## Integrationer och beroenden

- kund- och kontraktsskapande påverkar avisering, ekonomi och access
- Serviceportalen/hyra.apcoa.se verkar använda samma grundmodell fast via kundgränssnitt

## Valideringar, fel och edge cases

- vissa anläggningar kan kräva särskilda villkor eller garagekommentarer
- STP- och långtidsflöden kan ha olika datakrav
- `Ej verifierat`: exakt valideringsordning efter steg 1

## Bilder och visuellt underlag

Inga bilder sparade ännu. Bör kompletteras med skärmbilder från steg 1, produktval och kunduppgiftssteg.

## Kunskapsluckor / ej verifierat

- fullständig steg-för-steg-sekvens inne i kontraktsguiden
- vilka fält som är obligatoriska per kontraktstyp

## Öppna frågor

- Behöver separata syntetiska dokument skapas för B2C, B2B och STP-onboarding?
