# Golden processing program: 01 Countries that are long-standing liberal democracies

View: https://ourworldindata.org/grapher/countries-long-standing-liberal-democracies-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Closed autocracies`: table `vdem_num_countries`, column `num_countries_regime`, rows where category = 'closed autocracy'
- `Electoral autocracies`: table `vdem_num_countries`, column `num_countries_regime`, rows where category = 'electoral autocracy'
- `Electoral democracies`: table `vdem_num_countries`, column `num_countries_regime`, rows where category = 'electoral democracy'
- `Liberal democracies aged 1-18`: table `vdem_num_countries`, column `num_countries_years_in_libdem`, rows where category = '1-18 years'
- `aged 19-30`: table `vdem_num_countries`, column `num_countries_years_in_libdem`, rows where category = '19-30 years'
- `aged 31-60`: table `vdem_num_countries`, column `num_countries_years_in_libdem`, rows where category = '31-60 years'
- `aged 60-90`: table `vdem_num_countries`, column `num_countries_years_in_libdem`, rows where category = '61-90 years'
- `aged 91 +`: table `vdem_num_countries`, column `num_countries_years_in_libdem`, rows where category = '91+ years'
- The chart stacks the columns in relative mode: each value is shown as a percentage of the row total.

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
