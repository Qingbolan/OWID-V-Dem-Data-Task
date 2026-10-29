# OWID-V-Dem-Data-Task

Natural-language chart-data tasks built from [Our World in Data](https://ourworldindata.org) (OWID) charts on the
V-Dem democracy data (Country-Year v16), together with the raw data as a SQLite database, golden processing programs
that reproduce every published chart, and a benchmark harness for data-analysis agents. It follows the layout of
`OWID-WPP-Data-Task`.

## Why

> Given a chart's title (and, where a page shows it, the page's text) and read-only SQL access to the **raw upstream
> data**, can a general-purpose agent produce the data behind the chart?

V-Dem is a hard case for this question. OWID does not chart V-Dem's columns as they are: it rebuilds the regime
classification from its components, imputes today's countries from historical predecessors, carries election status
between elections, and builds regional averages and counts of countries and people with coverage thresholds. Most of
this is not stated on the chart. Correctness is judged on executed results against OWID's published chart data, never
on SQL text ([`docs/task-definition.md`](docs/task-definition.md)).

## Repository layout

```
.
├── pipeline/        Raw OWID snapshot + catalog tables -> one SQLite database (download, conversion, verification)
├── data/            Snapshot, database, golden output (not in git); manifests and reference files (in git)
├── OWID/            One folder per chart: view data, image, text, host-page prose, golden program spec
├── golden/          OWID's V-Dem code run on the database (shared part of every golden program)
├── Benchmark/       Benchmark harness (as in the WPP benchmark)
├── scripts/         Chart selection, task capture, golden specs and checks
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
make golden                              # run OWID's V-Dem code on the database, check all 100 charts
make test
```

The task folders in `OWID/` are in git; `make tasks` re-captures them from OWID (network).

## Data

| Item | Value |
|---|---|
| Source | V-Dem v16 via OWID's snapshot store (`democracy/2026-03-17`), plus OWID's population and region tables |
| Database | `data/sqlite/vdem2026.db`: 27 tables, 0.74 GB; V-Dem's 4,618 columns split by codebook section, codebook as text |
| Integrity | snapshot MD5 from OWID's `.dvc`; per-table content fingerprints in `data/manifests/BUILD.json` |

Details: [`docs/data-card.md`](docs/data-card.md).

## Charts

100 OWID charts that plot only V-Dem indicators ([decision 0005](docs/decisions/0005-chart-selection-and-host-pages.md));
9 further charts of the snapshot plot other data too and are excluded (`data/reference/charts.json`).

| View | Charts | Article level |
|---|---:|---:|
| Map (latest year) | 75 | |
| Stacked area (countries or people by regime, women in parliament, age of democracy) | 10 | |
| Line, scatter, bar | 15 | |
| All | 100 | 19 (12 host pages) |

**Golden programs: 100 of 100 charts reproduce OWID's published data exactly** (`make golden`). The programs run OWID's
own V-Dem code, pinned to owid/etl `bac9e16`, on this database, then select each chart's columns and apply its view
(relative stacking, a map's time tolerance, display conversion)
([decision 0004](docs/decisions/0004-golden-programs-run-owid-code.md)).

A caveat for reading results: many of the 75 maps plot a V-Dem index almost directly for the latest year (a smoke run
of the Codex SQL agent on the electoral democracy index map was correct, 174/174 cells, from `v2x_polyarchy`). OWID's
conventions matter most in the regime maps and the 25 other views (counts and populations by regime, regional averages).

## Status

| Component | State |
|---|---|
| Data pipeline | complete and verified |
| Chart tasks | 100 charts captured (view CSV, PNG, text, config, metadata; host-page prose for 19) |
| Golden programs | 100 match |
| Benchmark harness | adapted from the WPP benchmark; one smoke case run; no baseline study yet |

## Licence

Code: MIT. Data: see [`DATA_LICENSE.md`](DATA_LICENSE.md).
