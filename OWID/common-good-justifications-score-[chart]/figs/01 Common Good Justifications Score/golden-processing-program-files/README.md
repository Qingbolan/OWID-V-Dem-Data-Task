# Golden processing program: 01 Common Good Justifications Score

View: https://ourworldindata.org/grapher/common-good-justifications-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Common good justifications`: table `vdem_multi_with_regions`, column `justcomgd_polch_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
