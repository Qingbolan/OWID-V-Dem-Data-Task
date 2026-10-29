# Golden processing program: 01 Meaningful democratic electoral institutions

View: https://ourworldindata.org/grapher/democratic-electoral-institutions-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Electoral democracy`: table `vdem_multi_without_regions`, column `electdem_dich_row_owid`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
