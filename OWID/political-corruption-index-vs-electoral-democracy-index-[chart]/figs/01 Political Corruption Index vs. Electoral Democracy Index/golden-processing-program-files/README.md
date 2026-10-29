# Golden processing program: 01 Political Corruption Index vs. Electoral Democracy Index

View: https://ourworldindata.org/grapher/political-corruption-index-vs-electoral-democracy-index

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Political Corruption Index`: table `vdem_multi_with_regions`, column `corruption_vdem`, rows where estimate = 'best'
- `Electoral Democracy Index`: table `vdem_multi_with_regions`, column `electdem_vdem`, rows where estimate = 'best'
- `World region according to OWID`: not compared (OWID's world region (map and scatter colour), not a V-Dem indicator)

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
