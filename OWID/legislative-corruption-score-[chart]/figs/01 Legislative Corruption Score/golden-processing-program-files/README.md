# Golden processing program: 01 Legislative Corruption Score

View: https://ourworldindata.org/grapher/legislative-corruption-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Legislative Corruption Score`: table `vdem_multi_with_regions`, column `corr_leg_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
