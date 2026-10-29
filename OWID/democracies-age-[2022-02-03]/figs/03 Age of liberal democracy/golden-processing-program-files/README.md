# Golden processing program: 03 Age of liberal democracy

View: https://ourworldindata.org/grapher/age-of-liberal-democracy-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Age of liberal democracy`: table `vdem_uni_without_regions`, column `num_years_in_libdem_consecutive`

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
