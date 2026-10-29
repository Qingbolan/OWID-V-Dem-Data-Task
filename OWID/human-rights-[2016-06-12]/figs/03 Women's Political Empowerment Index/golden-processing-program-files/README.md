# Golden processing program: 03 Women's Political Empowerment Index

View: https://ourworldindata.org/grapher/women-political-empowerment-index?tab=line&time=earliest..latest&country=~OWID_WRL

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Women's Political Empowerment Index`: table `vdem_multi_with_regions`, column `wom_emp_vdem`, rows where estimate = 'best'
- `World region according to OWID`: not compared (OWID's world region (map and scatter colour), not a V-Dem indicator)

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
