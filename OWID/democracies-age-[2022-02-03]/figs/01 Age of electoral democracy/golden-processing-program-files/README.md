# Golden processing program: 01 Age of electoral democracy

View: https://ourworldindata.org/grapher/age-of-electoral-democracy

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Age of electoral democracy`: table `vdem_uni_without_regions`, column `num_years_in_electdem_consecutive`

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
