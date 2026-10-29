# Golden processing program: 02 People living in democracies and autocracies

View: https://ourworldindata.org/grapher/people-living-in-democracies-autocracies

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `No regime data`: table `vdem_population`, column `population_regime`, rows where category = '-1'
- `People living in closed autocracies`: table `vdem_population`, column `population_regime`, rows where category = 'closed autocracy'
- `in electoral autocracies`: table `vdem_population`, column `population_regime`, rows where category = 'electoral autocracy'
- `in electoral democracies`: table `vdem_population`, column `population_regime`, rows where category = 'electoral democracy'
- `in liberal democracies`: table `vdem_population`, column `population_regime`, rows where category = 'liberal democracy'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
