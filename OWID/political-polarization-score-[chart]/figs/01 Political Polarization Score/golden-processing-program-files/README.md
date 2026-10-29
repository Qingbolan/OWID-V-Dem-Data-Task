# Golden processing program: 01 Political Polarization Score

View: https://ourworldindata.org/grapher/political-polarization-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Political polarization score`: table `vdem_multi_with_regions`, column `v2cacamps`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
