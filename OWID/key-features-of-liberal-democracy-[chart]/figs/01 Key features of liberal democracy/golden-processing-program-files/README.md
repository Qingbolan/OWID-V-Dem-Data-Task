# Golden processing program: 01 Key features of liberal democracy

View: https://ourworldindata.org/grapher/key-features-of-liberal-democracy

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Liberal democracy overall`: table `vdem_multi_with_regions`, column `libdem_vdem`, rows where estimate = 'best'
- `Democratic elections`: table `vdem_multi_with_regions`, column `electdem_vdem`, rows where estimate = 'best'
- `Legislative checks on government`: table `vdem_multi_with_regions`, column `legis_constr_vdem`, rows where estimate = 'best'
- `Judicial checks on government`: table `vdem_multi_with_regions`, column `judicial_constr_vdem`, rows where estimate = 'best'
- `Rule of Law`: table `vdem_multi_with_regions`, column `rule_of_law_vdem`, rows where estimate = 'best'
- `Private civil liberties`: table `vdem_multi_with_regions`, column `priv_libs_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
