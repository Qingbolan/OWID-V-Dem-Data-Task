# Data pipeline

Turns OWID's snapshot of the V-Dem Country-Year dataset (v16), plus OWID's population and region tables, into one
verified SQLite database. Every step is idempotent and can be run on its own; `make data` runs all three.

| Step | Module | Input | Output |
|---|---|---|---|
| 1. Download | `pipeline.download_snapshots`, `pipeline.download_catalog` | OWID ETL `.dvc` file; catalog table paths | `data/raw/owid-snapshots/democracy/2026-03-17/`, `data/raw/owid-catalog/`, manifests |
| 2. Build | `pipeline.build_sqlite` | snapshot and catalog directories | `data/sqlite/vdem2026.db`, `data/manifests/database.json` |
| 3. Verify | `pipeline.verify_sqlite` | database, `data/manifests/BUILD.json` | `OK` or the list of differing tables |

```bash
uv run python -m pipeline.download_snapshots /path/to/owid/etl data/raw/owid-snapshots democracy/2026-03-17
uv run python -m pipeline.download_catalog data/raw/owid-catalog \
    garden/demography/2024-07-15/population/population garden/regions/2023-01-01/regions/regions
uv run python -m pipeline.build_sqlite data/raw/owid-snapshots/democracy/2026-03-17 data/raw/owid-catalog data/sqlite/vdem2026.db
uv run python -m pipeline.verify_sqlite data/sqlite/vdem2026.db data/manifests/BUILD.json
```

Run times on a laptop: download 27 MB, build about 40 seconds, verify about 1 minute.

## Guarantees

- **Exact inputs.** The snapshot comes from `https://snapshots.owid.io/<md5[:2]>/<md5[2:]>`, the store OWID's ETL
  reads, and must match the MD5 in the ETL `.dvc` file. Catalog tables come from `https://catalog.ourworldindata.org`;
  a re-published table with a different MD5 aborts the download.
- **Format conversion only.** V-Dem's 4,618 columns are split by column into one table per codebook section (SQLite
  allows 2,000 columns per table); rows and values are unchanged. See
  [`docs/decisions/0001-format-conversion-only.md`](../docs/decisions/0001-format-conversion-only.md) and the module
  docstring of `build_sqlite.py` for the exact rules.
- **Content verification.** `BUILD.json` holds, per table, the row count, column names with declared types and a
  SHA-256 over all rows in rowid order. `--record` rewrites the fingerprints after an intentional rebuild.

## Changing the conversion

1. Change `build_sqlite.py` and document why in a new decision record.
2. Rebuild, then `verify_sqlite --record`, and commit the updated `BUILD.json` and `database.json`.
3. Run `make golden`; every golden program must still match.
