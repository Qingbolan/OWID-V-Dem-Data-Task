# Golden processing program: 01 Countries that are democracies and autocracies

View: https://ourworldindata.org/grapher/democracies-autocracies-amb-row

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Closed autocracies`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'closed autocracy'
- `Probably closed autocracies`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'closed (maybe electoral) autocracy'
- `Probably electoral autocracy`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'electoral (maybe closed) autocracy'
- `Electoral autocracies`: table `vdem_num_countries`, column `num_countries_regime`, rows where category = 'electoral autocracy'
- ` Probably electoral autocracy`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'electoral autocracy (maybe electoral democracy)'
- ` Probably electoral democracy`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'electoral democracy (maybe electoral autocracy)'
- `Electoral democracies`: table `vdem_num_countries`, column `num_countries_regime`, rows where category = 'electoral democracy'
- `Probably electoral democracy`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'electoral democracy (maybe liberal democracy)'
- `Probably liberal democracy`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'liberal democracy (maybe electoral democracy)'
- `Liberal democracies`: table `vdem_num_countries`, column `num_countries_regime_amb`, rows where category = 'liberal democracy'
- The chart stacks the columns in relative mode: each value is shown as a percentage of the row total.

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
