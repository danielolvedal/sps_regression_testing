# Kunder, fastighetsagare, CPS och TPS

## Dokument-ID

kunder-fastighetsagare-cps-tps

## Syfte

Beskriver hur kund-, bolags- och organisationsrelaterade funktioner hänger ihop, inklusive CPS och Third Party Sales.

## Status

Initial syntetisk modell.

## Scope / avgränsning

Omfattar kunder, fastighetsägare/hyresvärdar, company administrator, CPS och TPS.

## Källor

- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SPS---Rulla-ut-statistik-för-fastighetsägare.pdf`
- `raw_data\SPS Funktionsträd – Utökad Specifik.txt`
- `raw_data\SPS Funktionsträd – Komplett System.txt`

## Relaterade dokument

- `crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`
- `feature\garage\garage-ds-setup-och-platser.md`

## Funktioner i scope

- `Admin\Company Administrator`
- `Admin\Customers`
- `Admin\Fastighetsägare`
- `Admin\CPS Dashboard`
- `Admin\Lista på identiteter`
- `Admin\Lista på externa tjänsteföretag`
- `Admin\Lista på fil importer`
- `Admin\ThirdPartySales Dashboard`

## Hur området fungerar

SPS verkar hantera både traditionella kontraktskunder och större organisationsstrukturer. Funktionsträden beskriver CPS som ett hierarkiskt system för personalparkering, medan TPS avser tredjepartsparkeringar/kunder med egen administration.

PDF-underlaget om utrullning av statistik för fastighetsägare förstärker bilden att fastighetsägarrollen också behöver informations- och rapporteringsflöden ut ur SPS.

## Primära arbetsflöden

1. Sök eller öppna juridisk person/kund
2. Hantera roller som kund, fastighetsägare eller hyresvärd
3. För CPS: administrera organisation, identiteter och arbetsplatser
4. För TPS: administrera tredjepartskunder och deras metadata

## Data, objekt och regler

- juridiska personer kan bära flera roller
- CPS använder flera administrativa nivåer enligt funktionsmaterialet
- externa tjänsteföretag förekommer som separat objekttyp

## UI, menyer och navigering

Stage och legacy visar liknande huvudområden, men stage har trasig `Lista på fil importer` medan legacy motsvarighet fungerar.

## Integrationer och beroenden

- Active Directory
- externa organisationer
- eventuellt HSA-id eller annan verifiering (`Ej verifierat i UI`)

## Valideringar, fel och edge cases

- samma bolag kan vara både kund och fastighetsägare
- CPS/TPS kräver sannolikt egen behörighetsmodell
- `Ej verifierat`: fullständig importmodell för CPS-filer

## Bilder och visuellt underlag

Saknas. Bör kompletteras med CPS- och TPS-dashboardbilder.

## Kunskapsluckor / ej verifierat

- exakt rollmodell i company administrator
- hur TPS-kunder kopplas till operativa flöden

## Öppna frågor

- Ska CPS och TPS få egna fördjupningsdokument?
