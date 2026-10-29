# Golden processing program: 01 Varieties of democracy

View: https://ourworldindata.org/grapher/varieties-democracy-vdem

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Electoral democracy index`: table `vdem_multi_with_regions`, column `electdem_vdem`, rows where estimate = 'best'
- `Liberal democracy`: table `vdem_multi_with_regions`, column `libdem_vdem`, rows where estimate = 'best'
- `Participatory democracy index`: table `vdem_multi_with_regions`, column `participdem_vdem`, rows where estimate = 'best'
- `Deliberative democracy`: table `vdem_multi_with_regions`, column `delibdem_vdem`, rows where estimate = 'best'
- `Egalitarian democracy`: table `vdem_multi_with_regions`, column `egaldem_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
