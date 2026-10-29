# Golden processing program: 03 Countries by share of women in parliament

View: https://ourworldindata.org/grapher/countries-by-share-of-women-in-parliament

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `No women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '0% women'
- `Less than 10% women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '0-10% women'
- `10 - 20% women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '10-20% women'
- `20 - 30% women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '20-30% women'
- `30 - 40% women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '30-40% women'
- `40 - 50% women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '40-50% women'
- `50% or more women`: table `vdem_num_countries`, column `num_countries_wom_parl`, rows where category = '50%+ women'
- The chart stacks the columns in relative mode: each value is shown as a percentage of the row total.

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
