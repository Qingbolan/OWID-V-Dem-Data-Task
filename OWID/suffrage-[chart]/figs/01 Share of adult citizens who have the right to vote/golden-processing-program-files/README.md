# Golden processing program: 01 Share of adult citizens who have the right to vote

View: https://ourworldindata.org/grapher/suffrage

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Share of population with suffrage`: table `vdem_uni_with_regions`, column `suffr_vdem`
- `World region according to OWID`: not compared (OWID's world region (map and scatter colour), not a V-Dem indicator)

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
