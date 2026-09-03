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

Agentkontrakt för loggning:

- `tool_error_logs` är reserverad för fasta verktyg/infra-loggar (install, start, stop, reinstall, Playwright-/node-starts etc.). Agenter får endast skriva verktygsinfrastruktur-loggar hit.
- Agenter får inte använda `tool_error_logs` för test-, regressions- eller temporära loggar. All testrelaterad loggning ska skrivas under `tmp`.
- Sök och använd alltid `dokument_index\index.md` och `tools\docs\katalogstruktur.md` för aktuella regler innan du skriver loggar.

## Standardstart för UI-arbete

När uppgiften kräver inloggning, UI-observation eller gemensam browserstyrning ska sessionen normalt starta med:

```powershell
.\runtime\start-collaborative-stage-browser.ps1
```

Arbetsmodellen för detta finns i:

- `tools\docs\browser-samarbete-stage-session.md`

## Copilot-admin testisolering

Det är **obligatoriskt** att hålla användarens/produktionssessionens Copilot-motor separerad från automatiserade tester.

- Produktionssessionens runner-state finns i `tmp\copilot_admin_runner_state`.
- Vanliga backend-, frontend- och dev-E2E-tester får **aldrig** läsa från eller skriva till `tmp\copilot_admin_runner_state`.
- Vanliga dev-tester ska använda injicerad host-state och testköer under `tmp\copilot_admin_control_plane`.
- Full real-E2E får prata med en riktig Copilot CLI, men bara via en **separat dold testsession** med egen state-katalog.
- Den isolerade real-E2E-state-katalogen ska vara `tmp\copilot_admin_control_plane\real_visible_e2e\runner_state`, normalt via miljövariabeln `COPILOT_ADMIN_RUNNER_STATE_DIR`.
- Real-E2E ska normalt använda separat browserport `9322`, inte användarens produktions-/samarbetsbrowser på `9222`.
- Om ett test behöver verifiera verklig Copilot-input ska testet starta eller använda den isolerade dolda testsessionen; det får inte återanvända användarens synliga Copilot-session.
- Ett E2E-resultat är ogiltigt om testet har skrivit testprompter till produktionskön `tmp\copilot_admin_runner_state\node-pty-copilot-input-queue`.

Den detaljerade testmodellen finns i:

- `tools\docs\copilot-admin-e2e-critical-coverage.md`

## Dokumentstruktur är styrande

Den fastlåsta katalogstrukturen och reglerna för hur material sorteras finns i:

- `tools\docs\katalogstruktur.md`
- `tools\docs\raw-data-forandringsprocess.md`
- `tools\docs\regressionstest-arbetsmodell.md`
- `tools\docs\regression-rapportering.md`

## Förväntningar på nya artefakter

- Om du skapar ett nytt beständigt dokument ska du också uppdatera `dokument_index\index.md`.
- Undantag: lokala körartefakter under `tmp` ska inte indexeras i `dokument_index\index.md`.
- Om du skapar ett nytt verktyg ska det få källkod i `tools\source` och en körbar entrypoint i `runtime` när det är relevant.
- Om du extraherar data från systemet ska originaluttaget sparas i `raw_data`.
- Om du sammanfattar eller normaliserar rådata för AI-bruk ska resultatet sparas i `syntetisk_data`.

## Tolkning av regressionstest-kommandon

- Om användaren ber om att köra ett regressionstest och meddelandet innehåller `regression` eller en uppenbar felstavning av ordet ska det tolkas som en begäran om regressionstestning.
- Promotade testdefinitioner och manuella scenarier finns i `testing\regression_test`.
- Personliga utkast och Learning Mode-kandidater ska ligga i `testing\regression_drafts\<github-anvandare>`.
- Regressionstest ska i första hand hittas via `testing\regression_test\regression-test-catalog.md`, där namn, sammanfattning och beroenden finns.
- Den renderbara beroendegrafen för regressionstester finns i `testing\regression_test\regression-test-dependencies.mmd` och ska hållas synkad med katalogen och testfilerna.
- Lokala körresultat och felrapporter ska skrivas under `tmp\regression_local\<owner>\reports`.
- UI-regressioner ska i första hand utföras genom att agenten följer dokumenterade teststeg, inte genom hårdkodad browserautomation.
- Körbara runtime-skript ska främst användas för stabila strukturtester som dokumentindex och källinventering.
- Om användaren signalerar att testet ska utvecklas, uppdateras, förbättras eller provas ska agenten gå in i `Learning Mode`.
- I `Learning Mode` ska agenten uppdatera testdefinitioner och kataloger men **inte** skapa rapporter utanför den lokala `tmp`-ytan.
- Om användaren ber om faktisk verifiering av ett befintligt test ska agenten använda `Regression Mode`.
- Om avsikten är oklar ska agenten fråga exakt: `Ska jag köra befintliga regressionstester?`
- Efter en UI-regressionskörning ska agenten uppdatera testfallet med återanvändbara lärdomar som gör framtida körningar snabbare.
- Efter varje regressionskörning ska agenten bara skriva en testrapport under `tmp\regression_local\<owner>\reports\YYYYMMDDvN` i `Regression Mode`, när utfallet är passerat eller när ett fel är verifierat.

## Mandatory krav

- Dokumentindex-testet **ska alltid köras** när ett beständigt dokument eller en beständig datafil skapas, ändras, flyttas eller tas bort.
- Källinventeringstestet **ska alltid köras** när en fil i `raw_data` skapas, ändras, flyttas eller tas bort.
- Regression dependency-testet **ska alltid köras** när ett namngivet regressionstest, `regression-test-catalog.md` eller `regression-test-dependencies.mmd` skapas, ändras, flyttas eller tas bort.
- Ingen dokumentationsrelaterad uppgift är klar förrän `.\runtime\test-document-index.ps1` har körts och passerat.
- Ingen `raw_data`-relaterad dokumentationsuppgift är klar förrän `.\runtime\test-kallinventering-coverage.ps1` har körts och passerat.
- Ingen regressionstest-relaterad dokumentationsuppgift är klar förrän `.\runtime\test-regression-dependencies.ps1` har körts och passerat.
- Testrapporter i `tmp\regression_local\<owner>\reports` ska skrivas på formell engelska.
- Om testet fallerar ska `dokument_index\index.md` uppdateras innan arbetet avslutas.
- Om källinventeringstestet fallerar ska `syntetisk_data\common\kallinventering.md` uppdateras innan arbetet avslutas.
- Om `raw_data` ändras ska även berörda dokument under `syntetisk_data` analyseras och uppdateras; att bara lägga till källan i `kallinventering.md` räcker inte.
- Varje `failed` regressionstest får endast få en detaljerad felrapport för utvecklare efter minst tre reproduktioner med samma utfall.
