"""Baseline solution: a general-purpose agent with one read-only SQL tool (the professor's baseline setting).

The agent runs in an isolated Codex session (no shell, files, network or plugins). Its final message must be one
SELECT statement; the processor executes it. Every tool call and model event is passed to `log`.
"""
import base64
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Callable

from ....benchmarking.tools.sqlite_tool import SQLiteQueryTool
from ....benchmarking.utils.struct import SolutionOutput
from .codex_session import CodexSession

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]


class ToolBudgetExceeded(RuntimeError):
    pass


def extract_select(text: str) -> str | None:
    """The final answer's SQL, tolerating a Markdown fence; None if it is not a SELECT/WITH statement."""
    body = re.sub(r"^```(?:sql)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    return body if re.match(r"(?is)^\s*(with|select)\b", body) else None


def image_urls(payload: dict) -> list[str]:
    """The payload's image (if any) as a data URL; the path is relative to the repository root."""
    if not payload.get("image"):
        return []
    data = base64.b64encode((REPO_ROOT / payload["image"]).read_bytes()).decode()
    return [f"data:image/png;base64,{data}"]


class SQLAgentWorkflow:
    name = "SQLAgent"

    def __init__(self, config: dict | None = None):
        self.config = config or json.loads((HERE / "config.json").read_text())
        self.prompt = (HERE / "prompt.txt").read_text()
        self.prompt_sha256 = hashlib.sha256(self.prompt.encode()).hexdigest()

    def solve(self, payload: dict, database: Path, log: Callable[[str, dict], None]) -> SolutionOutput:
        calls = 0
        tool = SQLiteQueryTool(database, timeout=self.config["query_timeout_seconds"], max_rows=self.config["max_query_rows"])

        def on_query(arguments):
            nonlocal calls
            if calls >= self.config["max_tool_calls"]:
                raise ToolBudgetExceeded("Maximum SQL tool calls reached")
            calls += 1
            try:
                arguments = json.loads(arguments) if isinstance(arguments, str) else arguments
                result = tool.query(arguments["sql"])
            except (sqlite3.Error, ValueError, KeyError, TypeError) as exc:
                result = {"error": str(exc)}
            log("query", {"arguments": arguments, "result": result})
            return result

        session = CodexSession(self.config, log)
        try:
            with session:
                answer = session.run(self.prompt, payload["query"], on_query, images=image_urls(payload))
            sql = extract_select(answer)
            return SolutionOutput(final_sql=sql, answer_text=answer, tool_calls=calls, usage=session.usage,
                                  model=session.resolved_model,
                                  error=None if sql else "Final answer is not a SELECT statement")
        except Exception as exc:  # reported as an execution failure, never retried silently
            return SolutionOutput(final_sql=None, answer_text="", tool_calls=calls, usage=session.usage,
                                  model=session.resolved_model, error=f"{type(exc).__name__}: {exc}")
        finally:
            tool.close()
