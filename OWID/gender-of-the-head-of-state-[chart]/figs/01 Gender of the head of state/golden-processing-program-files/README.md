# Golden processing program: 01 Gender of the head of state

View: https://ourworldindata.org/grapher/gender-of-the-head-of-state

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Woman head of state (31st December)`: table `vdem_uni_without_regions`, column `wom_hos_vdem`

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
