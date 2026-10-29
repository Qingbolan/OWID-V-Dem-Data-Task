# Golden processing program: 01 Equality of Political Power across Social Groups Score

View: https://ourworldindata.org/grapher/equality-of-political-power-across-social-groups-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Equality of political power across social groups`: table `vdem_multi_with_regions`, column `socgr_pow_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
