"""Minimal MCP server (stdio, JSON-RPC 2.0) exposing the benchmark's one tool, `sqlite_query`.

    python sqlite_mcp_server.py <database> <query_log.jsonl> <max_calls> <timeout_seconds> <max_rows>

It wraps the same SQLiteQueryTool the Codex-based SQLAgent uses (read-only, bounded), enforces the per-case tool
budget, and appends every call and its result to <query_log.jsonl> for the case trajectory.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from Benchmark.benchmarking.tools.sqlite_tool import TOOL_SPEC, SQLiteQueryTool  # noqa: E402

PROTOCOL = "2025-06-18"


def main() -> None:
    database, log_path, max_calls, timeout, max_rows = sys.argv[1:6]
    tool = SQLiteQueryTool(Path(database), timeout=float(timeout), max_rows=int(max_rows))
    calls = 0
    with open(log_path, "a", encoding="utf-8") as log:
        for line in sys.stdin:
            if not line.strip():
                continue
            message = json.loads(line)
            method, ident = message.get("method"), message.get("id")
            if ident is None:  # notifications (initialized, cancelled) need no answer
                continue
            if method == "initialize":
                result = {"protocolVersion": message.get("params", {}).get("protocolVersion", PROTOCOL),
                          "capabilities": {"tools": {}}, "serverInfo": {"name": "vdem", "version": "1.0"}}
            elif method == "tools/list":
                result = {"tools": [{"name": TOOL_SPEC["name"], "description": TOOL_SPEC["description"],
                                     "inputSchema": TOOL_SPEC["inputSchema"]}]}
            elif method == "tools/call":
                arguments = message["params"].get("arguments", {})
                if calls >= int(max_calls):
                    output = {"error": "Maximum SQL tool calls reached"}
                else:
                    calls += 1
                    try:
                        output = tool.query(arguments["sql"])
                    except (sqlite3.Error, ValueError, KeyError, TypeError) as exc:
                        output = {"error": str(exc)}
                log.write(json.dumps({"arguments": arguments, "result": output}, ensure_ascii=False, default=str) + "\n")
                log.flush()
                result = {"content": [{"type": "text", "text": json.dumps(output, ensure_ascii=False, default=str)}],
                          "isError": "error" in output}
            elif method == "ping":
                result = {}
            else:
                sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": ident,
                                             "error": {"code": -32601, "message": f"Unknown method {method}"}}) + "\n")
                sys.stdout.flush()
                continue
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": ident, "result": result}, default=str) + "\n")
            sys.stdout.flush()
    tool.close()


if __name__ == "__main__":
    main()
