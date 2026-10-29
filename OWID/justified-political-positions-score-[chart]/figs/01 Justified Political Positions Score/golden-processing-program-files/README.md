# Golden processing program: 01 Justified Political Positions Score

View: https://ourworldindata.org/grapher/justified-political-positions-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Justified political positions`: table `vdem_multi_with_regions`, column `justified_polch_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
