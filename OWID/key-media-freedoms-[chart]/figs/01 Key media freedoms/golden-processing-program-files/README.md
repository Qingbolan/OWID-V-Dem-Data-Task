# Golden processing program: 01 Key media freedoms

View: https://ourworldindata.org/grapher/key-media-freedoms

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `No government censorship of the media`: table `vdem_multi_with_regions`, column `v2mecenefm`, rows where estimate = 'best'
- `No journalist harassment`: table `vdem_multi_with_regions`, column `v2meharjrn`, rows where estimate = 'best'
- `No self-censorship by the media`: table `vdem_multi_with_regions`, column `v2meslfcen`, rows where estimate = 'best'
- `No media bias`: table `vdem_multi_with_regions`, column `v2mebias`, rows where estimate = 'best'

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
