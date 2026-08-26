# Kontraktets livscykel

## Dokument-ID

kontraktets-livscykel

## Syfte

Beskriver kontraktshanteringen som sammanhängande livscykel från sök/erbjudande och skapande till ändring, avisering, avslut och efterarbete.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar främst CSC/Kundtjänstportalen men knyter även in Sales Channel, Serviceportalen, köhantering, nycklar och ekonomi där de påverkar kontraktets livscykel.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS_function_spec_en.xlsx`
- `raw_data\SPS Funktionsträd.txt`
- `raw_data\Uthyrning Upplärning.docx`
- `raw_data\251203 Manual Hyra.apcoa.se.docx`

## Relaterade dokument

- `feature\kontrakt\skapa-kontrakt.md`
- `feature\kontrakt\andra-kontrakt.md`
- `feature\kontrakt\uppsagning-och-avslut.md`
- `feature\ko\koer-erbjudanden-och-importer.md`

## Funktioner i scope

- sök efter kund/DS/dokument
- skapa nytt kontrakt
- ändra kontrakt
- prisändringar och index
- VRM-hantering
- dokument och mallar
- uppsägning och avslut
- nyckelåterlämning
- kö och erbjudande efter avslut

## Hur området fungerar

SPS behandlar kontrakt som juridiska hyres- och tilläggsavtal, inte som enkla prenumerationer. Enligt funktionsspec och funktionsträd förekommer minst H-, T-, Q- och R-kontrakt. Ett kundflöde kan starta via kundtjänst, köerbjudande eller digital kanal, men leder i praktiken till samma behov: korrekt kund-/platskoppling, korrekt moms/avisering och korrekt uppföljning under avtalets hela liv.

## Primära arbetsflöden

1. **Identifiera behov** via sök, kö eller extern kanal
2. **Skapa kontrakt** genom val av DS/plats/paket och kunduppgifter
3. **Förvalta kontrakt** genom ändringar, VRM-hantering, prisjustering och dokument
4. **Avsluta kontrakt** enligt villkor, dokumentera kommentar och följ nyckelrutin
5. **Efterarbete**: återställ plats, hantera nycklar, kontrollera kö och skicka erbjudande

## Data, objekt och regler

- **H-kontrakt**: primärt hyresavtal för platsen
- **T-kontrakt**: tilläggstjänster och administration, normalt momspliktiga
- **Q-kontrakt**: köobjekt kopplade till framtida erbjudande
- **R-kontrakt/STP**: korttids- eller specialupplägg
- **GK/garagekommentarer**: central operativ källa vid uppsägning, specialregler och nycklar
- **VRM**: en eller flera registreringsnummer kan kopplas till kontraktet

## UI, menyer och navigering

Kärnflödet är utspritt över `Kontrakt`, `STP-tjänster`, `Köhantering`, `Loggar` och delar av `Admin`. I legacy ligger fler steg samlade under `Kontrakt` och `Garage`.

## Integrationer och beroenden

- Business Central/Navision för ekonomi och kontraktssynk
- Svea för betalning/fakturering
- Serviceportalen och hyra.apcoa.se för kundnära flöden
- Accessy/Parakey/EPMP/ANPR för access
- Outlook/mail för operativ kommunikation vid uppsägning och nyckelhantering

## Valideringar, fel och edge cases

- stage och legacy skiljer sig i menyplacering för samma flöde
- stage har brutna sidor för vissa stödfunktioner som påverkar full livscykeladministration
- kund kan vilja säga upp hela avtalet eller endast del av avtal/plats

## Bilder och visuellt underlag

Saknas underlag. Bör kompletteras med flödesbilder för skapa, ändra och avsluta kontrakt.

## Kunskapsluckor / ej verifierat

- exakta steg efter “Nästa steg” i alla kontraktsvyer är ännu inte genomgångna
- fullständig modell för uppdelning H/T/Q/R i UI saknas

## Öppna frågor

- Ska livscykeln modelleras separat för B2C, B2B, CPS och SaaS?
