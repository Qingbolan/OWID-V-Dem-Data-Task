# Golden processing program: 01 Share of countries that have had a woman as chief executive

View: https://ourworldindata.org/grapher/share-of-countries-that-have-had-a-woman-as-chief-executive

## How OWID computes it
OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:

- `Any woman chief executive`: table `vdem_share_countries`, column `share_countries_wom_hoe_ever`
- `Democratically-elected woman chief executive`: table `vdem_share_countries`, column `share_countries_wom_hoe_ever_demelect`

## Files
- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`.
