# Golden processing program: 01 Key features of electoral democracy

View: https://ourworldindata.org/grapher/key-features-of-electoral-democracy

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Electoral democracy overall`: table `vdem_multi_with_regions`, column `electdem_vdem`, rows where estimate = 'best'
- `Elected officials`: table `vdem_uni_with_regions`, column `electoff_vdem`
- `Share of adult citizens who have the right to vote`: table `vdem_uni_with_regions`, column `suffr_vdem`, multiplied by 0.01 (display conversion)
- `Free and fair elections`: table `vdem_multi_with_regions`, column `electfreefair_vdem`, rows where estimate = 'best'
- `Freedom of association`: table `vdem_multi_with_regions`, column `freeassoc_vdem`, rows where estimate = 'best'
- `Freedom of expression`: table `vdem_multi_with_regions`, column `freeexpr_vdem`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
