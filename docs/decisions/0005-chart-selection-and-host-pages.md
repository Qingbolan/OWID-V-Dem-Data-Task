# 0005. Charts, pages and figures

- Status: accepted
- Date: 2026-10-29 (revised 2026-10-30: one folder per page, as in the WPP benchmark)

## Context

The WPP benchmark takes figures from OWID articles: one folder per article, with the page as retrieved, its offline
snapshot, its prose and its figures, and one task per figure. Most V-Dem charts are not in a dated article. OWID's
crawl (`docs/owid-mapping/`) lists 109 direct charts of the V-Dem snapshot, linked mostly from topic pages
("Democracy", "Human Rights", "Corruption"), and many of those links are only thumbnails in a page's "all charts" grid.

## Decision

- **Charts.** The tasks cover the charts whose every indicator comes from OWID's V-Dem dataset
  (`grapher/democracy/2026-03-17/vdem`; OWID's region table, which only colours maps, is allowed): 100 charts. The 9
  charts that also plot other data (GDP, child mortality, World Bank, UN SDG, other democracy indices) are listed under
  "excluded" in `data/reference/charts.json`.
- **Pages.** Every OWID page that shows at least one of the 100 charts as a figure in its prose is materialised as in
  the WPP benchmark, with WPP's `scripts/build_owid_article.py`: `OWID/<page slug>-[<date published>]/`. A topic page's
  "all charts" grid and related-chart thumbnails only link to a chart and do not count. 14 pages qualify; their figure
  lists (`scripts/articles/<slug>.json`) are written by `scripts.owid_pages`.
- **Data insights.** The 7 data insights the crawl links to V-Dem charts show a static image. As in the WPP benchmark,
  each image was compared with the linked chart by hand and the view it shows written into the figure list with the
  identification; 5 show V-Dem data, 2 show other data (Integrated Values Surveys; national turnout statistics) and are
  static images without a data series.
- **Chart pages.** A V-Dem chart that no page or data insight shows (81 of 100) gets a folder of the same layout,
  `OWID/<chart slug>-[chart]/`, whose source page is the chart's own page on ourworldindata.org and whose figure is the
  chart's default view. It has no article.md, so its task has title and subtitle levels only.
- **Tasks.** Every figure of every folder is a task, as in the WPP benchmark. A figure whose chart is not one of the
  100 (other data) or that has no data series is kept, with a spec saying why it is not reproducible.

## Consequences

- 102 folders, 181 figures; 124 V-Dem figures are tasks, 43 of them (on the 14 pages and 5 data insights) with an
  article level. 57 figures are not reproducible: 54 plot other data, 3 have no data series.
- A chart shown on several pages, or several times on one page in different views, gives several tasks (e.g. the
  electoral democracy index appears in five views on "People around the world have gained democratic rights, but some
  have many more rights than others"); the 124 tasks cover the 100 charts.
- A page that shows several V-Dem charts contributes several tasks with the same article text and a different
  "[Figure n: the requested chart]" marker.
