"""Run one (solution, task, level, repeat) case and persist every artefact (mirrors GemBench's Processor).

Case directory layout:
    input.json         exactly what the solution received
    trajectory.jsonl   every tool call and model event, in order
    answer.txt         the solution's final message
    final.sql          the SELECT the host executed (if any)
    output.csv         the executed result
    meta.json          state, timing, tool calls, token usage, model, hashes
    sql_calls.sql      every SQL call with its outcome, then the final SQL (derived from the files above)
Directories are created exclusively: an existing case is never overwritten.
"""
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..tools.sqlite_tool import SQLiteQueryTool
from ..utils.struct import CaseRecord, InputLevel, Task
from .sql_calls import write_sql_calls

HOST_TIMEOUT_SECONDS = 120
HOST_MAX_ROWS = 2_000_000


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Processor:
    def __init__(self, database: Path):
        self.database = database

    def run_case(self, solution, task: Task, level: InputLevel, repeat: int, run_dir: Path) -> CaseRecord:
        case_dir = run_dir / task.task_id / level.value / f"repeat-{repeat}"
        case_dir.mkdir(parents=True, exist_ok=False)
        payload = task.payload(level)
        (case_dir / "input.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
        started = time.monotonic()
        with (case_dir / "trajectory.jsonl").open("x", encoding="utf-8") as trajectory:
            def log(direction: str, message: dict) -> None:
                trajectory.write(json.dumps({"direction": direction, "message": message}, ensure_ascii=False,
                                            default=str) + "\n")
                trajectory.flush()

            result = solution.solve(payload, task.database, log)
        (case_dir / "answer.txt").write_text(result.answer_text, encoding="utf-8")
        state, error = ("failed", result.error) if result.error else ("completed", None)
        if result.final_sql:
            (case_dir / "final.sql").write_text(result.final_sql + "\n", encoding="utf-8")
            try:
                with SQLiteQueryTool(task.database, timeout=HOST_TIMEOUT_SECONDS, max_rows=HOST_MAX_ROWS) as host:
                    executed = host.query(result.final_sql)
                pd.DataFrame(executed["rows"], columns=executed["columns"]).to_csv(case_dir / "output.csv", index=False)
            except (sqlite3.Error, ValueError) as exc:
                state, error = "failed", f"Host execution failed: {exc}"
        meta = {"task_id": task.task_id, "solution": getattr(solution, "name", type(solution).__name__),
                "level": level.value, "repeat": repeat, "state": state, "error": error,
                "elapsed_seconds": round(time.monotonic() - started, 2), "tool_calls": result.tool_calls,
                "model": result.model, "token_usage": result.usage, "input_sha256": sha256(case_dir / "input.json"),
                "database": task.database.name, "variant": task.variant,
                "gold_sha256": sha256(task.gold_csv), "finished_at": datetime.now(timezone.utc).isoformat()}
        (case_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        write_sql_calls(case_dir)
        return CaseRecord(task.task_id, meta["solution"], level, repeat, case_dir, state, meta)
