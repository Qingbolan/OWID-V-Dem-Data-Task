# Scripts

| Module | Purpose |
|---|---|
| `scripts.select_charts` | The OWID charts that plot only V-Dem v16 indicators, and the excluded ones (`data/reference/charts.json`) |
| `scripts.owid_pages` | Helpers for reading ourworldindata.org; writes the figure lists of the pages that show V-Dem charts (`make figure-lists`) |
| `scripts.list_page_figures` | The figure list of one page (`scripts/articles/<slug>.json`), as `build_owid_article` reads it |
| `scripts/articles/*.json` | Figure lists: 14 pages (generated) and 7 data insights (the chart and view identified by hand) |
| `scripts.build_pages` | Materialise every page with a figure list into `OWID/<slug>-[<date>]/` with `build_owid_article` (`make tasks`) |
| `scripts.build_owid_article` | One page into a folder: source page, offline snapshot, prose, figures; from the WPP benchmark |
| `scripts.snapshot_page` | Offline, styled copy of a saved page; imported by `build_owid_article` and `build_chart_pages` |
| `scripts.build_chart_pages` | `OWID/<slug>-[chart]/` for each V-Dem chart no page shows: its chart page and default view (`make tasks`) |
| `scripts.add_figure_sources` | Each figure's chart config, indicator metadata and column short names (`make tasks`) |
| `scripts.write_golden_specs` | Each figure's golden spec: source columns in OWID's V-Dem output tables, view settings, output precision (`make golden-specs`) |
| `scripts.run_golden` | Check every figure's golden program against the published figure data (`make golden`) |
| `scripts.analyze_runs`, `categorise_failures`, `aggregate_attribution`, `export_run_records`, `export_sql_calls` | Run analysis, from the WPP benchmark |
| `scripts.owid_mapping.*` | The OWID site crawl and per-snapshot chart counts behind `docs/owid-mapping/` (built in the WPP benchmark) |

Rebuild the tasks and their golden checks:

```bash
make figure-lists   # select charts; figure lists of the pages that show them (data-insight lists are kept)
make tasks          # pages, chart pages, figure sources (network: one request per second; folders already built are kept)
make golden-specs   # needs data/golden/vdem from `make golden-pipeline`
make golden
```

Rebuild the mapping in `docs/owid-mapping/` (writes a WPP-style overview to the path given last):

```bash
uv run python -m scripts.owid_mapping.index_snapshots /path/to/owid/etl docs/owid-mapping/snapshot_index.json
uv run python -m scripts.owid_mapping.crawl_site data/cache/owid-site docs/owid-mapping/crawl.json
uv run python -m scripts.owid_mapping.merge_counts docs/owid-mapping/snapshot_index.json docs/owid-mapping/crawl.json docs/owid-mapping/mapping.json
uv run python -m scripts.owid_mapping.render_mapping docs/owid-mapping/mapping.json docs/owid-mapping/overview.md --focus democracy/2026-03-17
```

The crawl issues about 15,500 requests on a cold cache (four workers, paced); later runs read the cache.
