# Fastlåst katalogstruktur för SPS-dokumentation

Den här katalogstrukturen är styrande för allt arbete under SPS-repositoryts rotkatalog, oavsett var den ligger på disk.

## Rotprincip

Alla beständiga filer ska placeras i en namngiven katalog under projektroten. Temporära filer får endast finnas i `tmp`.

## Kataloger

| Katalog | Syfte |
| --- | --- |
| `raw_data` | Råmaterial från SPS, browserextraktioner och extern/systemnära referensdokumentation. |
| `syntetisk_data` | Strukturerad, bearbetad eller AI-optimerad information baserad på `raw_data`. |
| `tools\source` | Källkod för verktyg, connectors, script och automation som arbetar med SPS eller dess dokumentation. Detta är inte SPS applikationskod. |
| `tools\docs` | Dokumentation för verktyg, arbetsmetoder och skript. Handlar om verktygen, inte om SPS-funktioner i sig. |
| `tools\docs\road-map` | Roadmaps för de verktyg vi bygger/använder runt SPS. |
| `tools\docs\decissions` | Beslut som rör verktyg, skript, runtime och arbetssätt. |
| `tools\source\[tool_name]` | Källkod för specifika hjälpverktyg som utvecklas för SPS-arbetet. |
| `testing\funktional_test` | Beskrivningar, fall och metodik för funktionella tester. |
| `testing\regression_test` | Promotade och körbara delade regressionstester. |
| `testing\regression_drafts` | Personliga eller opromotade regressionstestutkast per användare innan de flyttas till den delade katalogen. |
| `manuals\csc_user_manuals` | Färdiga manualer för kundtjänst/CSC. |
| `manuals\user_manuals` | Färdiga manualer för slutanvändare i serviceportalen. |
| `manuals\client_manuals` | Färdiga manualer för klienter, företag och SaaS-kunder. |
| `dokument_index` | Övergripande index över dokument, data, scripts och referenser. |
| `runtime` | Körklara skript och verktyg. Roten innehåller stabila användar-wrappers; OS-/miljöspecifika entrypoints placeras i underkataloger. |
| `runtime\windows` | Windows-specifika runtime-entrypoints, till exempel Copilot-admin host runner, terminalinmatning och PTY-POC. |
| `runtime\docker` | Målplats för framtida Docker-/control-plane-entrypoints. |
| `tmp` | Enda tillåtna platsen för temporära filer, profiler, exporter och mellanresultat. |

## Styrande regler

1. Inga nya toppnivåkataloger får införas utan uttryckligt beslut.
2. Inga temporära filer får läggas utanför repositoryrotens `tmp`; `tmp`-kataloger under `tools` eller andra underkataloger är förbjudna.

2.a. Verktygsinfrastruktur-loggar (install/start/stop/reinstall, Playwright- eller node-start, och andra fasta drift-/infrastruktur-skript) ska skrivas till `tool_error_logs` i repositoryroten. Endast loggar som tillhör verktygets infrastruktur får sparas där — test- och regressionsloggar ska fortsätta sparas under `tmp` och inte i `tool_error_logs`. "}
3. Nya råuttag från systemet ska i första hand till `raw_data`.
4. Strukturerad sammanställning för AI eller dokumentproduktion ska till `syntetisk_data`.
5. Färdiga användardokument ska till `manuals`.
6. Verktygsdokumentation ska till `tools\docs`; verktygsroadmaps ska till `tools\docs\road-map` och verktygsbeslut ska till `tools\docs\decissions`.
7. `AGENTS.md` ska alltid peka vidare till `dokument_index\index.md`.
8. Alla nya beständiga dokument/datafiler ska listas i `dokument_index\index.md`, **utom** lokala körartefakter under `tmp`.
9. Dokumentindex ska verifieras med regressionstest.
10. Dokumentindex-testet är obligatoriskt och ska alltid köras när beständiga dokument/datafiler skapas, ändras, flyttas eller tas bort.
11. När innehållet i `raw_data` ändras ska `syntetisk_data\common\kallinventering.md` uppdateras och verifieras med separat regressionstest.
12. En `raw_data`-ändring är inte klar förrän relevant påverkan på `syntetisk_data` har analyserats och spårats i `syntetisk_data\common\kallinventering.md`.
13. Varje rapporterad regressionskörning i `Regression Mode` ska dokumenteras under `tmp\regression_local\<owner>\reports\YYYYMMDDvN`.
14. Varje verifierat regressionsfel ska få en egen katalog `RegressionErrorNN` med utvecklarvänlig felrapport på engelska.
15. Ett `failed` test får inte rapporteras under `tmp\regression_local\<owner>\reports` förrän felet verifierats minst tre gånger.
16. Lokala körartefakter under `tmp` ska inte läggas in i `dokument_index\index.md`.
17. Körningar i `Learning Mode` får inte skapa rapportpaket utanför `tmp`; lärdomar ska i stället skrivas tillbaka till testdokumentationen.

## Förväntad arbetsordning

1. Samla in data till `raw_data`
2. Strukturera data i `syntetisk_data`
3. Bygg eller uppdatera verktyg i `tools\source`
4. Lägg körbara entrypoints i `runtime`
5. Dokumentera verktygen i `tools\docs`
6. Publicera färdiga manualer i relevant underkatalog i `manuals`
7. Uppdatera `dokument_index\index.md`
8. Kör alltid dokumentindex-testet i `runtime\test-document-index.ps1`
9. Om `raw_data` har ändrats, uppdatera `syntetisk_data\common\kallinventering.md` och kör `runtime\test-kallinventering-coverage.ps1`
10. Uppdatera därefter alla berörda syntetiska dokument innan arbetet anses klart
11. Om regressionstest körs, uppdatera först testfallet med lärdomar och skriv endast rapportpaket till `tmp\regression_local\<owner>\reports` i `Regression Mode` för passerade eller verifierade fallerade tester

## Runtime-understruktur

När ett verktyg får många entrypoints ska `runtime` inte fyllas med alla interna POC-/hjälpskript. Använd i stället:

- `runtime\windows\<tool>\...` för Windows-specifika körskript
- `runtime\docker\<tool>\...` för framtida container-/control-plane-skript
- `runtime\*.ps1` endast för stabila och frekvent använda root-wrappers

För Copilot-admin används:

- `runtime\windows\copilot-admin\bridge`
- `runtime\windows\copilot-admin\terminal`
- `runtime\windows\copilot-admin\pty`
- `runtime\windows\copilot-admin\node-pty`
