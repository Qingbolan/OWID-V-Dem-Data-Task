# Golden processing program: 01 Access to justice for men

View: https://ourworldindata.org/grapher/access-to-justice-men-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Access to justice for men`: table `vdem_multi_without_regions`, column `accessjust_m_row`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
