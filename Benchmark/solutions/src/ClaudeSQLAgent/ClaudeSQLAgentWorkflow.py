"""Comparison solution: the SQLAgent baseline with Claude instead of Codex/GPT.

Same prompt (`../SQLAgent/prompt.txt`), same tool (`sqlite_query`, the same SQLiteQueryTool behind a local MCP
server), same budgets. The runtime is Claude Code in non-interactive mode, reduced to a model and a tool loop:
every built-in tool disabled (`--tools ""`), only this MCP server (`--strict-mcp-config`), no user or project
settings, CLAUDE.md or memories (`--setting-sources ""`, an empty temporary working directory), no skills, the
default system prompt replaced, no session persisted. The session's init event is checked: if any tool other than
`sqlite_query` is available, or any other tool is used, the case fails as an isolation violation.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

from ....benchmarking.utils.struct import SolutionOutput
from ..SQLAgent.SQLAgentWorkflow import extract_select

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
TOOL = "mcp__vdem__sqlite_query"


class ClaudeSQLAgentWorkflow:
    name = "ClaudeSQLAgent"

    def __init__(self, config: dict | None = None):
        self.config = config or json.loads((HERE / "config.json").read_text())
        self.prompt = (HERE.parent / "SQLAgent" / "prompt.txt").read_text()
        self.prompt_sha256 = hashlib.sha256(self.prompt.encode()).hexdigest()

    def command(self, mcp_config: Path, stream_input: bool = False) -> list[str]:
        streaming = ["--input-format", "stream-json"] if stream_input else []
        return ["claude", "-p", *streaming, "--model", self.config["model"], "--output-format", "stream-json", "--verbose",
                "--tools", "", "--strict-mcp-config", "--mcp-config", str(mcp_config),
                "--allowedTools", TOOL, "--setting-sources", "", "--disable-slash-commands",
                "--no-session-persistence", "--system-prompt", self.prompt]

    def solve(self, payload: dict, database: Path, log: Callable[[str, dict], None]) -> SolutionOutput:
        with tempfile.TemporaryDirectory(prefix="owid-vdem-claude-") as tmp:
            work = Path(tmp)
            queries = work / "queries.jsonl"
            queries.touch()
            mcp_config = work / "mcp.json"
            mcp_config.write_text(json.dumps({"mcpServers": {"vdem": {
                "command": sys.executable,
                "args": [str(HERE / "sqlite_mcp_server.py"), str(Path(database).resolve()), str(queries),
                         str(self.config["max_tool_calls"]), str(self.config["query_timeout_seconds"]),
                         str(self.config["max_query_rows"])]}}}))
            env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_") and k != "CLAUDECODE"}
            usage = model = None
            final, error = None, None
            try:
                if payload.get("image"):  # text and image in one user message (stream-json input)
                    data = base64.b64encode((REPO_ROOT / payload["image"]).read_bytes()).decode()
                    message = {"type": "user", "message": {"role": "user", "content": [
                        {"type": "text", "text": payload["query"]},
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}]}}
                    command, stdin = self.command(mcp_config, stream_input=True), json.dumps(message) + "\n"
                else:
                    command, stdin = self.command(mcp_config), payload["query"]
                process = subprocess.run(command, input=stdin, capture_output=True,
                                         text=True, cwd=work, env=env, timeout=self.config["timeout_seconds"])
                for line in process.stdout.splitlines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    log("model_event", event)
                    if event.get("type") == "system" and event.get("subtype") == "init":
                        model = event.get("model")
                        tools = set(event.get("tools", []))
                        if tools != {TOOL}:
                            raise RuntimeError(f"Isolation violation: tools available {sorted(tools)}")
                    if event.get("type") == "assistant":
                        for block in event.get("message", {}).get("content", []):
                            if block.get("type") == "tool_use" and block.get("name") != TOOL:
                                raise RuntimeError(f"Isolation violation: tool {block.get('name')}")
                    if event.get("type") == "result":
                        usage = event.get("usage")
                        final = event.get("result")
                        if event.get("is_error"):
                            error = f"Claude run ended with an error: {event.get('subtype')}"
                if final is None and error is None:
                    error = f"No result from Claude (exit {process.returncode}): {process.stderr[-500:]}"
            except subprocess.TimeoutExpired:
                error = f"Timed out after {self.config['timeout_seconds']} s"
            except Exception as exc:  # reported as an execution failure, never retried silently
                error = f"{type(exc).__name__}: {exc}"
            calls = 0
            for line in queries.read_text().splitlines():
                calls += 1
                log("query", json.loads(line))
        sql = extract_select(final) if final and not error else None
        if error is None and sql is None:
            error = "Final answer is not a SELECT statement"
        return SolutionOutput(final_sql=sql, answer_text=final or "", tool_calls=calls, usage=usage,
                              model=model or self.config["model"], error=error)
