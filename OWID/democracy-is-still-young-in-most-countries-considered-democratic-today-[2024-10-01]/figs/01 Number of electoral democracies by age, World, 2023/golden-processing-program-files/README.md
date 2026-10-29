# Golden processing program: 01 Number of electoral democracies by age, World, 2023

View: https://ourworldindata.org/grapher/number-electoral-democracies-age?tab=discrete-bar&time=2023&country=~OWID_WRL

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `91 years +`: table `vdem_num_countries`, column `num_countries_years_in_electdem`, rows where category = '91+ years'
- `61-90 years`: table `vdem_num_countries`, column `num_countries_years_in_electdem`, rows where category = '61-90 years'
- `31-60 years`: table `vdem_num_countries`, column `num_countries_years_in_electdem`, rows where category = '31-60 years'
- `19-30 years`: table `vdem_num_countries`, column `num_countries_years_in_electdem`, rows where category = '19-30 years'
- `Electoral democracies aged 1-18 years`: table `vdem_num_countries`, column `num_countries_years_in_electdem`, rows where category = '1-18 years'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
