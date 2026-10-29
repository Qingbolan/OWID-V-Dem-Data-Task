# Scripts

| Module | Purpose |
|---|---|
| `scripts.select_charts` | The OWID charts that plot only V-Dem v16 indicators, and the excluded ones (`data/reference/charts.json`) |
| `scripts.build_chart_tasks` | One task folder per chart in `OWID/<slug>/`: host page, view CSV and PNG, chart text, config, metadata, column short names (`make tasks`) |
| `scripts.build_owid_article` | Page parsing used by `build_chart_tasks` (figures, embeds, prose); from the WPP benchmark |
| `scripts.snapshot_page` | Offline, styled copy of a saved page; imported by `build_owid_article` |
| `scripts.write_golden_specs` | Each chart's golden spec: source columns in OWID's V-Dem output tables and view settings (`make golden-specs`) |
| `scripts.run_golden` | Check every chart's golden program against the published figure data (`make golden`) |
| `scripts.analyze_runs`, `categorise_failures`, `aggregate_attribution`, `export_run_records`, `export_sql_calls` | Run analysis, from the WPP benchmark |
| `scripts.owid_mapping.*` | The OWID site crawl and per-snapshot chart counts behind `docs/owid-mapping/` (built in the WPP benchmark) |

Rebuild the tasks and their golden checks:

```bash
make tasks          # select charts, capture OWID/ (about 25 minutes: one request per second)
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
