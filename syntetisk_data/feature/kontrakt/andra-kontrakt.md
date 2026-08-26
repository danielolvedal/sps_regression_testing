# Andra kontrakt

## Dokument-ID

andra-kontrakt

## Syfte

Beskriver hur befintliga kontrakt identifieras och uppdateras samt vilka typer av ändringar som verkar stödjas.

## Status

Initial syntetisk modell, entrypoint verifierad i UI.

## Scope / avgränsning

Omfattar `Ändra ett kontrakt`, sökflöden och kontraktsöversikt i stage och legacy.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd.txt`
- `raw_data\SPS Funktionsträd – Utökad Specifik.txt`

## Relaterade dokument

- `feature\kontrakt\skapa-kontrakt.md`
- `feature\kontrakt\vrm-och-kontraktsdokument.md`

## Funktioner i scope

- `Kontrakt\Ändra ett kontrakt`
- `Kontrakt\Sök`
- `Kontrakt\Old Search Method`
- `Kontrakt\Översikt av garage`

## Hur området fungerar

Ändringsflödet utgår från kontraktsnummer eller sökning på kund/DS/VRM/dokument. Funktionsträden beskriver stöd för ändring av slutdatum, byte av parkeringsplats och översiktsvy med snabbkopiering av information.

## Primära arbetsflöden

1. Identifiera rätt kontrakt via sök eller kontraktsnummer
2. Öppna kontraktets redigeringsflöde
3. Justera avtalets detaljer, plats eller period
4. Säkerställ att följdeffekter för pris, VRM, dokument och access hanteras

## Data, objekt och regler

- kontraktsnummer är nyckelidentifierare i UI
- sökning kan ske på kund, DS, VRM och dokument
- ändringar kan påverka kopplade T-kontrakt och tillägg

## UI, menyer och navigering

Quick Search i stage visar tabeller med kontraktsnummer, kund, datum, pris, DS och kontaktdata. Legacy och stage har även en äldre sökvy som sannolikt används vid specialfall.

## Integrationer och beroenden

- ändringar kan kräva ny synk mot ekonomi- och accesssystem
- garageöversikten fungerar som sidoingång när ändringen berör plats/anläggning

## Valideringar, fel och edge cases

- samma kund kan ha flera kontrakt och flera platser
- uppsägning av en plats är inte alltid samma sak som uppsägning av hela avtalet
- `Ej verifierat`: exakt ändringsformulär efter “Nästa steg”

## Bilder och visuellt underlag

Saknas ännu.

## Kunskapsluckor / ej verifierat

- vilka ändringsfält som finns i steg 2+
- om alla ändringar loggas direkt i audit trail

## Öppna frågor

- Bör ändringsflödet delas upp i administrativa ändringar, kundändringar och platsändringar?
