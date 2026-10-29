# OWID mapping

`owid-mapping/crawl.json` and `owid-mapping/mapping.json` are copied from the WPP benchmark
(`OWID-WPP-Data-Task/docs/owid-mapping/`, built by its `scripts/owid_mapping/` from OWID ETL `f1ffd5e` and a crawl of
ourworldindata.org on 2026-10-17: 5,425 charts, 8,059 indicators, 2,046 pages).

- `mapping.json` lists, per snapshot group, the charts that use it directly. The group `democracy/2026-03-17` (V-Dem
  v16) has 109 direct charts.
- `crawl.json` gives each chart's indicators (with the dataset each comes from) and each page's embedded and linked
  charts.

`scripts/select_charts.py` reads both and writes `data/reference/charts.json`: the 100 charts that plot only V-Dem
indicators, and the 9 excluded with the other datasets they need. `scripts/owid_pages.py` then fetches the pages the
crawl lists for them and writes the figure lists (`scripts/articles/`) of the 14 pages that show a V-Dem chart as a
figure in their prose; the 7 data insights' lists are written by hand
([decision 0005](decisions/0005-chart-selection-and-host-pages.md)).
