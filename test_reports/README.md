# Test Reports

This folder contains results from completed regression reporting runs.

## Structure

- `YYYYMMDDvN` - one reported run with summaries and any verified defect folders
- `templates` - templates for future reports

## Rules

- all report content must be written in professional English
- each eligible regression run must create its own dated folder
- `summary.md` must always exist in a reported run folder
- each verified defect must get its own `RegressionErrorNN` folder
- failed regression outcomes must not be reported here before triple verification
- content under `test_reports` must not be indexed in `dokument_index\index.md`
- detailed reporting follows `tools\docs\regression-rapportering.md`
