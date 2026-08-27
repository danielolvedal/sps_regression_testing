# AGENTS.md

Detta repository används för att samla, strukturera och producera dokumentation, testunderlag och verktyg kring SPS. **Läs alltid `dokument_index\index.md` först** innan du börjar söka fritt.

## Primär navigering

1. Läs `dokument_index\index.md`
2. Följ sedan indexets referenser till rätt dokument, rådata, syntetisk data, verktygsdokument eller runtime-skript
3. Uppdatera indexet när du skapar nya beständiga dokument

## Arbetsprinciper

- Använd Windows-sökvägar med `\`.
- Lägg rå extraktion och referensmaterial i `raw_data`.
- Lägg AI-strukturerad bearbetning i `syntetisk_data`.
- Lägg verktygskällkod i `tools\source`.
- Lägg verktygsdokumentation i `tools\docs`.
- Lägg verktygsbeslut i `tools\docs\decissions`.
- Lägg verktygsroadmaps i `tools\docs\road-map`.
- Lägg körklara entrypoints i `runtime`.
- Lägg färdiga manualer i relevant katalog under `manuals`.
- Lägg temporära filer **endast** i repositoryrotens `tmp`. Skapa aldrig `tmp`-kataloger under `tools` eller andra underkataloger.

## Standardstart för UI-arbete

När uppgiften kräver inloggning, UI-observation eller gemensam browserstyrning ska sessionen normalt starta med:

```powershell
.\runtime\start-collaborative-stage-browser.ps1
```

Arbetsmodellen för detta finns i:

- `tools\docs\browser-samarbete-stage-session.md`

## Dokumentstruktur är styrande

Den fastlåsta katalogstrukturen och reglerna för hur material sorteras finns i:

- `tools\docs\katalogstruktur.md`
- `tools\docs\raw-data-forandringsprocess.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `tools\docs\regression-rapportering.md`

## Förväntningar på nya artefakter

- Om du skapar ett nytt beständigt dokument ska du också uppdatera `dokument_index\index.md`.
- Undantag: innehåll under `test_reports` ska inte indexeras i `dokument_index\index.md`.
- Om du skapar ett nytt verktyg ska det få källkod i `tools\source` och en körbar entrypoint i `runtime` när det är relevant.
- Om du extraherar data från systemet ska originaluttaget sparas i `raw_data`.
- Om du sammanfattar eller normaliserar rådata för AI-bruk ska resultatet sparas i `syntetisk_data`.

## Tolkning av regressionstest-kommandon

- Om användaren ber om att köra ett regressionstest och meddelandet innehåller `regression` eller en uppenbar felstavning av ordet ska det tolkas som en begäran om regressionstestning.
- Testdefinitioner och manuella scenarier finns i `testing\regression_test`.
- Regressionstest ska i första hand hittas via `testing\regression_test\regression-test-catalog.md`, där namn, sammanfattning och beroenden finns.
- Den renderbara beroendegrafen för regressionstester finns i `testing\regression_test\regression-test-dependencies.mmd` och ska hållas synkad med katalogen och testfilerna.
- Tidigare körresultat och felrapporter finns i `test_reports`.
- UI-regressioner ska i första hand utföras genom att agenten följer dokumenterade teststeg, inte genom hårdkodad browserautomation.
- Körbara runtime-skript ska främst användas för stabila strukturtester som dokumentindex och källinventering.
- Om användaren signalerar att testet ska utvecklas, uppdateras, förbättras eller provas ska agenten gå in i `Learning Mode`.
- I `Learning Mode` ska agenten uppdatera testdefinitioner och kataloger men **inte** skapa rapporter i `test_reports`.
- Om användaren ber om faktisk verifiering av ett befintligt test ska agenten använda `Regression Mode`.
- Om avsikten är oklar ska agenten fråga exakt: `Ska jag köra befintliga regressionstester?`
- Efter en UI-regressionskörning ska agenten uppdatera testfallet med återanvändbara lärdomar som gör framtida körningar snabbare.
- Efter varje regressionskörning ska agenten bara skriva en testrapport under `test_reports\YYYYMMDDvN` i `Regression Mode`, när utfallet är passerat eller när ett fel är verifierat.

## Mandatory krav

- Dokumentindex-testet **ska alltid köras** när ett beständigt dokument eller en beständig datafil skapas, ändras, flyttas eller tas bort.
- Källinventeringstestet **ska alltid köras** när en fil i `raw_data` skapas, ändras, flyttas eller tas bort.
- Regression dependency-testet **ska alltid köras** när ett namngivet regressionstest, `regression-test-catalog.md` eller `regression-test-dependencies.mmd` skapas, ändras, flyttas eller tas bort.
- Ingen dokumentationsrelaterad uppgift är klar förrän `.\runtime\test-document-index.ps1` har körts och passerat.
- Ingen `raw_data`-relaterad dokumentationsuppgift är klar förrän `.\runtime\test-kallinventering-coverage.ps1` har körts och passerat.
- Ingen regressionstest-relaterad dokumentationsuppgift är klar förrän `.\runtime\test-regression-dependencies.ps1` har körts och passerat.
- Testrapporter i `test_reports` ska skrivas på formell engelska.
- Om testet fallerar ska `dokument_index\index.md` uppdateras innan arbetet avslutas.
- Om källinventeringstestet fallerar ska `syntetisk_data\common\kallinventering.md` uppdateras innan arbetet avslutas.
- Om `raw_data` ändras ska även berörda dokument under `syntetisk_data` analyseras och uppdateras; att bara lägga till källan i `kallinventering.md` räcker inte.
- Varje `failed` regressionstest får endast få en detaljerad felrapport för utvecklare efter minst tre reproduktioner med samma utfall.
