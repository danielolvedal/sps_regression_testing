# Syntetisk data - standard

## Dokument-ID

syntetisk-data-standard

## Syfte

Definierar standarden för all syntetisk data i SPS-repositoryt. Standarden säkerställer att efterföljande AI-agenter producerar kompatibla dokument som kan återanvändas för manualer, instruktioner, one-pagers och säljmaterial.

## Status

Aktiv standard.

## Scope / avgränsning

Gäller alla dokument under `syntetisk_data`.

## Källor

- `AGENTS.md`
- `dokument_index\index.md`
- `tools\docs\katalogstruktur.md`
- `tools\docs\browser-samarbete-stage-session.md`
- `raw_data\kundtjanst-funktioner-data.json`
- `raw_data\kundtjanst-funktioner-legacy-data.json`

## Relaterade dokument

- `common\kallinventering.md`
- `common\ordlista-och-namnstandard.md`
- `lifecycle\kontraktets-livscykel.md`

## Primär struktur

- `common` för regler, källor och namnstandard
- `feature` för vad funktioner gör
- `lifecycle` för när/hur funktioner används över tid
- `crosscutting` för juridik, ekonomi och integrationer
- `assets\images` för visuellt underlag

## Obligatoriska sektioner i varje syntetiskt dokument

Alla nya syntetiska dokument ska innehålla följande rubriker:

1. Dokument-ID
2. Syfte
3. Status
4. Scope / avgränsning
5. Källor
6. Relaterade dokument
7. Funktioner i scope
8. Hur området fungerar
9. Primära arbetsflöden
10. Data, objekt och regler
11. UI, menyer och navigering
12. Integrationer och beroenden
13. Valideringar, fel och edge cases
14. Bilder och visuellt underlag
15. Kunskapsluckor / ej verifierat
16. Öppna frågor

## Dokumentregler

- Fakta ska beskrivas en gång och länkas från andra dokument i stället för att dupliceras.
- Om information saknas ska sektionen stå kvar och märkas `Ej verifierat` eller `Saknas underlag`.
- Ett feature-dokument beskriver **vad** en funktion gör; ett lifecycle-dokument beskriver **när** och **hur** flera funktioner samverkar.
- Legacy-specifik information ska markeras tydligt i brödtexten.
- Språk ska i första hand vara svenska, men faktiska systemnamn och UI-etiketter får återges på originalspråk.

## Rekommenderad detaljnivå

- Beskriv varje område så att en ny AI-agent kan skriva en första manual utan att börja om från rådata.
- Fånga både affärslogik och handläggningslogik.
- Notera skillnader mellan `stage` och `stage legacy` när de påverkar dokumentation eller testning.

## Bilder och visuellt underlag

- Bilder sparas under `syntetisk_data\assets\images\...`
- Filnamn ska spegla dokument och steg, exempelvis `skapa-kontrakt-step-01.png`
- Om bilder saknas ska sektionen ändå finnas kvar i dokumentet

## Underhållsregler

- Nya syntetiska dokument ska läggas in i `syntetisk_data\index.md`
- Alla beständiga filer ska registreras i `dokument_index\index.md`
- `runtime\test-document-index.ps1` ska alltid köras efter ändringar
- När `raw_data` ändras ska `common\kallinventering.md` uppdateras och `runtime\test-kallinventering-coverage.ps1` köras
- `common\kallinventering.md` ska för varje råkälla ange påverkade syntetiska dokument eller uttryckligen markera `Analyserad - ingen ytterligare påverkan`
