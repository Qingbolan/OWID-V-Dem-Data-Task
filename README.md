# OWID-V-Dem-Data-Task

Natural-language chart-data tasks built from [Our World in Data](https://ourworldindata.org) (OWID) pages and charts
on the V-Dem democracy data (Country-Year v16), together with the raw data as a SQLite database, golden processing
programs that reproduce every published figure, and a benchmark harness for data-analysis agents. It has the layout of
`OWID-WPP-Data-Task`: one folder per page, with the page as retrieved, its offline snapshot, its prose and its figures.

## Why

> Given an OWID page (or a chart's title and subtitle) and read-only SQL access to the **raw upstream data**, can a
> general-purpose agent produce the data behind a published figure?

V-Dem is a hard case for this question. OWID does not chart V-Dem's columns as they are: it rebuilds the regime
classification from its components, imputes today's countries from historical predecessors, carries election status
between elections, and builds regional averages and counts of countries and people with coverage thresholds. Most of
this is not stated on the chart. Correctness is judged on executed results against OWID's published figure data, never
on SQL text ([`docs/task-definition.md`](docs/task-definition.md)).

## Repository layout

```
.
├── pipeline/        Raw OWID snapshot + catalog tables -> one SQLite database (download, conversion, verification)
├── data/            Snapshot, database, golden output (not in git); manifests and reference files (in git)
├── OWID/            One folder per page: source page, offline snapshot, prose, figures, golden program specs
├── golden/          OWID's V-Dem code run on the database (shared part of every golden program)
├── Benchmark/       Benchmark harness (as in the WPP benchmark)
├── scripts/         Chart selection, figure lists, page capture, golden specs and checks
├── docs/            Task definition, data card, OWID mapping, decision records
└── tests/
```

## Quick start

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), a local clone of [owid/etl](https://github.com/owid/etl)
containing commit `bac9e16` (for the golden programs), about 2 GB of free disk.

```bash
uv sync
make data ETL=/path/to/owid/etl          # download 27 MB, build the 0.74 GB database, verify it
make golden-env ETL=/path/to/owid/etl    # OWID's libraries at the pinned commit, in .venv-golden
make golden                              # run OWID's V-Dem code on the database, check every figure
make test
```

`OWID/` and the figure lists in `scripts/articles/` are in git; `make figure-lists` and `make tasks` rebuild them
from OWID (network).

## Data

| Item | Value |
|---|---|
| Source | V-Dem v16 via OWID's snapshot store (`democracy/2026-03-17`), plus OWID's population and region tables |
| Database | `data/sqlite/vdem2026.db`: 27 tables, 0.74 GB; V-Dem's 4,618 columns split by codebook section, codebook as text |
| Integrity | snapshot MD5 from OWID's `.dvc`; per-table content fingerprints in `data/manifests/BUILD.json` |

Details: [`docs/data-card.md`](docs/data-card.md).

## Pages and figures

The tasks cover the 100 OWID charts that plot only V-Dem indicators; 9 further charts of the snapshot plot other data
too and are excluded (`data/reference/charts.json`). They come from 102 folders
([decision 0005](docs/decisions/0005-chart-selection-and-host-pages.md)):

| Folder | Folders | Figures | V-Dem figures (tasks) | Article level |
|---|---:|---:|---:|---:|
| OWID page that shows V-Dem charts in its prose (topic pages, articles) | 14 | 93 | 38 | 38 |
| OWID data insight (static image; the chart and view identified by hand) | 7 | 7 | 5 | 5 |
| Chart page of a V-Dem chart no page shows (`<slug>-[chart]`) | 81 | 81 | 81 | – |
| All | 102 | 181 | **124** | **43** |

A figure is one task, so a chart shown on several pages (or several times on one page, in different views) gives
several tasks: the 124 tasks cover the 100 charts. The other 57 figures are not reproducible from this database
(54 plot data other than V-Dem, 3 have no data series); their specs say why, as in the WPP benchmark.

Every task's query ends with supplementary material: the output columns, in order, and the precision of each
([decision 0006](docs/decisions/0006-output-columns-as-supplementary-material.md)).

**Golden programs: 124 of 124 figures reproduce OWID's published data exactly** (`make golden`). The programs run OWID's
own V-Dem code, pinned to owid/etl `bac9e16`, on this database, then select each figure's columns and apply its view
(relative stacking, a map's time tolerance, display conversion)
([decision 0004](docs/decisions/0004-golden-programs-run-owid-code.md)).

A caveat for reading results: 83 of the 124 views are maps, and many plot a V-Dem index almost directly for the latest
year. OWID's conventions matter most in the regime maps and in the other views (counts and populations by regime,
regional averages).

## Status

| Component | State |
|---|---|
| Data pipeline | complete and verified |
| Tasks | 102 folders, 181 figures; 124 tasks, 43 with an article level |
| Golden programs | 124 match |
| Benchmark harness | adapted from the WPP benchmark; first article-level run of Codex and Claude (43 tasks, one repeat) in progress |

## Licence

Code: MIT. Data: see [`DATA_LICENSE.md`](DATA_LICENSE.md).
