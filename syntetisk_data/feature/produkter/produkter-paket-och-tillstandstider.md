# Produkter, paket och tillstandstider

## Dokument-ID

produkter-paket-och-tillstandstider

## Syfte

Beskriver hur produkter, paket, tillståndsscheman och relaterade skatte-/BC-koder hänger ihop.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar produktmallar, paketmallar, tillståndsscheman, tilläggsprodukter och ekonomiska kodningar.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd – Teknisk & Jurid.txt`
- `raw_data\SPS Funktionsträd – Detaljerad Syst.txt`
- `raw_data\SPS_function_spec_en.xlsx`

## Relaterade dokument

- `feature\kontrakt\skapa-kontrakt.md`
- `feature\kontrakt\prissattning-avisering-och-index.md`

## Funktioner i scope

- `Produkt\Produktmall`
- `Produkt\Paketmallar`
- `Produkt\Reklambanner`
- `Gemensamma inställningar\Tillståndsscheman`
- `Gemensamma inställningar\Skattesatser`
- `Gemensamma inställningar\BC-koder`
- legacyfunktioner för att skapa/hantera hyresprodukter och tilläggsprodukter

## Hur området fungerar

Funktionsmaterialet beskriver SPS som ett paketerat system där produkter, tariff, tillståndstid och produktklass samverkar. Ett paket kan enligt beskrivningen generera både H- och T-kontrakt för korrekt moms och bokföring. Legacy visar dessutom äldre operativa verktyg för att skapa och hantera hyresprodukter direkt.

## Primära arbetsflöden

1. Definiera skattesats, BC-kod och tillståndsschema
2. Skapa produktmall eller tilläggsprodukt
3. Samla produkter i paketmall
4. Knyt paket till DS och kontraktsflöden

## Data, objekt och regler

- paket kan innehålla flera produktmallar
- tillståndsschema definierar giltighet i tid
- BC-koder mappar produkt/avgift till ekonomi
- skattesatser styr momsbehandling

## UI, menyer och navigering

Stage innehåller moderna register för produktmallar, paketmallar och tillståndsscheman. Legacy visar fler verktyg direkt under `Garage`/`Sales` för att skapa och hantera produkter.

## Integrationer och beroenden

- Business Central/Navision
- kontraktsskapande
- serviceportal/sales channel

## Valideringar, fel och edge cases

- flera engelska termer finns kvar i produktrelaterad UI
- `Ej verifierat`: exakt skillnad mellan produktmall, produkttyp och paket i varje flöde

## Bilder och visuellt underlag

Saknas. Bör kompletteras med skärmbilder på produktmall, paketmall och tillståndsschema.

## Kunskapsluckor / ej verifierat

- fullständig fältmodell för produktregister
- exakt hur reklam banners används i kundflöden

## Öppna frågor

- Behöver produkt-/paketarkitekturen få ett separat dokument per objekttyp?
