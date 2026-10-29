# Golden processing program: 01 Liberal political institutions

View: https://ourworldindata.org/grapher/liberal-political-institutions-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Liberal political institutions`: table `vdem_multi_without_regions`, column `lib_dich_row`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
