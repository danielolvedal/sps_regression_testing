# Kundtjänst - köer, uppsägning och kundflöden

Den här manualen beskriver hur CSC arbetar när en kund väntar på plats, får ett erbjudande, säger upp sitt avtal eller behöver styras vidare till kundnära kanalflöden.

## Syfte

Ge Kundtjänst ett sammanhållet arbetssätt för:

- köhantering och erbjudanden
- uppsägning och efterarbete
- nyckel- och återlämningsrelaterad uppföljning
- koppling till serviceportalen och andra kundnära kanaler

## Bygger på

- `syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`
- `syntetisk_data\feature\kontrakt\uppsagning-och-avslut.md`
- `syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md`
- `syntetisk_data\lifecycle\kontraktets-livscykel.md`

## Grundprinciper

1. Dokumentera alltid kundens avsikt tydligt innan status eller kontrakt ändras.
2. Behandla kö, uppsägning och nytt erbjudande som delar av samma livscykel.
3. Kontrollera alltid garagekommentarer och lokala regler innan du avslutar ett avtal eller erbjuder ny plats.
4. När kanalval eller kundflöde är oklart ska Kundtjänst klargöra om kunden ska hanteras manuellt, via portal eller via specialupplägg.

## Köhantering

### Typiska menyvägar

| Behov | Typisk menyväg | Användning |
| --- | --- | --- |
| Se alla köer | `Köhantering > Visa alla köande` | Översikt över köer per garage/DS |
| Se kömedlemmar | `Köhantering > Alla ködeltagare` | Identifiera enskilda väntande kunder |
| Se kö för specifikt garage | `Köhantering > Visa kö för garage` | Garage- eller DS-specifik uppföljning |
| Sök kö för användare | `Köhantering > Sök kö för användare` | Kundspecifik köbild |
| Följa erbjudanden | `Köhantering > Visa erbjudanden` | Uppföljning av skickade erbjudanden |

### Rekommenderad arbetsordning

1. Identifiera rätt garage, DS eller kund.
2. Kontrollera om kunden redan finns i kö.
3. Kontrollera köposition, datum och kontaktuppgifter.
4. När plats finns: skapa eller följ upp erbjudandet.
5. Följ accept, avslag eller utgång innan platsen lämnas vidare till nästa kund.

### Tänk på

- Q-kontrakt verkar representera väntande kunder i systemlogiken.
- Stage och legacy har olika menystruktur för samma område.
- Vissa mall- och importsteg är tydligare i legacy än i stage.

## Uppsägning och avslut

### Huvudregel

Uppsägning ska hanteras som en styrd process, inte som en enskild klickåtgärd.

### Rekommenderad arbetsordning

1. Kontrollera garagekommentarer.
2. Bekräfta om kunden säger upp hela avtalet eller bara en del, till exempel en plats.
3. Registrera uppsägningen med rätt datum och tydlig kommentar.
4. Följ lokal rutin för nyckel, tagg, fjärrkontroll eller annan access.
5. Skicka eller initiera rätt kundkommunikation.
6. Kontrollera därefter om ny plats ska erbjudas nästa köande.

### Viktiga regler från underlaget

- Uppsägning ska normalt inkomma skriftligt.
- Kundens skriftliga uppsägning bör dokumenteras i systemkommentar.
- Vissa anläggningar kan ha kvartalsvisa eller andra särskilda avslutsvillkor.
- Utebliven nyckelretur kan utlösa engångsavgift.

## Efterarbete efter avslut

När ett avtal har avslutats bör Kundtjänst kontrollera:

- om platsen ska återställas som ledig
- om nyckel eller access behöver spärras eller följas upp
- om kö eller erbjudande ska aktiveras
- om ekonomi eller avisering påverkas av avslutet

## Kundnära kanalflöden

Underlaget beskriver tre huvudsätt att möta kunden:

| Kanal | När den typiskt används |
| --- | --- |
| Kundtjänst/CSC | När ärendet kräver manuell handläggning, bedömning eller specialfall |
| Serviceportalen / Mina sidor | När kunden själv ska hantera pågående avtal, status eller tillstånd |
| Hyra.apcoa.se / digitala flöden | När kunden själv söker plats, skapar kontrakt eller ställer sig i kö |

### När Kundtjänst bör styra kunden vidare

- när kunden kan slutföra standardflödet själv digitalt
- när portalen ger bättre uppföljning av tillstånd eller avisering
- när Kundtjänst har initierat ett flöde som kunden sedan ska förvalta själv

### När Kundtjänst bör behålla ärendet manuellt

- när flera kontrakt eller specialvillkor är inblandade
- när garagekommentarer eller lokala regler kräver bedömning
- när uppsägning, nyckelhantering eller ekonomiska följdeffekter måste säkras först

## Praktisk kontrollista vid kundärenden

- Vad vill kunden faktiskt uppnå?
- Finns redan ett aktivt avtal, en köpost eller ett erbjudande?
- Behöver kunden få hjälp i CSC nu, eller styras vidare till portal?
- Behöver lokal DS-information eller garagekommentar granskas först?
- Behöver access, nyckel eller ekonomi följas upp efter ändringen?

## Vanliga felkällor

- att kö, erbjudande och nytt kontrakt behandlas som separata processer
- att uppsägning registreras innan garagekommentarer eller omfattning kontrollerats
- att nyckel- eller accessefterarbete missas
- att kund hänvisas till portal trots att ärendet kräver manuell handläggning

## Ej fullverifierat

- detaljerad prioriteringslogik i köer
- fullständig modell för automatisk kundimport
- exakt klickflöde för individuell uppsägning i live-UI
- detaljerna i serviceportalens digitala tillståndsflöde

## Relaterade manualer

- `manuals\csc_user_manuals\Kundtjänst - kontrakt och avtal.md`
- `manuals\csc_user_manuals\Kundtjänst - anläggningar, produkter och access.md`
- `manuals\csc_user_manuals\Kundtjänst - rapporter, loggar och administration.md`
