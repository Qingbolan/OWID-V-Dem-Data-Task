# Golden processing program: 01 Foreign Policy Free from Interference of other States Score

View: https://ourworldindata.org/grapher/foreign-policy-free-from-interference-of-other-states-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Foreign policymaking free from foreign influence`: table `vdem_multi_with_regions`, column `int_auton_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
