# 0005. Chart selection and host pages

- Status: accepted
- Date: 2026-10-29

## Context

The WPP benchmark takes figures from OWID articles published in 2026. Most V-Dem charts are not in a dated article:
OWID's crawl (`docs/owid-mapping/`) lists 109 direct charts of the V-Dem snapshot, linked mostly from topic pages
("Democracy", "Human Rights", "Corruption").

## Decision

- **Charts.** A chart is a task when every indicator it plots comes from OWID's V-Dem dataset
  (`grapher/democracy/2026-03-17/vdem`; OWID's region table, which only colours maps, is allowed): 100 charts.
  The 9 charts that also plot other data (GDP, child mortality, World Bank, UN SDG, other democracy indices) are
  listed under "excluded" in `data/reference/charts.json`.
- **Host page.** Of the pages the crawl lists for a chart, only those that show it as a figure in their prose count;
  a topic page's "all charts" grid and related-chart thumbnails only link to it. Among those, the page with the fewest
  figures, then the most recent. The host page gives the view (its embed's query) and the article-level input.
- A chart that no page shows as a figure (81 of 100) is taken in its default view and has title and subtitle levels
  only; the harness skips its article level (`Task.supports`).

## Consequences

- 19 charts have an article level; their host pages are 12 pages (topic pages and articles; e.g. "Women have made major advances in politics" and "Democracies age" host 4 charts each).
- The benchmark's unit is the chart, so a topic page that shows several charts contributes several tasks with the same
  article text and a different "[Figure n: the requested chart]" marker.
