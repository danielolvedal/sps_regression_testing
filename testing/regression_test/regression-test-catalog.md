# Regressionskatalog

Detta dokument är huvudlistan över namngivna regressionstester, deras syfte och deras beroenden.

## Syfte

Göra det möjligt att referera till regressionstester med ett kort och stabilt namn när ett test ska köras, uppdateras eller utökas.

## Standard för referenser

Varje regressionstest ska ha:

- ett **Catalog Key** för kort referens, till exempel `A` eller `B`
- ett **Test-ID** för unik identifiering
- en **kort sammanfattning**
- en tydlig lista över **beroenden**

När en användare säger exempelvis:

- `uppdatera regressionstest A`
- `kör test B`
- `lägg till ett steg efter A`

ska agenten först läsa denna katalog och därefter öppna rätt testfil.

## Testöversikt

| Catalog Key | Dependency | Test ID | Summary | File |
| --- | --- | --- | --- | --- |
| `A` | `-` | `regression-kontrakt-anna-serviceportal-login` | Find a user via contract search and end on that user's logged-in service portal page through assisted login. | `testing\regression_test\kontrakt-sok-anna-serviceportal-login.md` |
| `B` | `A -> B` | `regression-serviceportal-nytt-kontrakt-migrated-ds` | Start from the logged-in service portal page created by A, click Nytt kontrakt, then find a migrated DS through Admin -> Migrate DS and verify the new-contract flow for that parking. | `testing\regression_test\serviceportal-nytt-kontrakt-migrated-ds.md` |
| `C` | `A -> C` | `regression-serviceportal-nytt-kontrakt-non-migrated-ds` | Start from the logged-in service portal page created by A, click Nytt kontrakt, then find a non-migrated DS through Admin -> Migrate DS and verify that a product can be purchased for that parking. | `testing\regression_test\serviceportal-nytt-kontrakt-non-migrated-ds.md` |
| `D` | `-` | `regression-document-index-coverage` | Validate document index coverage for all tracked persistent documentation and data files. | `testing\regression_test\document-index-coverage.md` |
| `E` | `-` | `regression-kallinventering-coverage` | Validate raw-data coverage and downstream synthetic-data traceability in kallinventering.md. | `testing\regression_test\kallinventering-coverage.md` |
| `F` | `-` | `regression-regression-dependency-synchronization` | Validate synchronization between regression test metadata, the regression catalog, and the standalone Mermaid dependency file. | `testing\regression_test\regression-dependency-coverage.md` |
| `G` | `B -> G, K -> G` | `regression-serviceportal-checkout-verify-and-create-contract` | Start from the checkout page created by B or K, verify checkout and contract creation, and retry the source-specific setup flow until one DS passes or every relevant DS candidate has been tested. | `testing\regression_test\serviceportal-checkout-verifiering-och-skapa-kontrakt.md` |
| `H` | `-` | `regression-kundtjanst-svensk-lokalisering-och-terminologi` | Audit every Customer Service Center menu and page in stage for non-Swedish UI text and Swedish terminology consistency. | `testing\regression_test\kundtjanst-svensk-lokalisering-och-terminologi.md` |
| `I` | `-` | `regression-wallboard-messages-layout-och-acknowledge` | Create six active wallboard messages in Admin, verify FullScreen, HalfScreen and OneThirdScreen rendering in Stage, and confirm that one message requires acknowledge. | `testing\regression_test\wallboard-messages-layout-och-acknowledge.md` |
| `J` | `-` | `regression-ds-routing-inventory-sps-vs-legacy` | Build and maintain the shared DS routing inventory by collecting all DS numbers/names and classifying each DS as SPS-stage or legacy-stage through Create New Contract step 1. | `testing\regression_test\ds-routing-inventory-sps-vs-legacy.md` |
| `K` | `A + J -> K` | `regression-serviceportal-nytt-kontrakt-sps-ds` | Start from the logged-in service portal page created by A, use J's DS routing inventory as the SPS-DS source, and verify the new-contract flow for that parking. | `testing\regression_test\serviceportal-nytt-kontrakt-sps-ds.md` |

## Beroendegraf

Den fristående Mermaid-koden finns i:

- `testing\regression_test\regression-test-dependencies.mmd`

## Tolkning

- `A` är ett fristående starttest.
- `A` ska avslutas på kundens inloggade serviceportalsida.
- `B` bygger på att `A` först etablerar rätt inloggad serviceportal-session och startar därefter med `Nytt kontrakt` innan en migrerad site/ett migrerat DS med status `Migrated` i `Admin -> Migrate DS` används. Kedjan `B -> G` testar kontraktsskapande på migrerade DS.
- `G` bygger vidare på slutläget i `B` eller `K` och verifierar checkout- samt skapa-kontrakt-steget. Om `G` fallerar ska vald källkedja upprepas med nya relevanta DS-kandidater tills ett DS passerar eller alla kandidater för den kedjan har prövats.
- `C` bygger på att `A` först etablerar rätt inloggad serviceportal-session och startar därefter med `Nytt kontrakt` innan ett DS som inte är migrerat används.
- `D`, `E` och `F` är fristående strukturregressioner utan beroenden till UI-flödena.
- `H` är ett fristående Kundtjänst-/CSC-UI-test som granskar alla stage-menyer mot engelska, blandade eller andra utländska UI-uttryck och normaliserar terminologin till god svenska.
- `I` är ett fristående Admin-/CSC-UI-test som skapar sex wallboardmeddelanden, verifierar layoutfamiljerna i Stage och kontrollerar att `Acknowledge` verkligen kräver kvittens.
- `J` är ett fristående Kundtjänst-/CSC-dataregressionstest som skapar och håller uppdaterad den gemensamma DS-routinglistan för SPS kontra legacy.
- `K` bygger på både `A` och `J`: `A` etablerar kundens inloggade serviceportal-session och `J` är den styrande DS-förutsättningen. Kedjan `K -> G` testar kontraktsskapande på DS som finns i SPS genom att välja DS med `routing: "sps-stage"` från `raw_data\ds-routing-inventory.json`. J behålls fristående så listan kan uppdateras utan att först köra A.
- Nya tester ska läggas till i tabellen och i Mermaid-grafen när de införs.

## Underhållsregel

När ett regressionstest skapas, byter syfte eller får nya beroenden ska både denna katalog och `testing\regression_test\regression-test-dependencies.mmd` uppdateras samtidigt.
