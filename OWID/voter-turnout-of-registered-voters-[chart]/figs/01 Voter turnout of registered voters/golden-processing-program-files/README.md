# Golden processing program: 01 Voter turnout of registered voters

View: https://ourworldindata.org/grapher/voter-turnout-of-registered-voters

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Voter turnout of registered voters`: table `vdem_uni_with_regions`, column `turnout_vdem`
- `Voter turnout of registered voters (Original Year)`: the year the value of `Voter turnout of registered voters` comes from (map tolerance)
- `World region according to OWID`: not compared (OWID's world region (map and scatter colour), not a V-Dem indicator)
- The map shows, per entity, the value of the closest year within 4 years.

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
