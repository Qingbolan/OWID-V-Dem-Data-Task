# Benchmark

Runs solutions on the reproducible figures in `OWID/` (124 tasks) and scores the executed results. Every query ends
with the output columns and their precision as supplementary material (docs/decisions/0006). A chart page has no
article level; image levels need redacted images, which this repository does not have yet. Unsupported levels are
skipped (`Task.supports`). The package layout mirrors GEM-Bench's `GemBench` package.

```
Benchmark/
├── benchmarking/
│   ├── OWIDBench.py              Entry point: solutions x tasks x input levels x repeats -> evaluate -> report
│   ├── dataset/
│   │   ├── OWIDDatasets.py       Builds tasks from OWID/ figures whose golden program verified as `match`
│   │   └── VDEM_2026/            dataset.json (the 102 page and chart-page folders)
│   ├── evaluator/
│   │   ├── base_evaluator.py
│   │   ├── quantitative_evaluator/   Cell-level comparison with the figure CSV (implemented)
│   │   ├── claim_evaluator/          Claim-level evaluation for open article settings (planned)
│   │   └── failure_evaluator/        Failure categorisation (planned)
│   ├── processor/processor.py    Runs one case and persists input, trajectory, SQL, result and metadata
│   ├── tools/sqlite_tool.py      Read-only, bounded SQL access (the only data capability of a solution)
│   ├── utils/                    Paths, logging, data structures, reports
│   └── output/                   One directory per run (not in git)
├── cli/                          python -m Benchmark.cli
├── demo/                         Smallest end-to-end run
└── solutions/src/
    ├── SQLAgent/                 Baseline: general-purpose agent + read-only SQL, Codex / GPT (implemented)
    └── ClaudeSQLAgent/           The same baseline with Claude: same prompt, tool and budgets (implemented)
```

## Usage

```bash
uv run python -m Benchmark.cli tasks                                  # reproducible tasks
uv run python -m Benchmark.cli show <task_id> --level subtitle        # exact solution input
uv run python -m Benchmark.cli run --level title subtitle article --repeats 3
uv run python -m Benchmark.cli run --level article --repeats 1                # only the 43 tasks with page text
uv run python -m Benchmark.cli run --level subtitle article --richest       # per task, its richest level only
uv run python -m Benchmark.demo.main                                  # one task, one level, one repeat
```

`SQLAgent` runs in an isolated Codex app-server session (no shell, files, network or plugins) and needs a logged-in
Codex CLI. Its model, reasoning effort, tool-call budget and timeouts are in `solutions/src/SQLAgent/config.json`.
`ClaudeSQLAgent` is the comparison: the same prompt file and the same `sqlite_query` implementation (served by a
local MCP server, `sqlite_mcp_server.py`), run by Claude Code in non-interactive mode with every built-in tool
disabled, no settings, CLAUDE.md, memories or skills loaded, and an empty working directory; it needs a logged-in
Claude Code CLI. The session's init event is checked, and a case fails if any other tool is available or used.
The Claude account adds a one-line context note to the message (the account e-mail); it carries no task data.

## Input levels

One natural-language query per case, with no output schema: `title` (the chart title), `subtitle` (title and
subtitle) and `article` (title, subtitle and the report's full text). Results are matched to the figure by value;
see [`docs/task-definition.md`](../docs/task-definition.md).

## Run directory

```
output/<YYYYMMDD_HHMMSS>_<solutions>_<models>_repeat-<n>[_<tags>]/
├── manifest.json                         configuration and hashes of every input that determines the result
├── <task_id>/<level>/repeat-<k>/
│   ├── input.json  trajectory.jsonl  answer.txt  final.sql  output.csv  meta.json  sql_calls.sql  evaluation.json
├── evaluation_result.json                one record per case
├── report.json  report.md                correct cases by solution, level and category
```

Run directories are created exclusively and never overwritten.

## Adding a solution

Implement a class with `name`, `config`, `prompt_sha256` and
`solve(payload: dict, database: Path, log) -> SolutionOutput`, and register it in `solutions/src/__init__.py`.
