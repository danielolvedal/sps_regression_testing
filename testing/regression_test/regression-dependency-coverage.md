# Regressionstest - regression dependency synchronization

Detta test säkerställer att alla namngivna regressionstester hålls synkade mellan testfilerna, regressionskatalogen och den fristående Mermaid-koden i `regression-test-dependencies.mmd`.

## Test-ID

regression-regression-dependency-synchronization

## Catalog Key

`F`

## Summary

Validate synchronization between regression test metadata, the regression catalog, and the standalone Mermaid dependency file.

## Dependencies

- none

## Varför testet är kritiskt

Om katalogen, testfilerna och Mermaid-diagrammet glider isär blir det snabbt oklart vilka tester som finns, vad de heter och vilka beroenden som gäller. Då riskerar nästa agent att köra fel test, missa ett beroende eller uppdatera bara en del av modellen.

## Vad som kontrolleras

Testet verifierar att:

- varje namngivet regressionstest har `Test-ID`, `Catalog Key`, `Summary` och `Dependencies`
- varje testfil finns med i `testing\regression_test\regression-test-catalog.md`
- katalogens `Test ID`, `Summary`, `Dependency` och `File` matchar testfilernas metadata
- `testing\regression_test\regression-test-dependencies.mmd` innehåller en nod för varje katalogpost
- Mermaid-filen innehåller rätt beroendepilar och inga extra testnoder eller beroenden

## Körning

```powershell
.\runtime\test-regression-dependencies.ps1
```

## Förväntat resultat

- Testet ska returnera exit code `0` när testfiler, katalog och Mermaid-kod är synkade.
- Testet ska returnera exit code `1` och lista avvikelser när metadata, katalog eller Mermaid-fil inte längre stämmer överens.

## Arbetsregel

Varje gång ett regressionstest skapas, byter namn, får nytt `Catalog Key`, nya beroenden eller ny sammanfattning ska:

1. testfilen uppdateras
2. `testing\regression_test\regression-test-catalog.md` uppdateras
3. `testing\regression_test\regression-test-dependencies.mmd` uppdateras
4. detta regressionstest alltid köras
