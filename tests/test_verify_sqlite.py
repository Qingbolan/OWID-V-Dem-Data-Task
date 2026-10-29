import json
import sqlite3

from pipeline.verify_sqlite import fingerprints


def make_db(path, value):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE t (a TEXT, b REAL)")
        db.executemany("INSERT INTO t VALUES (?, ?)", [("x", 1.0), ("y", value)])


def test_fingerprint_detects_single_cell_change(tmp_path):
    make_db(tmp_path / "a.db", 2.0)
    make_db(tmp_path / "b.db", 2.0)
    make_db(tmp_path / "c.db", 2.5)
    recorded = json.loads(json.dumps(fingerprints(tmp_path / "a.db")))  # as stored in BUILD.json
    assert json.loads(json.dumps(fingerprints(tmp_path / "b.db"))) == recorded
    assert json.loads(json.dumps(fingerprints(tmp_path / "c.db"))) != recorded
