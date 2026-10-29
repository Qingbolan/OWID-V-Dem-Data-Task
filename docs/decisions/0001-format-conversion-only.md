# 0001. Format conversion only when building the database

- Status: accepted
- Date: 2026-10-29

## Context

The benchmark measures whether an agent can perform the analysis behind a published chart. Any processing done while
building the database (recoding regimes, imputing historical countries, mapping names, aggregating regions) would
perform part of that analysis for the agent.

The V-Dem Country-Year CSV has 4,618 columns; SQLite tables hold at most 2,000.

## Decision

`pipeline/build_sqlite.py` performs format conversion only:

- V-Dem's CSV is split **by column only**: the 22 identifier columns go to `vdem__identifiers`, and each codebook
  section (the column-name prefix: `v2x` indices, `v2el` elections, `v2ex` executive, `e_` other sources, ...) gets
  one table repeating the key columns (`country_name`, `country_text_id`, `country_id`, `year`). Sections with
  fewer than 20 columns share `vdem__misc`. Rows, column names and values are unchanged.
- The PDFs in the snapshot (codebook, cautionary notes, what's new, citation) are stored as text, one row per page,
  in `vdem_documents`. Without the codebook an agent cannot know that "electoral democracy index" is `v2x_polyarchy`.
- OWID's population and region tables, which OWID's V-Dem processing reads, are stored unchanged as `owid_population`
  and `owid_regions` (as the Global Carbon Budget benchmark stores OWID's population, region and income tables).

## Consequences

- The database keeps the source's difficulties: historical entities (Baden, Piedmont-Sardinia), country-years without
  data, interval estimates (`_codelow`, `_codehigh`), and V-Dem's own regime classification next to the components
  OWID rebuilds it from.
- An agent must join section tables on (`country_id`, `year`) when a chart needs columns from several sections.
- Golden programs must implement OWID's processing explicitly ([0004](0004-golden-programs-run-owid-code.md)).
