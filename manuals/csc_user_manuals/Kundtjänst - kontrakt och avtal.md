# Kundtjänst - kontrakt och avtal

Den här manualen beskriver hur CSC normalt arbetar med kontrakt från första identifiering till löpande ändringar, prisjusteringar och kontraktsdokument.

## Syfte

Ge Kundtjänst ett praktiskt arbetssätt för att:

- hitta rätt kund eller kontrakt
- skapa nya kontrakt eller korttidsavtal
- ändra befintliga avtal
- hantera pris, avisering och kontraktsdokument

## Bygger på

- `syntetisk_data\lifecycle\kontraktets-livscykel.md`
- `syntetisk_data\feature\kontrakt\skapa-kontrakt.md`
- `syntetisk_data\feature\kontrakt\andra-kontrakt.md`
- `syntetisk_data\feature\kontrakt\prissattning-avisering-och-index.md`
- `syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md`

## Grundprinciper

1. Börja alltid med att identifiera rätt kontrakt, kund eller DS.
2. Kontrollera om ärendet gäller långtidskontrakt, korttidsavtal/STP, tillägg eller dokument.
3. Tänk igenom följdeffekter innan ändring sparas: pris, moms, avisering, VRM, access och dokument.
4. Om instruktionen från kunden är oklar ska ärendet först klargöras innan administrativ ändring görs.

## Vanliga ingångar i Kundtjänstportalen

| Behov | Typisk menyväg | Vad den används till |
| --- | --- | --- |
| Hitta kund eller kontrakt snabbt | `Kontrakt > Sök` | Snabbsökning på kontrakt, kund, DS, VRM och dokument |
| Skapa nytt avtal | `Kontrakt > Sätt upp nytt kontrakt` | Startar skapaflödet via DS-val |
| Skapa korttidsavtal | `STP-tjänster > Skapa nytt korttidsavtal` | Startar STP-flöde via DS-val |
| Ändra befintligt avtal | `Kontrakt > Ändra ett kontrakt` | Öppnar redigeringsflödet via kontraktsnummer |
| Ändra pris | `Kontrakt > Ändra pris på ett kontrakt` | Enskild prisjustering |
| Uppdatera VRM | `Kontrakt > Lägg till/ta bort VRMer för ett kontrakt` | Koppla eller ta bort registreringsnummer |
| Skapa dokument | `Kontrakt > Skapa kontrakt utfrån mall` | Skapa eller skriv ut kontraktsdokument |

## Arbetsflöde: hitta rätt avtal

1. Starta i `Kontrakt > Sök` när kund, VRM, dokument eller DS är känt men inte exakt kontraktsnummer.
2. Använd `Ändra ett kontrakt` när kontraktsnumret redan är känt.
3. Använd `Old Search Method` bara när den moderna sökvägen inte räcker eller när specialfall kräver bredare sökningar.
4. Verifiera alltid att rätt kund och rätt period har valts innan du går vidare till ändring eller uppsägning.

## Arbetsflöde: skapa nytt kontrakt

### Rekommenderad arbetsordning

1. Välj rätt DS/anläggning.
2. Kontrollera att rätt produkt, plats eller paket används.
3. Registrera kunduppgifter.
4. Ange startdatum och relevant aviserings-/betalningsinformation.
5. Slutför skapandet och kontrollera om dokument eller portalinformation behöver skickas vidare.

### Tänk på

- DS är första styrande objektet i skapaflödet.
- Vissa anläggningar kan ha särskilda regler i garagekommentarer eller lokala rutiner.
- Korttidsflöden och långtidsflöden kan ha olika datakrav.
- Djupare steg efter första DS-valet är delvis `Ej fullverifierat` i live-UI och bör därför dubbelkontrolleras i faktisk körning.

## Arbetsflöde: ändra befintligt kontrakt

Vanliga ändringstyper enligt underlaget:

- ändra period eller slutdatum
- byta plats eller anläggningskoppling
- uppdatera kundnära uppgifter som påverkar kontraktets fortsättning
- följa upp VRM, dokument eller tilläggstjänster

### Rekommenderad kontrollista före ändring

- Är det rätt kontrakt?
- Gäller ändringen hela avtalet eller bara en plats/del?
- Påverkas pris, moms eller avisering?
- Behöver VRM, nyckel eller access ändras samtidigt?
- Behöver nytt dokument skapas efter ändringen?

## Arbetsflöde: prisändring och avisering

SPS-underlaget beskriver stöd för flera prisjusteringsmetoder:

- procentuell höjning
- fast belopp
- KPI-baserad höjning
- nytt fast pris

### När en prisändring hanteras

1. Identifiera rätt kontrakt eller DS.
2. Välj korrekt höjningsmetod.
3. Kontrollera ändringsdatum.
4. Kontrollera om moms, BC-kod eller paketlogik påverkas.
5. Följ upp om ändringen behöver verifieras i loggar eller ekonomiuppföljning.

### Viktiga regler

- H-kontrakt och T-kontrakt kan ha olika momslogik.
- Batchändringar på DS ska användas med större försiktighet än enskilda prisändringar.
- Stage har kända problem kring `Uppdatera KPI`; om KPI-spåret behövs operativt kan legacy eller annan verifieringsyta behöva användas.

## Arbetsflöde: VRM och kontraktsdokument

### VRM

- Ett kontrakt kan vara kopplat till ett eller flera registreringsnummer.
- Vanlig VRM-hantering sker på kontraktsnivå.
- Mer avancerad VRM-poolhantering ligger under adminverktyg och bör användas försiktigt eftersom ompekning eller sammanslagning kan få bredare följdeffekter.

### Dokument

- Kontraktsdokument kan skapas från mall.
- Dokumentflödet används när Kundtjänst behöver skriva ut eller generera avtalshandlingar.
- Dokumentfunktionerna verkar vara bredare i legacy än i stage, så vissa uppslag eller metadata kan kräva äldre vyer.

## Beslutsstöd: vilket spår ska användas?

| Situation | Rekommenderat spår |
| --- | --- |
| Kunden vill ha ny plats eller nytt avtal | Starta nytt kontraktsflöde |
| Kunden har ett aktivt kontrakt som ska justeras | Öppna ändringsflödet |
| Endast priset ska uppdateras | Prisändring på kontrakt eller DS |
| Endast registreringsnummer ska bytas | VRM-flödet |
| Ett avtal eller bevis behöver skapas ut | Dokument från mall |

## Vanliga felkällor

- fel kund när samma person eller bolag har flera kontrakt
- sammanblandning mellan hel uppsägning och deluppsägning
- prisändring utan kontroll av moms eller aviseringspåverkan
- VRM-ändring utan att access- eller dokumentpåverkan beaktas

## Ej fullverifierat

- hela steg 2+ i kontraktsskapandet
- hela steg 2+ i kontraktsändringsflödet
- fullständig beslutslogik för samavisering och alla aviseringsmetoder
- exakt gräns mellan vanlig VRM-redigering och VRM-pooladministration

## Relaterade manualer

- `manuals\csc_user_manuals\Kundtjänst - köer, uppsägning och kundflöden.md`
- `manuals\csc_user_manuals\Kundtjänst - anläggningar, produkter och access.md`
- `manuals\csc_user_manuals\Kundtjänst - rapporter, loggar och administration.md`
- `manuals\csc_user_manuals\Kundtjänst - funktioner.md`
