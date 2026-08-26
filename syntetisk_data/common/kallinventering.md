# Källinventering för syntetisk data

## Dokument-ID

kallinventering

## Syfte

Beskriver vilka källor i `raw_data` som finns, vad de bidrar med och hur de bör användas när syntetisk data byggs ut.

## Status

Initial inventering baserad på nuvarande `raw_data`.

## Scope / avgränsning

Täcker samtliga filer som fanns i `raw_data` vid genomgången.

## Källor

- `raw_data\251203 Manual Hyra.apcoa.se.docx`
- `raw_data\ANPR.docx`
- `raw_data\Bokstavsfonetik, förkortningar.docx`
- `raw_data\DS Grundinformation Garagekommentarer.docx`
- `raw_data\Features.txt`
- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`
- `raw_data\SAAS services.txt`
- `raw_data\Serviceportalen Digitala tillstånd guide .pdf`
- `raw_data\SPS Funktionsträd*.txt`
- `raw_data\SPS_function_spec_en.xlsx`
- `raw_data\SPS---Rulla-ut-statistik-för-fastighetsägare.pdf`
- `raw_data\System & länkar.xlsx`
- `raw_data\Uthyrning Upplärning.docx`
- `raw_data\sps_vs_legacy_summary.md`

## Relaterade dokument

- `common\syntetisk-data-standard.md`
- `feature\kanaler\serviceportalen-sales-channel-och-saas.md`
- `crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md`

## Funktioner i scope

- Källstyrning
- Val av auktoritativt underlag
- Bedömning av datakvalitet

## Hur området fungerar

Källorna kan delas in i fyra huvudtyper:

- **Hög struktur / hög tillförlitlighet:** menyinventeringarna i JSON samt `SPS_function_spec_en.xlsx`
- **Operativa guider:** utbildnings- och användardokument för kundtjänst, serviceportal och ANPR
- **Systemkartor och funktionsresonemang:** `SPS Funktionsträd*.txt`
- **Övriga stödmaterial:** ordlista, garagekommentarer, system-/länkkatalog, kompletterande PDF-underlag och lösa anteckningar

## Primära arbetsflöden

1. Börja med menyinventeringar och funktionsspecifikation för att identifiera funktioner
2. Fördjupa med utbildningsmaterial och processguider
3. Komplettera med funktionsträd för affärslogik, juridik och integrationsbild
4. Markera osäkerheter där källorna säger olika saker eller där endast legacy stödjer funktionen

## Data, objekt och regler

| Källa | Huvudvärde | Begränsning | Rekommenderad användning | Påverkade syntetiska dokument | Analysutfall |
| --- | --- | --- | --- | --- | --- |
| `raw_data\kundtjanst-funktioner-data.json` | Verifierad stage-navigation och sidstruktur | Visar främst UI-yta, inte djup backendlogik | Bas för nuvarande CSC-funktioner | `syntetisk_data\kundtjanst-menykarta.md`<br>`syntetisk_data\lifecycle\kontraktets-livscykel.md`<br>`syntetisk_data\feature\kontrakt\skapa-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\andra-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\prissattning-avisering-och-index.md`<br>`syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md`<br>`syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`<br>`syntetisk_data\feature\garage\garage-ds-setup-och-platser.md`<br>`syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md`<br>`syntetisk_data\feature\loggar\loggar-audit-och-drift.md`<br>`syntetisk_data\feature\rapporter\rapporter-och-powerbi.md` | Uppdaterad - inventeringskällan driver portal- och menybaserade syntetiska dokument. |
| `raw_data\kundtjanst-funktioner-legacy-data.json` | Verifierad legacy-navigation och äldre arbetsytor | Innehåller legacy-specifika placeringar | Gap-analys och komplett funktionstäckning | `syntetisk_data\kundtjanst-menykarta-legacy.md`<br>`syntetisk_data\lifecycle\kontraktets-livscykel.md`<br>`syntetisk_data\feature\kontrakt\skapa-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\andra-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\prissattning-avisering-och-index.md`<br>`syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md`<br>`syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`<br>`syntetisk_data\feature\garage\garage-ds-setup-och-platser.md`<br>`syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md`<br>`syntetisk_data\feature\loggar\loggar-audit-och-drift.md`<br>`syntetisk_data\feature\rapporter\rapporter-och-powerbi.md` | Uppdaterad - legacykällan används där funktionsbredd eller gap mot stage behöver beskrivas. |
| `raw_data\SPS_function_spec_en.xlsx` | Strukturerad feature-matris | På engelska, delvis konceptuell | Systemmodell, begrepp, funktionsgrupper | `syntetisk_data\lifecycle\kontraktets-livscykel.md`<br>`syntetisk_data\feature\kontrakt\skapa-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\prissattning-avisering-och-index.md`<br>`syntetisk_data\feature\kontrakt\uppsagning-och-avslut.md`<br>`syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md`<br>`syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`<br>`syntetisk_data\feature\produkter\produkter-paket-och-tillstandstider.md`<br>`syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md` | Uppdaterad - strukturerad specifikation används för normalisering av feature-grupper. |
| `raw_data\SPS Funktionsträd*.txt` | Brett resonemang om domän, juridik och integrationer | Överlappande och delvis syntetiskt | Tvärgående dokument och hypoteser | `syntetisk_data\lifecycle\kontraktets-livscykel.md`<br>`syntetisk_data\feature\kontrakt\skapa-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\andra-kontrakt.md`<br>`syntetisk_data\feature\kontrakt\prissattning-avisering-och-index.md`<br>`syntetisk_data\feature\kontrakt\uppsagning-och-avslut.md`<br>`syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md`<br>`syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`<br>`syntetisk_data\feature\produkter\produkter-paket-och-tillstandstider.md`<br>`syntetisk_data\feature\nycklar\nycklar-access-och-anpr.md`<br>`syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md`<br>`syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md`<br>`syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md` | Uppdaterad - wildcardraden täcker flera funktionsträdsfiler som används tvärgående. |
| `raw_data\Uthyrning Upplärning.docx` | Praktisk handläggning för kundtjänst | Rollspecifikt och situationsbundet | Avslut, GK, nyckelprocesser, erbjudanden | `syntetisk_data\lifecycle\kontraktets-livscykel.md`<br>`syntetisk_data\feature\kontrakt\uppsagning-och-avslut.md`<br>`syntetisk_data\feature\ko\koer-erbjudanden-och-importer.md`<br>`syntetisk_data\feature\garage\garage-ds-setup-och-platser.md`<br>`syntetisk_data\feature\nycklar\nycklar-access-och-anpr.md` | Uppdaterad - operativa arbetsflöden kommer från utbildningsmaterialet. |
| `raw_data\251203 Manual Hyra.apcoa.se.docx` | Slutanvändarflöde för hyra.apcoa.se | Kanalfokuserat, ej full systembild | Service portal / sales channel | `syntetisk_data\lifecycle\kontraktets-livscykel.md`<br>`syntetisk_data\feature\kontrakt\skapa-kontrakt.md`<br>`syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md` | Uppdaterad - kanal- och kontraktsflöden har normaliserats utifrån manualen. |
| `raw_data\Serviceportalen Digitala tillstånd guide .pdf` | Guide för digitala tillstånd i serviceportalen | Kanal- och delprocessfokuserad | Serviceportalens tillståndsflöden och självservice | `syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md` | Uppdaterad - används för portalens tillståndsflöden och begrepp. |
| `raw_data\ANPR.docx` | ANPR/Park & Go-flöde och betalning | Kanal-/produktfokuserat | Access, betalning, externa system | `syntetisk_data\feature\nycklar\nycklar-access-och-anpr.md`<br>`syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md` | Uppdaterad - ANPR används i access- och integrationsdokumentation. |
| `raw_data\DS Grundinformation Garagekommentarer.docx` | Struktur för publika och interna garagekommentarer | Exempelbaserat | DS/GK-processer | `syntetisk_data\feature\garage\garage-ds-setup-och-platser.md` | Uppdaterad - garage/DS-dokumentet använder denna källa direkt. |
| `raw_data\System & länkar.xlsx` | Systemlandskap och ägarskap | Mer katalog än processdokument | Integrationer, systemansvar, beroenden | `syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md`<br>`syntetisk_data\feature\loggar\loggar-audit-och-drift.md`<br>`syntetisk_data\crosscutting\juridik-efterlevnad-ekonomi-och-integrationer.md` | Uppdaterad - används främst för systemlandskap och beroenden. |
| `raw_data\Bokstavsfonetik, förkortningar.docx` | Ordlista och förkortningar | Stödmaterial | Namnstandard, begreppsstöd | `syntetisk_data\common\ordlista-och-namnstandard.md` | Uppdaterad - ordlistan normaliserar språket i det syntetiska lagret. |
| `raw_data\SPS---Rulla-ut-statistik-för-fastighetsägare.pdf` | Referens om statistikleverans och fastighetsägarperspektiv | Begränsat specialistunderlag | Tvärgående material för rapportering och kundkommunikation | `syntetisk_data\feature\rapporter\rapporter-och-powerbi.md`<br>`syntetisk_data\feature\organisation\kunder-fastighetsagare-cps-tps.md` | Uppdaterad - rapport- och fastighetsägarperspektivet har införts i berörda dokument. |
| `raw_data\Features.txt` | Lågstrukturerad stödanteckning | Mycket tunt underlag | Endast som svag kompletterande signal | Ingen ytterligare påverkan utöver `syntetisk_data\common\kallinventering.md` | Analyserad - ingen ytterligare påverkan eftersom filen saknar tillräckligt innehåll. |
| `raw_data\SAAS services.txt` | Lågstrukturerade SaaS-anteckningar | Mötesnära och ospecificerat | Endast som svagt stöd för kanal-/SaaS-resonemang | `syntetisk_data\feature\kanaler\serviceportalen-sales-channel-och-saas.md` | Uppdaterad - källan används som svag stödkälla i SaaS-resonemanget. |
| `raw_data\sps_vs_legacy_summary.md` | Koncentrerad gap-analys | Härledd sekundärkälla | Prioritering av dokument- och testarbete | `syntetisk_data\feature\garage\garage-ds-setup-och-platser.md`<br>`syntetisk_data\feature\loggar\loggar-audit-och-drift.md`<br>`syntetisk_data\feature\rapporter\rapporter-och-powerbi.md`<br>`syntetisk_data\feature\kontrakt\vrm-och-kontraktsdokument.md` | Uppdaterad - används där stage/legacy-gap påverkar syntetiska slutsatser. |

## UI, menyer och navigering

Ej primär källa. Se i första hand JSON-inventeringarna och menykartorna.

## Integrationer och beroenden

Källinventeringen pekar redan ut centrala beroenden till Business Central, EPMP, Svea, HOJAB/Octavius, Accessy/Parakey, Flowbird/Cale och externa portaler.

## Valideringar, fel och edge cases

- `Features.txt` är tom och tillför för närvarande inget
- `SAAS services.txt` innehåller lösa mötesanteckningar och bör endast användas som svagt stöd
- vissa Power BI-länkar är trasiga i stage och ska inte ensam användas som sanningskälla
- `kallinventering.md` ska hållas synkad mot aktuellt innehåll i `raw_data` och verifieras med regressionstest
- varje rad i tabellen ovan måste också visa vilka syntetiska dokument som analyserats eller uppdaterats

## Bilder och visuellt underlag

Saknas ännu som strukturerad uppsättning.

## Kunskapsluckor / ej verifierat

- Flera PDF-källor är ännu inte transkriberade fullt ut
- Ingen databasmodell eller API-kontrakt finns i källmaterialet
- Djup systemlogik bakom vissa adminverktyg är fortfarande indirekt beskriven

## Öppna frågor

- Vilka raw-data-källor ska betraktas som affärsmässigt auktoritativa när de säger olika saker?
- Ska PDF- och DOCX-utdrag normaliseras ytterligare till maskinläsbara JSON/Markdown-källor?
