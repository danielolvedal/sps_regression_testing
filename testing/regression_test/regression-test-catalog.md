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
| `G` | `B -> G` | `regression-serviceportal-checkout-verify-and-create-contract` | Start from the checkout page created by B, verify that customer data and pricing are correct, then accept the terms and create the contract. | `testing\regression_test\serviceportal-checkout-verifiering-och-skapa-kontrakt.md` |

## Beroendegraf

Den fristående Mermaid-koden finns i:

- `testing\regression_test\regression-test-dependencies.mmd`

## Tolkning

- `A` är ett fristående starttest.
- `A` ska avslutas på kundens inloggade serviceportalsida.
- `B` bygger på att `A` först etablerar rätt inloggad serviceportal-session och startar därefter med `Nytt kontrakt` innan ett DS med status `Migrated` används.
- `G` bygger vidare på slutläget i `B` och verifierar checkout- samt skapa-kontrakt-steget.
- `C` bygger på att `A` först etablerar rätt inloggad serviceportal-session och startar därefter med `Nytt kontrakt` innan ett DS som inte är migrerat används.
- `D`, `E` och `F` är fristående strukturregressioner utan beroenden till UI-flödena.
- Nya tester ska läggas till i tabellen och i Mermaid-grafen när de införs.

## Underhållsregel

När ett regressionstest skapas, byter syfte eller får nya beroenden ska både denna katalog och `testing\regression_test\regression-test-dependencies.mmd` uppdateras samtidigt.
