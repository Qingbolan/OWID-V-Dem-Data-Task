import json
import sqlite3

from Benchmark.benchmarking.processor import write_sql_calls


def make_case(tmp_path, calls, final=None, lenient=None):
    case = tmp_path / "task__01" / "title" / "repeat-1"
    case.mkdir(parents=True)
    (case / "meta.json").write_text(json.dumps({"level": "title", "repeat": 1, "solution": "S", "model": "m",
                                                "database": "t.db", "state": "completed"}))
    (case / "input.json").write_text(json.dumps({"query": "Population of A"}))
    events = [{"direction": "server", "message": {}}] + [{"direction": "query", "message": c} for c in calls]
    (case / "trajectory.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    for name, sql in (("final.sql", final), ("final.lenient.sql", lenient)):
        if sql:
            (case / name).write_text(sql + "\n")
    return case


def test_calls_in_order_with_outcomes(tmp_path):
    case = make_case(tmp_path, [
        {"arguments": {"sql": "SELECT name FROM sqlite_master;"}, "result": {"columns": ["name"], "rows": [["t"]]}},
        {"arguments": {"sql": "SELECT x FROM t"}, "result": {"error": "no such column: x"}},
        {"arguments": {"sql": "SELECT v FROM t"}, "result": {"columns": ["v"], "rows": [[1], [2], [3], [4]]}},
    ], final="SELECT v FROM t")
    text = write_sql_calls(case).read_text()
    assert "-- query:\n-- Population of A" in text
    assert text.index("[1/3]") < text.index("[2/3]") < text.index("[3/3]") < text.index("[final SQL]")
    assert "SELECT name FROM sqlite_master;\n-- 1 rows; columns: name" in text
    assert "-- error: no such column: x" in text
    assert "--   [3]\n--   ..." in text
    assert "master;;" not in text


def test_lenient_and_missing_final(tmp_path):
    case = make_case(tmp_path, [], lenient="SELECT 1")
    assert "[final SQL, read out of the answer]\nSELECT 1;" in write_sql_calls(case).read_text()
    (case / "final.lenient.sql").unlink()
    assert write_sql_calls(case).read_text().endswith("-- [no final SQL]\n")


def test_file_runs_as_a_script(tmp_path):
    database = tmp_path / "t.db"
    with sqlite3.connect(database) as db:
        db.execute("CREATE TABLE t (v INTEGER)")
    case = make_case(tmp_path, [{"arguments": {"sql": "SELECT v FROM t"}, "result": {"columns": ["v"], "rows": []}}],
                     final="SELECT COUNT(*) FROM t")
    with sqlite3.connect(database) as db:
        db.executescript(write_sql_calls(case).read_text())
