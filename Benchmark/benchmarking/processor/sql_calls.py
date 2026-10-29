"""A readable, runnable record of the SQL calls in one case directory.

sql_calls.sql holds a header (task, level, repeat, solution, model, database, state, the query the solution received),
then each sqlite_query call in order, numbered, with its outcome as a comment (columns, number of rows and the first
rows, or the error), then the final SQL (and the lenient one, if the answer had prose around it). Statements end with
";", so the file runs as is: sqlite3 -readonly data/sqlite/vdem2026.db < sql_calls.sql. It is derived from
trajectory.jsonl, meta.json and the final SQL files, and rewritten whenever one of them changes.
"""
import json
from pathlib import Path

PREVIEW_ROWS = 3
QUERY_CHARS = 600


def comment(text: str) -> str:
    return "\n".join(f"-- {line}".rstrip() for line in str(text).splitlines() or [""])


def statement(sql: str) -> str:
    return sql.strip().rstrip(";").rstrip() + ";"


def outcome(result: dict) -> str:
    if "error" in result:
        return comment(f"error: {result['error']}")
    rows = result.get("rows", [])
    lines = [f"{len(rows)} rows; columns: {', '.join(map(str, result.get('columns', [])))}"]
    lines += [f"  {json.dumps(row, ensure_ascii=False)[:200]}" for row in rows[:PREVIEW_ROWS]]
    if len(rows) > PREVIEW_ROWS:
        lines.append("  ...")
    return comment("\n".join(lines))


def render(case_dir: Path) -> str:
    meta = json.loads((case_dir / "meta.json").read_text())
    query = json.loads((case_dir / "input.json").read_text()).get("query", "")
    if len(query) > QUERY_CHARS:
        query = query[:QUERY_CHARS] + f" ... [{len(query) - QUERY_CHARS} more characters in input.json]"
    parts = [comment(f"task: {case_dir.parent.parent.name}\nlevel: {meta['level']}  repeat: {meta['repeat']}\n"
                     f"solution: {meta['solution']}  model: {meta.get('model')}  "
                     f"database: {meta.get('database', 'vdem2026.db')}\nstate: {meta['state']}"),
             comment("query:\n" + query)]
    events = [json.loads(line) for line in (case_dir / "trajectory.jsonl").open(encoding="utf-8")]
    calls = [event["message"] for event in events if event.get("direction") == "query"]
    for number, call in enumerate(calls, 1):
        sql = (call.get("arguments") or {}).get("sql") or ""
        parts.append(f"-- [{number}/{len(calls)}]\n{statement(sql)}\n{outcome(call.get('result', {}))}")
    finals = [(name, label) for name, label in (("final.sql", "final SQL"),
                                                ("final.lenient.sql", "final SQL, read out of the answer"))
              if (case_dir / name).exists() and (case_dir / name).read_text(encoding="utf-8").strip()]
    for name, label in finals:
        parts.append(f"-- [{label}]\n{statement((case_dir / name).read_text(encoding='utf-8'))}")
    if not finals:
        parts.append("-- [no final SQL]")
    return "\n\n".join(parts) + "\n"


def write_sql_calls(case_dir: Path) -> Path:
    path = case_dir / "sql_calls.sql"
    path.write_text(render(case_dir), encoding="utf-8")
    return path
