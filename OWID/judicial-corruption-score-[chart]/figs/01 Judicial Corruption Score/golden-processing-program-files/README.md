# Golden processing program: 01 Judicial Corruption Score

View: https://ourworldindata.org/grapher/judicial-corruption-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Judicial Corruption Score`: table `vdem_multi_with_regions`, column `corr_jud_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
