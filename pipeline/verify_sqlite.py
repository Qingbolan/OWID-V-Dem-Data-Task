"""Record or verify content fingerprints of every table in the SQLite database.

    python -m pipeline.verify_sqlite <db> <BUILD.json> [--record]

Per table: row count, column names with declared types, and SHA-256 over all rows in rowid order (each value encoded
with its SQLite storage class). SQLite file bytes may differ between identical rebuilds, so verification is by
content; the file hash in BUILD.json is informational only.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


def fingerprint(db: sqlite3.Connection, table: str) -> dict:
    columns = [[r[1], r[2]] for r in db.execute(f'PRAGMA table_info("{table}")')]
    h, rows = hashlib.sha256(), 0
    for row in db.execute(f'SELECT * FROM "{table}" ORDER BY rowid'):
        h.update(repr(tuple((type(v).__name__, v) for v in row)).encode())
        h.update(b"\n")
        rows += 1
    return {"rows": rows, "columns": columns, "content_sha256": h.hexdigest()}


def fingerprints(path: Path) -> dict:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        names = sorted(r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        result = {}
        for name in names:
            result[name] = fingerprint(db, name)
            print(f"{name}: {result[name]['rows']:,} rows", flush=True)
        return result
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("db", type=Path)
    parser.add_argument("build", type=Path, help="BUILD.json holding the recorded fingerprints")
    parser.add_argument("--record", action="store_true", help="write fingerprints instead of checking them")
    args = parser.parse_args()
    current = fingerprints(args.db)
    if args.record:
        build = json.loads(args.build.read_text()) if args.build.exists() else {}
        build["tables"] = current
        args.build.write_text(json.dumps(build, ensure_ascii=False, indent=1))
        print(f"recorded {len(current)} tables")
        return
    expected = json.loads(args.build.read_text())["tables"]
    problems = sorted(t for t in set(expected) | set(current) if expected.get(t) != current.get(t))
    for table in problems:
        print("MISMATCH", table)
    print("OK" if not problems else f"FAILED: {len(problems)} tables differ")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
