# 0002. Large data files are not committed

- Status: accepted
- Date: 2026-10-29

## Context

The database is 0.74 GB and the snapshot 27 MB (406 MB unpacked). GitHub rejects files above 100 MB.

## Decision

The snapshot, catalog tables and the database live under `data/raw/` and `data/sqlite/`, and the golden pipeline's
output under `data/golden/`; git ignores all three. Git tracks the code that rebuilds them, the manifests with MD5
and SHA-256, and per-table content fingerprints (`data/manifests/BUILD.json`). `make data` rebuilds and verifies the
database from OWID's public snapshot store and catalog.

## Consequences

- Clones are small; anyone with an owid/etl clone can rebuild the exact data.
- Verification is by content rather than file bytes, because SQLite file layout can differ between identical builds.
