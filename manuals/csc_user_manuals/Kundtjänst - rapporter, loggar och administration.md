# Kundtjänst - rapporter, loggar och administration

Den här manualen beskriver hur CSC använder rapporter, loggar och administrativa register för uppföljning, felsökning och styrning av kund- och kontraktsprocesser.

## Syfte

Ge ett praktiskt stöd för att:

- välja rätt rapportyta
- förstå skillnaden mellan rapport, audit trail och driftstatus
- använda administrativa register för masterdata och specialflöden
- bedöma när stage-felet ligger i data, integration eller UI

## Bygger på

- `syntetisk_data\feature\rapporter\rapporter-och-powerbi.md`
- `syntetisk_data\feature\loggar\loggar-audit-och-drift.md`
- `syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md`
- `syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`
- `syntetisk_data\common\ordlista-och-namnstandard.md`

## Tre huvudtyper av uppföljning

| Typ | Används för | Exempel |
| --- | --- | --- |
| Rapport | Affärsöversikt, statistik eller export | Power BI, kontrakts- eller DS-rapporter |
| Audit trail / logg | Spåra vem eller vad som ändrat något | kontrakt, garage, produkter, synkloggar |
| Drift-/processvy | Felsöka bakgrundsjobb, tjänster och integrationer | Backend Process Events, scheduler, microservices |

## Rapporter

Rapportområdet består av både inbyggda operativa rapporter och Power BI-länkar.

### När rapport bör användas

- när Kundtjänst behöver statistik, översikt eller export
- när ett mönster behöver följas över flera kontrakt eller anläggningar
- när en fastighetsägare, intern funktion eller uppföljningsroll behöver sammanställd information

### Viktig skillnad

- En Power BI-container kan öppnas även om själva rapporten bakom är felkopplad.
- Därför måste `rapporten öppnade` och `rapportinnehållet fungerade` behandlas som två olika kontroller.

### Kända rapportproblem i stage

Underlaget pekar ut flera rapporter som felande eller delvis trasiga. Om en sådan rapport behövs operativt ska problemet dokumenteras tydligt och inte tolkas som användarfel utan verifiering.

## Audit trail och loggar

Audit och loggar används när Kundtjänst behöver förstå förändringar eller förklara vad som hänt.

### Typiska användningar

- kontrollera kontraktsändringar
- kontrollera garageändringar
- kontrollera produkt- eller paketändringar
- följa synk mot externa system
- bekräfta om ett bakgrundsjobb har startat, fastnat eller fallerat

### Rekommenderad felsökningsordning

1. Bekräfta vilket objekt som berörs: kontrakt, garage, produkt, kund eller integration.
2. Öppna relevant audit trail eller synklogg.
3. Kontrollera om ändringen syns där.
4. Om inte: kontrollera driftstatus eller process events.
5. Om stage beter sig avvikande: jämför med känd legacy-funktion när sådan finns dokumenterad.

## Driftverktyg och bakgrundsjobb

SPS-underlaget beskriver flera verktyg för att följa scheduler, mikrotjänster och processhändelser.

### När dessa verktyg är viktiga

- när en ändring inte verkar slå igenom
- när pris, synk eller import inte uppdateras som väntat
- när ett UI-fel kan bero på underliggande tjänst och inte på skärmen i sig

### Känd skillnad mellan miljöer

- vissa driftverktyg fungerar i legacy men är trasiga i stage
- samma funktion kan ha olika namn i olika miljöer, till exempel `SysDaemons` kontra `Running microservices and scheduled task`

## Administration och masterdata

Administrativa register används när Kundtjänst behöver förstå eller underhålla objekt som påverkar flera flöden samtidigt.

### Exempel på sådana områden

- kunder
- fastighetsägare och hyresvärdar
- Company Administrator
- CPS- och TPS-relaterade ytor
- BC-koder
- skattesatser
- tillståndsscheman
- uppsägningsorsaker

### Praktisk regel

Om ett problem återkommer i flera olika kundärenden bör CSC överväga om roten ligger i masterdata eller registerkonfiguration snarare än i ett enskilt kontrakt.

## Tvärgående regler att ha i huvudet

| Regelområde | Praktisk betydelse för Kundtjänst |
| --- | --- |
| H-, T-, Q- och R-kontrakt | Påverkar hur avtal, kö och korttidsflöden ska tolkas |
| Moms och BC-koder | Påverkar ekonomi, avisering och prislogik |
| Externa integrationer | Påverkar betalning, access, rapportering och synk |
| Språk- och namninkonsekvenser | Samma funktion kan heta olika i stage, legacy och dokumentation |

## När ärendet ska eskaleras

Eskaleringsbehov finns ofta när:

- rapportcontainern öppnar men datan saknas eller är uppenbart fel
- audit trail saknar väntad ändring
- backendprocess eller mikrotjänst verkar stå still
- samma fel uppstår i flera kontrakt, DS eller kundärenden
- stage saknar funktion som finns dokumenterat fungerande i legacy

## Vanliga felkällor

- att användaren tror att en rapport fungerar bara för att ramen öppnas
- att audit trail, synklogg och driftstatus blandas ihop
- att masterdatafel misstolkas som fel i ett enskilt kundärende
- att olika namn i stage och legacy får CSC att tro att det är olika funktioner

## Ej fullverifierat

- full datadefinition per rapport
- fullständig tolkning av varje backendjobb
- exakt ansvarsfördelning per mikrotjänst
- detaljerad rollmodell i CPS/TPS och Company Administrator

## Relaterade manualer

- `manuals\csc_user_manuals\Kundtjänst - kontrakt och avtal.md`
- `manuals\csc_user_manuals\Kundtjänst - köer, uppsägning och kundflöden.md`
- `manuals\csc_user_manuals\Kundtjänst - anläggningar, produkter och access.md`
- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
