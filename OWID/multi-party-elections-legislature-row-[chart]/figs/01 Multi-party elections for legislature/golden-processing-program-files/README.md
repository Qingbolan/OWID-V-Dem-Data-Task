# Golden processing program: 01 Multi-party elections for legislature

View: https://ourworldindata.org/grapher/multi-party-elections-legislature-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Multiparty elections for legislature`: table `vdem_multi_without_regions`, column `electmulpar_leg_row`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
