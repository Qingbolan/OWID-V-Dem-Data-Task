"""Command line interface.

    python -m Benchmark.cli tasks  [--dataset VDEM_2026]
    python -m Benchmark.cli show   <task_id> [--level subtitle]
    python -m Benchmark.cli run    [--solution SQLAgent] [--level title subtitle article] [--repeats 3] [--task ID ...] [--richest]
    python -m Benchmark.cli report <run_dir>
    python -m Benchmark.cli evaluate <run_dir>   (re-evaluate recorded cases; no solution is called)
"""
import argparse
import json
from pathlib import Path

from ..benchmarking import InputLevel, OWIDBench, OWIDDatasets
from ..benchmarking.utils.report import write_report
from ..solutions.src import SOLUTIONS


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m Benchmark.cli", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    tasks = commands.add_parser("tasks", help="list reproducible tasks")
    tasks.add_argument("--dataset", nargs="*")
    show = commands.add_parser("show", help="print the input a solution receives")
    show.add_argument("task_id")
    show.add_argument("--level", default="subtitle", choices=[level.value for level in InputLevel])
    run = commands.add_parser("run", help="run solutions and evaluate")
    run.add_argument("--solution", nargs="+", default=["SQLAgent"], choices=sorted(SOLUTIONS))
    run.add_argument("--dataset", nargs="*")
    run.add_argument("--level", nargs="+", default=[level.value for level in InputLevel], choices=[level.value for level in InputLevel])
    run.add_argument("--repeats", type=int, default=3)
    run.add_argument("--task", nargs="*")
    run.add_argument("--tags", default="")
    run.add_argument("--resume", type=Path, help="continue an interrupted run directory in place")
    run.add_argument("--richest", action="store_true",
                     help="per task, run only the last --level it supports (e.g. --level subtitle article)")
    evaluate = commands.add_parser("evaluate", help="re-evaluate the recorded cases of a run")
    evaluate.add_argument("run_dir", type=Path)
    evaluate.add_argument("--dataset", default="VDEM_2026", help="dataset the run used (task ids repeat across datasets)")
    evaluate.add_argument("--lenient", action="store_true",
                          help="also read SQL out of non-bare answers (written to *.lenient.* files; originals kept)")
    report = commands.add_parser("report", help="rebuild report.md from evaluation_result.json")
    report.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    if args.command == "tasks":
        for task in OWIDDatasets(args.dataset).get_all_tasks():
            print(f"{task.task_id}\t{task.category}\t{task.figure_name}")
    elif args.command == "show":
        task = next(t for t in OWIDDatasets().get_all_tasks() if t.task_id == args.task_id)
        print(json.dumps(task.payload(InputLevel(args.level)), ensure_ascii=False, indent=1))
    elif args.command == "run":
        bench = OWIDBench({name: SOLUTIONS[name]() for name in args.solution}, data_sets=args.dataset,
                          levels=[InputLevel(level) for level in args.level], n_repeats=args.repeats, task_ids=args.task,
                          tags=args.tags, richest=args.richest)
        print(json.dumps(bench.run(resume=args.resume), ensure_ascii=False, indent=1))
    elif args.command == "evaluate":
        bench = OWIDBench({}, data_sets=[args.dataset])
        result = bench.evaluate_lenient(args.run_dir) if args.lenient else bench.reevaluate(args.run_dir)
        print(json.dumps(result, ensure_ascii=False, indent=1))
    elif args.command == "report":
        results = json.loads((args.run_dir / "evaluation_result.json").read_text())
        print(json.dumps(write_report(args.run_dir, results), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
