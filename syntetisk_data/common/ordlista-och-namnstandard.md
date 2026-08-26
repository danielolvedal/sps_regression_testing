# Ordlista och namnstandard

## Dokument-ID

ordlista-och-namnstandard

## Syfte

Skapar en gemensam terminologi för syntetisk data och pekar ut kända namn- och språkinkonsekvenser i systemet.

## Status

Initial standard, baserad på nuvarande raw data.

## Scope / avgränsning

Täcker SPS-begrepp, förkortningar och namnvariationer mellan `stage` och `stage legacy`.

## Källor

- `raw_data\Bokstavsfonetik, förkortningar.docx`
- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\sps_vs_legacy_summary.md`

## Relaterade dokument

- `common\syntetisk-data-standard.md`
- `crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`

## Funktioner i scope

- Begreppsnormalisering
- Språkstandard
- Namnkonflikter mellan menyer och miljöer

## Hur området fungerar

Syntetiska dokument ska använda svenska som huvudregel, men ange faktiska UI-etiketter i parentes när dessa avviker eller är engelska.

Exempel:

- **Kontraktsdokument** (`Visa kontraktsdokument`)
- **Nyckelinventarie** (`Key Inventory`)
- **Notifieringsmallar** (`Notification Templates`)

## Primära arbetsflöden

1. Använd normaliserat svenskt begrepp som rubrik
2. Lägg till faktisk menytext när den behövs för igenkänning i UI
3. Notera skillnader mellan stage och legacy i respektive dokument

## Data, objekt och regler

| Normaliserat begrepp | Vanliga varianter i materialet |
| --- | --- |
| DS | DS-nummer, anläggning, garage |
| GK | Garagekommentarer |
| VRM | registreringsnummer, vehicle registration mark |
| H-kontrakt | hyresavtal, huvudkontrakt |
| T-kontrakt | tilläggstjänst, add-on agreement |
| Q-kontrakt | köavtal |
| R-kontrakt / STP | korttidsavtal, Short Term Parking |
| Kundtjänst | CSC, Customer Service Center |
| Nyckelinventarie | Key Inventory |
| Driftstatus | SysDaemons, Running microservices and scheduled task |
| Verifieringskedja | Audit trail - Contract parking |

## UI, menyer och navigering

Kända inkonsekvenser:

- STP ligger under `Kontrakt` i legacy men under `STP-tjänster` i stage
- `Uppdatera KPI` ligger under `Garage` i legacy men under `Gemensamma inställningar` i stage
- `Notification Templates` finns på fler än ett ställe i stage
- flera admin- och rapportfunktioner har engelska namn i ett annars svenskt UI

## Integrationer och beroenden

Ordval påverkar hur integrationer beskrivs, särskilt kring Business Central, EPMP, HOJAB/Octavius, Accessy/Parakey och Sales Channel.

## Valideringar, fel och edge cases

- Samma path kan ha olika menybenämning i olika miljöer
- Engelska produktnamn bör inte översättas fritt om det riskerar att dölja faktiska systemnamn

## Bilder och visuellt underlag

Ej verifierat.

## Kunskapsluckor / ej verifierat

- Fullständig ordlista för alla interna förkortningar saknas ännu
- Svenska måltermer för flera engelska menyobjekt behöver beslutas formellt

## Öppna frågor

- Ska en separat officiell översättningsmatris skapas för menyer och manualer?
