"""Smallest end-to-end run: one task, one level, one repeat with the SQL-only baseline.

    python -m Benchmark.demo.main

Requires the database (`make data`), verified golden programs (`make golden`) and a logged-in Codex CLI.
"""
from ..benchmarking import InputLevel, OWIDBench, OWIDDatasets
from ..solutions.src import SQLAgentWorkflow


def main() -> None:
    first = OWIDDatasets().get_all_tasks()[0]
    bench = OWIDBench({"SQLAgent": SQLAgentWorkflow()}, levels=[InputLevel.DESCRIPTION], n_repeats=1,
                      task_ids=[first.task_id], tags="demo")
    print(bench.run())


if __name__ == "__main__":
    main()
