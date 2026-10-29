# Data card

## Source

| Item | Value |
|---|---|
| Dataset | V-Dem Country-Year (Full + Others), version 16 (Coppedge et al. 2026, https://doi.org/10.23696/vdemds26) |
| Via | OWID's snapshot `democracy/2026-03-17/vdem.zip` (MD5 `5cc16b7636bd3bef29b39dcabf19e3d9`, 26.9 MB) from `snapshots.owid.io` |
| Also | OWID's `garden/demography/2024-07-15/population` and `garden/regions/2023-01-01/regions` tables, which OWID's V-Dem processing reads (population weights, continent membership) |
| Licence | CC BY 4.0 (V-Dem; OWID), see `DATA_LICENSE.md` |

## Database `data/sqlite/vdem2026.db`

0.74 GB, 27 tables; format conversion only ([decision 0001](decisions/0001-format-conversion-only.md)).

| Table | Rows | Columns | Content |
|---|---:|---:|---|
| `vdem__identifiers` | 28,092 | 22 | country name, ids, year, historical name, coding periods |
| `vdem__v2x` | 28,092 | 345 | V-Dem's indices (`v2x_polyarchy` electoral democracy, `v2x_libdem`, `v2x_regime`, ...) |
| `vdem__v2el`, `__v2ex`, `__v2lg`, `__v2ju`, `__v2cl`, `__v2cs`, `__v2me`, `__v2pe`, `__v2ca`, `__v2sm`, `__v2ed`, `__v2ps`, `__v2dl`, `__v2re`, `__v2st`, `__v2sv`, `__v2dd`, `__v3el`, `__v3lg`, `__v3st`, `__e`, `__misc` | 28,092 each | 37-456 | one table per codebook section (elections, executive, legislature, judiciary, civil liberties, ...; `e_` other sources); sections under 20 columns in `__misc` |
| `vdem_documents` | 513 | 3 | the snapshot's PDFs as text, one row per page (codebook, cautionary notes, what's new, citation) |
| `owid_population` | 78,536 | 5 | OWID population by country and region |
| `owid_regions` | 481 | 24 | OWID's regions; `members` is a JSON list of member codes |

Every V-Dem table repeats `country_name`, `country_text_id`, `country_id`, `year` and joins on (`country_id`, `year`).
One row per country-year, 1789-2025, including historical entities (e.g. Baden, Piedmont-Sardinia, Two Sicilies).

## Known properties

- V-Dem's estimates have interval bounds (`_codelow`, `_codehigh`) and, for many indicators, ordinal versions
  (`_ord`) and "original scale" versions (`_osp`); OWID's charts use specific ones.
- `v2x_regime` (V-Dem's Regimes of the World) is present, but OWID publishes its own classification rebuilt from the
  components, with different coverage and hand-reconciled cases (see `data/reference/owid_etl/vdem/vdem_clean.py`).
- Many country-years have no data; OWID imputes some of today's countries from historical predecessors
  (`vdem.countries_impute.yml`, 57 rules) for regime counts.

## Tasks

124 tasks (figures) covering the 100 V-Dem-only charts, in 102 folders of `OWID/`: 14 OWID pages, 7 data insights and
81 chart pages ([decision 0005](decisions/0005-chart-selection-and-host-pages.md)). Their views:

| View | Tasks |
|---|---:|
| Map | 83 |
| Line chart | 18 |
| Stacked area (counts of countries or people by category; 9 views in relative mode) | 12 |
| Discrete bar | 4 |
| Scatter plot | 4 |
| Marimekko | 3 |

Figure data: 1 to 606 rows per task (median 174), 20,537 rows in all. Two map views use a time tolerance (the closest
year within 4 years, with an "(Original Year)" column).
