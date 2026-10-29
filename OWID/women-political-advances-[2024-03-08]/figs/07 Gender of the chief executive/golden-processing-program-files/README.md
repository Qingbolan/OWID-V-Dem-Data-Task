# Golden processing program: 07 Gender of the chief executive

View: https://ourworldindata.org/grapher/gender-of-chief-executive

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Woman chief executive (31st December)`: table `vdem_uni_without_regions`, column `wom_hoe_vdem`

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
