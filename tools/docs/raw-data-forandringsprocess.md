# Raw data - förändringsprocess

Detta dokument fastställer vad som **måste** hända när innehållet i `raw_data` förändras.

## Syfte

Säkerställa att nya eller ändrade råkällor inte bara indexeras och listas, utan också analyseras och förs in i relevant syntetisk dokumentation.

## När processen ska användas

Processen gäller när en fil i `raw_data`:

- skapas
- ändras
- flyttas
- tas bort

## Obligatorisk arbetsordning

1. Uppdatera `dokument_index\index.md`
2. Uppdatera `syntetisk_data\common\kallinventering.md`
3. Analysera källans påverkan på befintligt syntetiskt data
4. Uppdatera alla relevanta dokument under `syntetisk_data`
5. Uppdatera spårbarheten i `kallinventering.md` så att berörda syntetiska dokument listas
6. Kör `.\runtime\test-kallinventering-coverage.ps1`
7. Kör `.\runtime\test-document-index.ps1`

## Obligatoriska beslut per råkälla

För varje ny eller ändrad råkälla måste följande avgöras och dokumenteras i `syntetisk_data\common\kallinventering.md`:

- vad källan tillför
- vilka begränsningar den har
- hur den ska användas
- vilka syntetiska dokument som påverkas
- om utfallet blev:
  - `Uppdaterad` - syntetiska dokument ändrades
  - `Analyserad - ingen ytterligare påverkan` - källan bedömdes men gav ingen ny användbar information

## Spårbarhetsregel

Om `kallinventering.md` säger att en råkälla påverkar ett syntetiskt dokument måste det dokumentet också referera till råkällan i sin egen dokumentation, normalt under `## Källor`.

## Tolkning av testfel

- Fel i `test-document-index.ps1` betyder att repositoryts beständiga filer inte är korrekt indexerade.
- Fel i `test-kallinventering-coverage.ps1` betyder att `raw_data` inte längre är korrekt analyserat och spårat in i det syntetiska lagret.

## Viktig princip

Att bara lägga till en fil i `kallinventering.md` räcker inte. En `raw_data`-förändring är inte klar förrän dess påverkan på `syntetisk_data` är bedömd, dokumenterad och verifierad med test.
