"""Format-convert OWID's snapshot of the V-Dem Country-Year dataset (v16), plus OWID's population and region tables,
into one SQLite file.

    python -m pipeline.build_sqlite <snapshot_dir> <catalog_dir> <out_db>

Rules (format conversion only, see docs/decisions/0001-format-conversion-only.md):
- The CSV `V-Dem-CY-Full+Others-v16.csv` (one row per country-year, 4,618 columns) does not fit one SQLite table
  (at most 2,000 columns). It is split by column only, never by row: the 22 identifier columns go to `vdem__identifiers`,
  and the indicator columns go to one table per codebook section, named by the section prefix of the column
  (`v2x` indices, `v2el` elections, `v2ex` executive, `e_` other sources, ...). Sections with fewer than
  MIN_SECTION columns share `vdem__misc`. Every table repeats the key columns KEYS, so tables join on
  (country_id, year). Original column names and values; no filtering, recoding, imputation or entity processing.
- The codebook and the other PDFs in the snapshot are stored as text, one row per page, in `vdem_documents`.
- OWID's population and region tables (catalog feather files) are stored as one table each, unchanged.
- Indexes on (country_id, year), (country_name, year) and the catalog keys only speed up queries.
A per-table summary (rows, columns, source file, MD5/SHA-256) is written next to the database.
"""
import argparse
import hashlib
import io
import json
import re
import sqlite3
import time
import zipfile
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

CSV_NAME = "V-Dem-CY-Full+Others-v16.csv"
KEYS = ["country_name", "country_text_id", "country_id", "year"]
FIRST_INDICATOR = "v2x_polyarchy"  # columns before it are identifiers
MIN_SECTION = 20
SECTION = re.compile(r"^(v2x|v3x|v2[a-z]{2}|v3[a-z]{2}|e_)")
INDEX_KEYS = [("country_id", "year"), ("country_name", "year"), ("country", "year"), ("code",)]


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def section_of(column: str) -> str:
    match = SECTION.match(column)
    return match.group(1).rstrip("_") if match else "misc"


def split_columns(columns: list[str]) -> dict[str, list[str]]:
    """Table name -> its columns (keys first); the identifier table holds every column before the first indicator."""
    first = columns.index(FIRST_INDICATOR)
    sections: dict[str, list[str]] = {}
    for column in columns[first:]:
        sections.setdefault(section_of(column), []).append(column)
    tables = {"vdem__identifiers": columns[:first]}
    misc = []
    for name, members in sections.items():
        if len(members) < MIN_SECTION:
            misc += members
        else:
            tables[f"vdem__{name}"] = KEYS + members
    if misc:
        tables["vdem__misc"] = KEYS + misc
    return tables


def finish(db: sqlite3.Connection, name: str, source: dict, tables: dict) -> None:
    columns = [r[1] for r in db.execute(f'PRAGMA table_info("{name}")')]
    for i, keys in enumerate(INDEX_KEYS):
        if set(keys) <= set(columns):
            quoted = ", ".join('"' + k + '"' for k in keys)
            db.execute(f'CREATE INDEX "{name}_idx{i}" ON "{name}"({quoted})')
    rows = db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
    tables[name] = {"rows": rows, "columns": len(columns), **source}
    db.commit()
    print(f"{name}: {rows:,} rows, {len(columns)} cols", flush=True)


def load_vdem(db: sqlite3.Connection, archive: zipfile.ZipFile, source: dict, tables: dict) -> None:
    frame = pd.read_csv(io.BytesIO(archive.read(CSV_NAME)), low_memory=False)
    if frame.duplicated(["country_id", "year"]).any():
        raise ValueError("V-Dem rows are not unique on (country_id, year)")
    for name, columns in split_columns(list(frame.columns)).items():
        part = frame[columns]
        text = {c: "TEXT" for c in columns if part[c].dtype == object}
        part.to_sql(name, db, index=False, if_exists="replace", dtype=text, chunksize=2000)
        finish(db, name, dict(source, source=f"{source['archive']}:{CSV_NAME}"), tables)


def load_documents(db: sqlite3.Connection, archive: zipfile.ZipFile, source: dict, tables: dict) -> None:
    rows = []
    for member in sorted(m for m in archive.namelist() if m.lower().endswith(".pdf")):
        reader = PdfReader(io.BytesIO(archive.read(member)))
        rows += [{"document": member, "page": i + 1, "text": page.extract_text() or ""}
                 for i, page in enumerate(reader.pages)]
    if not rows:
        return
    pd.DataFrame(rows).to_sql("vdem_documents", db, index=False, if_exists="replace")
    finish(db, "vdem_documents", dict(source, source=f"{source['archive']}:*.pdf"), tables)


def build(src: Path, catalog: Path, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    tables, started = {}, time.time()
    archive_path = src / "vdem.zip"
    source = {"archive": archive_path.name, "md5": digest(archive_path, "md5"), "sha256": digest(archive_path, "sha256")}
    with sqlite3.connect(out) as db:
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        with zipfile.ZipFile(archive_path) as archive:
            load_vdem(db, archive, source, tables)
            load_documents(db, archive, source, tables)
        for path in sorted(catalog.rglob("*.feather")):
            relative = path.relative_to(catalog).with_suffix("")
            name = f"owid_{relative.name}"
            frame = pd.read_feather(path)
            for column in frame.columns:  # categoricals and pandas extension types are stored by value
                if not pd.api.types.is_numeric_dtype(frame[column]):
                    frame[column] = frame[column].astype(object)
            frame.to_sql(name, db, index=False, if_exists="replace")
            finish(db, name, {"source": f"https://catalog.ourworldindata.org/{relative}.feather",
                              "md5": digest(path, "md5"), "sha256": digest(path, "sha256")}, tables)
    return {"database": out.name, "database_bytes": out.stat().st_size, "source_dir": str(src),
            "catalog_dir": str(catalog), "elapsed_seconds": round(time.time() - started), "tables": tables}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("src", type=Path, help="snapshot directory, e.g. data/raw/owid-snapshots/democracy/2026-03-17")
    parser.add_argument("catalog", type=Path, help="OWID catalog tables, e.g. data/raw/owid-catalog")
    parser.add_argument("out", type=Path, help="output SQLite file, e.g. data/sqlite/vdem2026.db")
    parser.add_argument("--summary", type=Path, default=Path("data/manifests/database.json"))
    args = parser.parse_args()
    summary = build(args.src, args.catalog, args.out)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"done: {len(summary['tables'])} tables, {summary['database_bytes'] / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
