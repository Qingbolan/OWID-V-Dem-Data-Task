# Golden processing program: 01 Transparent laws

View: https://ourworldindata.org/grapher/transparent-laws-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Transparent laws with predictable enforcement`: table `vdem_multi_without_regions`, column `transplaws_row`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
