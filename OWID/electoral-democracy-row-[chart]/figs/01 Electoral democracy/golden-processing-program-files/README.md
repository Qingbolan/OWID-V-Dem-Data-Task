# Golden processing program: 01 Electoral democracy

View: https://ourworldindata.org/grapher/electoral-democracy-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Political regime`: table `vdem_uni_without_regions`, column `regime_redux_row_owid`

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
