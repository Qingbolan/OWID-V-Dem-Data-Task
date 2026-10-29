import sqlite3

import pytest

from Benchmark.benchmarking.tools.sqlite_tool import SQLiteQueryTool


@pytest.fixture()
def database(tmp_path):
    path = tmp_path / "t.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE t (v INTEGER)")
        db.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(10)])
    return path


def test_select_and_schema(database):
    with SQLiteQueryTool(database) as tool:
        assert tool.query("SELECT COUNT(*) FROM t")["rows"] == [(10,)]
        assert tool.query("SELECT name FROM pragma_table_info('t')")["rows"] == [("v",)]


@pytest.mark.parametrize("sql", ["INSERT INTO t VALUES (1)", "DELETE FROM t", "CREATE TABLE u (x)",
                                 "ATTACH DATABASE ':memory:' AS m"])
def test_writes_are_denied(database, sql):
    with SQLiteQueryTool(database) as tool, pytest.raises(sqlite3.Error):
        tool.query(sql)


def test_row_cap(database):
    with SQLiteQueryTool(database, max_rows=5) as tool, pytest.raises(ValueError):
        tool.query("SELECT * FROM t")
