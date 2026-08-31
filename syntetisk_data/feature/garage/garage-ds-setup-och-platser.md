# Garage, DS-setup och platser

## Dokument-ID

garage-ds-setup-och-platser

## Syfte

Normaliserar kunskapen om anläggningar, DS, zoner, platser, fysiska egenskaper, adresser och garagekommentarer.

## Status

Initial syntetisk modell med starkt stöd från legacy.

## Scope / avgränsning

Omfattar garage- och platsadministration i både stage och legacy, inklusive sådant som ännu bara är exponerat i legacy.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\ds-routing-inventory.json`
- `raw_data\DS Grundinformation Garagekommentarer.docx`
- `raw_data\Uthyrning Upplärning.docx`
- `raw_data\SPS Funktionsträd.txt`
- `raw_data\sps_vs_legacy_summary.md`

## Relaterade dokument

- `feature\produkter\produkter-paket-och-tillstandstider.md`
- `feature\kontrakt\skapa-kontrakt.md`

## Funktioner i scope

- skapa/ändra DS
- översikt av garage
- zoner, områden och våningsplan
- platser och fysiska egenskaper
- garageadresser
- betalautomater per DS
- BA-lager
- standardvärden per DS
- GK/garagekommentarer

## Hur området fungerar

DS verkar vara den grundläggande organisatoriska enheten för en anläggning. Legacy visar ett större operativt verktygsset för zoner, platser, adresser, hyresprodukter och standardvärden. Garagekommentarer fungerar samtidigt som ett viktigt kunskapslager för kundtjänst med både publik och intern information.

`raw_data\ds-routing-inventory.json` visar vilka DS som kan väljas i Kundtjänst-GUI:t och hur de routas från `Skapa kontrakt` steg 1 i stage. Källan ska användas för att välja rätt SPS- eller legacy-DS i test och för att skilja direkt upplagda SPS-DS från migrationsreferenser.

## Primära arbetsflöden

1. Skapa eller välj DS
2. Lägg upp zoner, områden, våningsplan och platser
3. Ange fysiska egenskaper, adresser och operativa kommentarer
4. Koppla ägare/hyresvärd/operatör samt produkter/defaultvärden
5. Underhåll BA- och betalautomatsinformation

## Data, objekt och regler

- GK delas i publik del och intern del
- intern GK innehåller produktnivåer, nyckelregler, kartor, historik och kontaktvägar
- platser kan enligt funktionsträd vara reserverade, oreserverade, aktiva, uthyrda, blockerade eller raderade

## UI, menyer och navigering

Stage visar främst övergripande entrypoints, medan legacy innehåller fler förvaltningssteg:

- `Administrera Område/zoner i ett garage`
- `Administrera platser i ett garage`
- `Administrera fysiska egenskaper för platser`
- `Administrera garageadresser`
- `Skapa nya platser i ett garage`
- `Sätt standardvärden per DS`

## Integrationer och beroenden

- produkt/paket-setup
- fastighetsägare/hyresvärd/operatör
- Accessy/Parakey/ANPR
- GK som operativ källa för kundservice

## Valideringar, fel och edge cases

- stage: `Registrera eller kontrollera BA i lagret` är trasig
- legacy: samma BA-funktion fungerar och visar faktisk lagerlista
- vissa DS verkar ha specialregler som endast finns i GK

## Bilder och visuellt underlag

Saknas. Bör kompletteras med DS-setup, platsadministration och GK-exempel.

## Kunskapsluckor / ej verifierat

- detaljerad datamodell för zoner/våningar/platser
- hur standardvärden påverkar efterföljande kontraktsskapande

## Öppna frågor

- Ska GK-strukturen brytas ut till ett eget syntetiskt dokument?
