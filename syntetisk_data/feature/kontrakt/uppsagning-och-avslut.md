# Uppsagning och avslut

## Dokument-ID

uppsagning-och-avslut

## Syfte

Beskriver processen för att avsluta kontrakt, dokumentera kundens uppsägning och hantera uppföljande aktiviteter som nyckelåterlämning och köerbjudanden.

## Status

Initial syntetisk modell med starkt processunderlag från utbildningsmaterial.

## Scope / avgränsning

Omfattar kontraktsavslut, massavslut i DS, uppsägningsorsaker och nyckeluppföljning.

## Källor

- `raw_data\Uthyrning Upplärning.docx`
- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS Funktionsträd – Utökad Specifik.txt`
- `raw_data\SPS_function_spec_en.xlsx`

## Relaterade dokument

- `lifecycle\kontraktets-livscykel.md`
- `feature\ko\koer-erbjudanden-och-importer.md`
- `feature\nycklar\nycklar-access-och-anpr.md`

## Funktioner i scope

- `Garage\Avsluta alla kontrakt på ett DS`
- `Gemensamma inställningar\Contract Termination Reasons`
- kontraktsavslut i redigeringsflöden (`Ej verifierat i UI`)

## Hur området fungerar

Utbildningsmaterialet beskriver uppsägning som en styrd process: kontrollera alltid garagekommentarer, verifiera om kunden säger upp hela avtalet eller bara en plats, klistra in kundens skriftliga uppsägning i SPS-kommentarer, följ nyckelrutinen, skicka bekräftelse och kontrollera därefter kölistan.

## Primära arbetsflöden

1. Kontrollera GK/garagekommentarer
2. Bedöm avtalsvillkor och uppsägningsomfattning
3. Registrera uppsägningen i SPS med korrekt datum och kommentar
4. Hantera nycklar och kommunikation
5. Lägg upp eventuell nyckelbevakning
6. Kontrollera kölista och skicka nytt erbjudande

## Data, objekt och regler

- uppsägningar ska enligt utbildningsmaterial normalt inkomma skriftligt
- kvartalsvisa avslut verkar vanliga i vissa upplägg
- nyckel som inte återlämnas inom viss tid kan utlösa engångsavgift
- uppsägningsorsaker har eget register i systemet

## UI, menyer och navigering

Massavslut i DS är verifierat i både stage och legacy. Uppsägningsorsaker finns i stage under `Gemensamma inställningar` och i legacy under `Admin`.

## Integrationer och beroenden

- Outlook/e-post
- nyckelhantering
- köhantering
- ekonomi/fakturering för avgifter efter utebliven återlämning

## Valideringar, fel och edge cases

- ett avtal kan innehålla flera platser
- lokal GK kan innehålla specialinstruktioner per DS
- `Ej verifierat`: komplett klickflöde för individuell uppsägning i UI

## Bilder och visuellt underlag

Saknas. Bör kompletteras med uppsägningsvy, termination reasons och nyckeluppföljning.

## Kunskapsluckor / ej verifierat

- exakt systemsteg för individuell uppsägning
- om automatisk notifiering triggas direkt i UI eller via bakgrundsjobb

## Öppna frågor

- Ska nyckelbevakningslistan modelleras som egen syntetisk artefakt?
