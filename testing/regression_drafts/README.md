# Regressionstestutkast

Den här katalogen innehåller användarspecifika regressionstestutkast som ännu inte är promotade till den delade katalogen `testing\regression_test`.

## Syfte

- hålla Learning Mode-iterationer separerade från delade, körbara regressionstester
- göra det tydligt vem som äger ett pågående testutkast
- låta backend och Copilot-admin UI visa draft-scope och ägare utan att blanda ihop utkast med promotade tester

## Struktur

- varje användare får en egen undermapp: `testing\regression_drafts\<github-anvandare>\`
- endast promotade tester ska ligga i `testing\regression_test\`
- lokala körartefakter och rapporter hör **inte** hemma här; de ska skrivas under `tmp\regression_local\<owner>\reports`

## Rekommenderad metadata för draft-tester

Ett draft-test bör använda samma grundformat som ett promotat test, men behöver inte ha `Catalog Key` förrän det ska promotas:

- `## Test-ID`
- `## Summary`
- `## Dependencies`
- `## Typ`
- `## Owner`
- `## Maintainers`

När ett draft-test blir stabilt ska det flyttas till `testing\regression_test`, registreras i `regression-test-catalog.md` och inkluderas i `regression-test-dependencies.mmd` om det får beroenden.
