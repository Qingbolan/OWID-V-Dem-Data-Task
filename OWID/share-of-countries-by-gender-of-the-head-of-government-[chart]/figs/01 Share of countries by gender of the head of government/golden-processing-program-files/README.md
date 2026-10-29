# Golden processing program: 01 Share of countries by gender of the head of government

View: https://ourworldindata.org/grapher/share-of-countries-by-gender-of-the-head-of-government

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Man is head of government`: table `vdem_num_countries`, column `num_countries_hog`, rows where category = 'Man'
- `Woman is head of government`: table `vdem_num_countries`, column `num_countries_hog`, rows where category = 'Woman'
- The chart stacks the columns in relative mode: each value is shown as a percentage of the row total.

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
