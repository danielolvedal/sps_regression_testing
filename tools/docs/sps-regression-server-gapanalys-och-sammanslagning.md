# Gapanalys och sammanslagning av `sps-regression-server`

Detta dokument sammanfattar hur materialet i `C:\docker\sps-regression-server` förhåller sig till det nuvarande SPS-repositoryt och vad som krävs för att slå samman initiativen.

## Syfte

Målet är att undvika att två separata projekt driver samma regressionsidé i olika former.

Den här analysen utgår från att:

- SPS-repositoryt redan har fungerande arbetsmodeller för dokumentstyrda regressionstester
- den svåraste praktiska POC-frågan i `sps-regression-server` - hur man hanterar Microsoft-login och MFA i verklig drift - i praktiken har lösts här genom delad synlig browser-session
- nästa steg därför inte är ännu en fristående POC, utan en sammanslagen målbild där detta repository blir den operativa kärnan

## Källmaterial från `C:\docker\sps-regression-server`

Följande externa dokument låg till grund för analysen:

- `docs\index.md`
- `docs\reports\phase-0-final-report.md`
- `docs\implementation\phase-0-implementation.md`
- `docs\specifications\project-scope.md`
- `docs\specifications\implementation-roadmap.md`
- `docs\specifications\architecture-analysis.md`
- `docs\specifications\environment-management.md`
- `docs\specifications\shared-test-library.md`
- `docs\specifications\interactive-web-interface.md`
- `docs\specifications\mfa-operating-model.md`
- `phase0\README.md`

## Huvudslutsats

`sps-regression-server` fastnade i en container- och Playwright-orienterad Phase 0, medan detta repository redan har kommit längre inom flera områden som faktiskt krävs för användbar SPS-regression:

- verkligt körbara regressionstestfall i stage
- delad synlig browser-session med användarledd inloggning
- dokumenterade körlägen för `Learning Mode` och `Regression Mode`
- spårbara testrapporter
- regressionstestkatalog och beroendegraf
- återföring av lärdomar direkt in i testdefinitionerna

Det nya projektet bör därför inte behandlas som en separat produkt som ska ersätta detta repository. Det bör i stället behandlas som ett **idédokument och en arkitektur-/roadmap-källa** som normaliseras in i SPS-repositoryts struktur.

## Gapanalys

| Område | `sps-regression-server` | Nuvarande SPS-repo | Gap / slutsats |
| --- | --- | --- | --- |
| Login/MFA POC | Phase 0 Playwright-POC för Microsoft-login och manuell MFA | Fungerande delad synlig browser med riktig användarinloggning och 5-minuters väntregel | SPS-repot har en mer praktisk operativ modell för manuella körningar |
| Körbara regressioner | Endast login-POC, inga fulla affärsflöden | Dokumenterade och delvis körda regressioner A-G | SPS-repot ligger klart före |
| Resultatrapportering | Tänkta rapportytor och artefaktmodell | Faktiska `test_reports\YYYYMMDDvN` med summary + felrapporter | SPS-repot ligger före |
| Regressionstestkatalog | Tänkta shared definitions | Namngiven katalog + Mermaid-beroenden + testfiler | SPS-repot ligger före för manuella regressionsflöden |
| Operatörsflöde | Planerad web UI | Copilot CLI + samma terminalfönster + delad browser | SPS-repot har bättre handhavande nu, men saknar admin/control plane |
| Miljömodell | Tydligt definierad environment registry | Stage-fokuserat i praktiken, viss dokumenterad host-separation | Gap: central miljömodell saknas |
| Multi-user / role testing | Krav definierade men ej lösta | Praktiskt löst för delad loginmodell, men ännu inte katalogiserat som identitets-/rollager | Gap: saknar strukturerad identity registry |
| Shared test library | Tydlig målbild för `O:\...TEST-Library` | Ingen sådan synkmodell ännu | Gap: återstår |
| Policy engine | Dokumenterad målbild | Manuella regler i dokumentation | Gap: återstår |
| Docker/control plane | Container-first arkitektur och web interface beskriven | Windows-/PowerShell-/browser-debugging-first operativ modell | Gap: återstår, men bör byggas runt nuvarande arbetssätt i stället för att ersätta det |
| API-regressioner | Finns i målarkitekturen | Ej etablerat i detta repo | Gap: återstår |
| Retention / audit services | Beskrivna som plattformsfunktioner | Rapporter och artefakter finns, men ingen generell retentionstjänst | Gap: återstår |

## Vad som bör migreras från det externa projektet

Det som är värdefullt att föra över är främst **arkitektur, begrepp och roadmap**, inte Phase 0-koden som produktkärna.

### Bör tas över konceptuellt

- environment registry-tänket
- shared test library-modellen
- operator/control-plane-tänket
- tydlig separering mellan testdefinitioner och körresultat
- identity/security boundary-tänket
- retention/audit-modellen

### Bör inte tas över som primär operativ modell

