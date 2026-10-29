"""Read-only SQLite access: the only data capability a solution receives."""
import sqlite3
import time
from pathlib import Path

TOOL_SPEC = {
    "type": "function",
    "name": "sqlite_query",
    "description": ("Execute a read-only SQLite SELECT. Inspect sqlite_master or pragma_table_info('table') to "
                    "discover the schema. Results are bounded; use LIMIT for exploration."),
    "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"],
                    "additionalProperties": False},
}


class SQLiteQueryTool:
    """Bounded, read-only queries: no writes, attachments or extension loading; per-query timeout and row cap."""

    _ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_RECURSIVE}
    _FORBIDDEN_FUNCTIONS = {"load_extension", "writefile", "readfile"}

    def __init__(self, path: Path, *, timeout: float = 30.0, max_rows: int = 500):
        self._db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True, check_same_thread=False)
        self._db.execute("PRAGMA query_only=ON")
        self._db.set_authorizer(self._authorize)
        self.timeout, self.max_rows = timeout, max_rows

    def _authorize(self, action, arg1, arg2, database, trigger):
        if action in self._ALLOWED:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_FUNCTION and arg2 not in self._FORBIDDEN_FUNCTIONS:
            return sqlite3.SQLITE_OK
        if action == sqlite3.SQLITE_PRAGMA and arg1 == "table_info":
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    def query(self, sql: str) -> dict:
        deadline = time.monotonic() + self.timeout
        self._db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 10_000)
        try:
            cursor = self._db.execute(sql)
            if cursor.description is None:
                raise ValueError("A result-producing SELECT is required")
            rows = cursor.fetchmany(self.max_rows + 1)
            if len(rows) > self.max_rows:
                raise ValueError(f"Result exceeds {self.max_rows} rows; narrow the query")
            return {"columns": [c[0] for c in cursor.description], "rows": rows}
        finally:
            self._db.set_progress_handler(None, 0)

    def close(self) -> None:
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
