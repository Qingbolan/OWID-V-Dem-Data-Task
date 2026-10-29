# Golden processing program: 01 Key features of human rights

View: https://ourworldindata.org/grapher/key-features-of-human-rights

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Human rights overall`: table `vdem_multi_with_regions`, column `civ_libs_vdem`, rows where estimate = 'best'
- `Physical integrity`: table `vdem_multi_with_regions`, column `phys_integr_libs_vdem`, rows where estimate = 'best'
- `Private civil liberties`: table `vdem_multi_with_regions`, column `priv_libs_vdem`, rows where estimate = 'best'
- `Political civil liberties`: table `vdem_multi_with_regions`, column `pol_libs_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
