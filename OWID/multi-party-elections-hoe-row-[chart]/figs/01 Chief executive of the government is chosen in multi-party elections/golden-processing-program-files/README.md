# Golden processing program: 01 Chief executive of the government is chosen in multi-party elections

View: https://ourworldindata.org/grapher/multi-party-elections-hoe-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Multi-party elections for government's chief executive`: table `vdem_multi_without_regions`, column `electmulpar_hoe_row_owid`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
