# Golden processing program: 03 Rigorous and Impartial Public Administration Score

View: https://ourworldindata.org/grapher/rigorous-and-impartial-public-administration-score

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Rigorous and impartial public administration`: table `vdem_multi_with_regions`, column `public_admin_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
