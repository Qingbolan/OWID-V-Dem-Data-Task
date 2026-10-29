"""Write sql_calls.sql into every case directory of existing runs (new runs write it themselves).

    python -m scripts.export_sql_calls <run_dir> [<run_dir> ...]

See Benchmark/benchmarking/processor/sql_calls.py for the file's content.
"""
import sys
from pathlib import Path

from Benchmark.benchmarking.processor import write_sql_calls


def main() -> None:
    for run in map(Path, sys.argv[1:]):
        cases = sorted(run.glob("*/*/repeat-*"))
        for case in cases:
            write_sql_calls(case)
        print(f"{run.name}: {len(cases)} cases")


if __name__ == "__main__":
    main()
