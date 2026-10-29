# Golden processing program: 01 Key features of women's political empowerment

View: https://ourworldindata.org/grapher/key-features-of-womens-political-empowerment

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Women's political empowerment overall`: table `vdem_multi_with_regions`, column `wom_emp_vdem`, rows where estimate = 'best'
- `Women's civil liberties`: table `vdem_multi_with_regions`, column `wom_civ_libs_vdem`, rows where estimate = 'best'
- `Women's civil society participation`: table `vdem_multi_with_regions`, column `wom_civ_soc_vdem`, rows where estimate = 'best'
- `Women's political participation`: table `vdem_multi_with_regions`, column `wom_pol_par_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
