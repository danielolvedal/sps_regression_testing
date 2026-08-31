# Kundtjänst - anläggningar, produkter och access

Den här manualen beskriver hur CSC bör tänka kring DS, garage, produkter, paket, VRM, nycklar och access så att rätt objekt används i kund- och kontraktsflöden.

## Syfte

Ge en praktisk översikt för att:

- förstå hur DS och garage styr arbetet
- välja rätt produkter och paket
- hantera registreringsnummer, nycklar och access
- tolka lokala regler och anläggningsspecifika förutsättningar

## Bygger på

- `syntetisk_data\feature\garage\garage-ds-setup-och-platser.md`
- `syntetisk_data\feature\produkter\produkter-paket-och-tillstandstider.md`
- `syntetisk_data\feature\nycklar\nycklar-access-och-anpr.md`
- `syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md`

## DS och garage som grundobjekt

DS är den viktigaste styrande enheten i stora delar av SPS. När Kundtjänst arbetar med skapande, ändring, pris, kö, nycklar eller platsfrågor bör rätt DS verifieras tidigt.

### När DS ska kontrolleras först

- nytt kontrakt eller nytt korttidsavtal
- byte av plats eller anläggning
- prisändring på flera kontrakt
- garageöversikt, köhantering eller lokala regler
- frågor om access, nycklar eller betalautomater

## Garagekommentarer och lokala regler

Underlaget beskriver garagekommentarer som en central operativ källa.

### Garagekommentarer kan innehålla

- publika instruktioner
- interna arbetsanteckningar
- nyckelregler
- produktnivåer
- kontaktvägar
- lokala undantag och historik

### Praktisk regel

Om ett ärende gäller en specifik anläggning och utfallet känns osäkert ska garagekommentarer eller lokal DS-information kontrolleras innan kunden får ett definitivt besked.

## Produkter, paket och tillståndsscheman

Produkter och paket beskriver vad kunden faktiskt hyr eller får tillgång till. Tillståndsscheman, skattesatser och BC-koder styr samtidigt ekonomi och giltighet.

### Rekommenderad arbetsordning

1. Kontrollera vilket DS eller vilken anläggning kunden tillhör.
2. Kontrollera vilken produkt eller paketmall som ska användas.
3. Kontrollera om särskilt tillståndsschema eller skatteregel gäller.
4. Verifiera att upplägget stämmer med kundtyp och kontraktsmodell.

### Viktiga begrepp

| Begrepp | Praktisk betydelse |
| --- | --- |
| Produktmall | Grundobjektet för det som säljs eller hyrs ut |
| Paketmall | Samling av flera produkter |
| Tillståndsschema | Styr när tillståndet gäller |
| BC-kod | Koppling till ekonomisystemet |
| Skattesats | Styr momsbehandling |

## VRM och fordonskoppling

VRM är centralt i både kundservice och access.

### När vanlig VRM-hantering räcker

- när ett registreringsnummer ska läggas till eller tas bort från ett enskilt kontrakt

### När extra försiktighet krävs

- när VRM-pooler ska slås ihop
- när kontrakt ska pekas om till annan VRM-pool
- när flera kunder eller flera kontrakt påverkas av samma fordonsstruktur

## Nycklar och fysisk access

Underlaget beskriver både fysisk och digital access.

### Exempel på accessobjekt

- fysisk nyckel
- tagg
- fjärrkontroll
- kort
- registreringsnummer i ANPR-/LPR-flöde

### Rekommenderad kontrollista

- vilken accessform använder anläggningen?
- finns lokal rutin i garagekommentarer?
- ska access delas ut, uppdateras, spärras eller återlämnas?
- krävs uppföljning efter uppsägning eller platsbyte?

## Digital access och ANPR

SPS-underlaget beskriver beroenden till bland annat:

- Accessy
- Parakey
- EPMP
- ANPR/Park & Go-flöden

Det betyder att VRM och access inte bara är interna registerfrågor. Fel i fordons- eller accessdata kan påverka inpassering, debitering och kundens faktiska möjlighet att använda platsen.

## Betalautomater och anläggningsstöd

Frågor om betalautomater, BA och relaterad utrustning är också kopplade till DS.

### Viktigt att känna till

- `Visa betalautomater per DS` fungerar som sökväg för betalautomatsuppslag.
- `Registrera eller kontrollera BA i lagret` är känd som trasig i stage men fungerar i legacy enligt underlaget.

## Vanliga felkällor

- att fel DS används i början av ärendet
- att produkt och paket blandas ihop
- att VRM ändras utan kontroll av accesspåverkan
- att lokal garageinformation inte granskas innan besked ges
- att nyckel- eller accessretur inte följs upp vid avslut

## Ej fullverifierat

- detaljerad datamodell för zoner, våningar och platser
- fullständig fältmodell för produktregister
- fullständig modell för digital behörighetsprovisionering
- exakt relation mellan VRM-pooler och accessmotor

## Relaterade manualer

- `manuals\csc_user_manuals\Kundtjänst - kontrakt och avtal.md`
- `manuals\csc_user_manuals\Kundtjänst - köer, uppsägning och kundflöden.md`
- `manuals\csc_user_manuals\Kundtjänst - rapporter, loggar och administration.md`