- antagandet att Playwright-baserad containerlogin är den centrala vägen för SPS
- antagandet att MFA-problemet måste lösas genom ren browserautomation innan affärsregressioner kan köras
- antagandet att operatören främst ska arbeta i ett separat web UI innan testbibliotek och flöden är stabila

## Rekommenderad sammanslagningsstrategi

### 1. Gör detta repository till primär produkt

Det här repo:t bör vara den plats där:

- regressionstestdefinitioner lever
- körbara runtime-skript lever
- testrapporter lever
- regressionstestkatalogen och beroendegrafen lever
- framtida admin-/control-plane-verktyg dokumenteras och byggs

### 2. Behandla `sps-regression-server` som referens- och idékälla

Det externa projektet bör inte fortsätta som en parallell produktlinje. Dess dokumentation bör i stället successivt normaliseras till:

- `tools\docs` för styrande verktygsdokument
- `tools\docs\road-map` för framtida steg
- `tools\docs\decissions` för låsta verktygsbeslut

### 3. Bygg en control plane runt nuvarande Copilot-arbetssätt

I stället för att bygga en helt separat webapplikation som ersätter dagens arbetssätt bör nästa steg vara att lägga ett administrativt lager ovanpå det som redan fungerar:

- standardiserade kommandon/prompter
- logg- och rapportvisning
- visualisering av beroendegraf
- run-historik
- enklare start av dokumenterade regressioner

## Genomförbarhet för den nya idén

## Övergripande bedömning

Idén är **genomförbar**, men inte som en ren containerlösning som ensam äger browser, Windows-session och Copilot-terminal.

Den genomförbara målbilden är i stället:

1. **Dockeriserad control plane**
2. **Host-side runner på Windows**
3. **Copilot CLI som exekveringsmotor för dokumentstyrda uppgifter**
4. **Delad synlig browser-session på värdmaskinen**

## Vad som är realistiskt

### Realistiskt

- en Docker-hostad webb- eller terminalnära adminyta
- vyer för loggar, rapporter, testkatalog och Mermaid-graf
- knappar eller mallar för att generera uniforma Copilot-kommandon som:
  - `kör regressionstest`
  - `kör regressionstest A`
  - `gå in i learning mode`
  - `uppdatera regressionstest B`
- orkestrering av lokala PowerShell-entrypoints
- indexering av `test_reports`, `testing\regression_test` och andra lokala artefakter
- metadata-lager för test, miljöer, roller och körhistorik

### Inte realistiskt som ren första lösning

- att en Linux-container ensam ska styra den synliga Windows-browsern där användaren själv loggar in
- att containern utan vidare ska “skriva i exakt samma Copilot-fönster” som användaren använder nu
- att MFA, delad browser och Copilot CLI ska bli helt friktionsfri enbart genom en web UI-front

## Viktig arkitekturinsikt

Det som fungerar idag är **host-bundet**:

- synlig Edge/Chrome
- remote debugging på Windows
- PowerShell-runtime
- interaktiv Copilot CLI-session

Därför bör Docker-lagret fungera som **control plane och metadata-/UI-lager**, medan den faktiska exekveringen görs via en lokal Windows-runner som:

- startar browser-sessioner
- läser/uppdaterar testfiler
- kör runtime-skript
- anropar Copilot CLI
- skriver tillbaka loggar och rapportpekare

## Rekommenderad målarkitektur

| Lager | Rekommendation |
| --- | --- |
| Control plane | Docker-hostad adminyta/API |
| Exekvering | Lokal Windows-runner |
| Interaktiv AI | Copilot CLI |
| UI-testning | Delad synlig browser med remote debugging |
| Testdefinitioner | `testing\regression_test` + framtida delat bibliotek |
| Rapporter | `test_reports` |
| Miljö-/rollmetadata | Ny lokal metadata-/konfigurationsmodell |

## Konkreta gap som återstår före sammanslagen lösning

1. **Administrativt gränssnitt** för att starta och följa körningar
2. **Metadata-lager** för miljöer, roller, DS-scope och kommandomallar
3. **Terminal-/session bridge** om en UI ska kunna driva Copilot-kommandon utan manuellt copy/paste
4. **Shared test library** för återanvändbara definitioner mellan installationer
5. **Host-runner-kontrakt** mellan Docker control plane och Windows-värden
6. **Strukturerad loggmodell** för Copilot-körningar, runtime-skript och browser-sessioner
7. **Säkerhetsmodell** för regression identities, MFA-status och eventuell framtida credential lifecycle

## Rekommenderad slutsats

Den bästa vägen framåt är:

1. slå fast att detta SPS-repository är huvudprojektet
2. använda `sps-regression-server` som design- och roadmap-källa
3. bygga nästa steg som en **control plane ovanpå nuvarande fungerande arbetssätt**, inte som en ersättare för det
4. hålla browserstyrning och interaktiv Copilot-exekvering på Windows-värden, även om adminytan körs i Docker

Det gör att ni kan få:

- samma arbetsmodell som idag
- bättre operatörsstöd
- bättre visualisering
- återanvändbara kommandon
- bättre loggning och uppföljning

utan att först behöva lösa ett onödigt svårt “allt i containern”-problem.
