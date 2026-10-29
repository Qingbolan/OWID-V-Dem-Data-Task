# Golden processing program: 01 Key features of democracy

View: https://ourworldindata.org/grapher/key-features-of-democracy

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Electoral political institutions`: table `vdem_multi_with_regions`, column `electdem_vdem`, rows where estimate = 'best'
- `Liberal political institutions`: table `vdem_multi_with_regions`, column `lib_vdem`, rows where estimate = 'best'
- `Participatory political institutions`: table `vdem_multi_with_regions`, column `particip_vdem`, rows where estimate = 'best'
- `Egalitarian political institutions`: table `vdem_multi_with_regions`, column `egal_vdem`, rows where estimate = 'best'
- `Deliberative political institutions`: table `vdem_multi_with_regions`, column `delib_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
