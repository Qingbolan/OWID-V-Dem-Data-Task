# Golden processing program: 01 Women's Civil Society Participation Index

View: https://ourworldindata.org/grapher/women-civil-society-participation-index

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Women's Civil Society Participation Index`: table `vdem_multi_with_regions`, column `wom_civ_soc_vdem`, rows where estimate = 'best'
- `World region according to OWID`: not compared (OWID's world region (map and scatter colour), not a V-Dem indicator)

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
