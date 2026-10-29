"""Benchmark entry point (mirrors GemBench.py): solutions x tasks x input levels x repeats -> evaluate -> report.

Before any case runs, the run directory receives manifest.json with the configuration and the hashes of every
input that determines the result (prompts, solution configs, gold CSVs, golden specs, database fingerprints).
"""
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from .dataset.OWIDDatasets import OWIDDatasets
from .evaluator import QuantEvaluator
from .processor import Processor, write_sql_calls
from .tools.sqlite_tool import SQLiteQueryTool
from .utils.logger import get_logger
from .utils.path import DATABASE, OUTPUT_ROOT, REPO_ROOT
from .utils.report import write_report
from .utils.struct import InputLevel


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


SQL_START = re.compile(r"(?is)\s*(with|select)\b")
SQL_WORD = re.compile(r"(?i)^\s*([()]|with|select|from|where|union|join|left|inner|group|order|having|and|or|on|case|"
                      r"when|then|else|end|limit|as|[a-z_][a-z0-9_]*\s+as\s*\(|--)")


def last_sql_statement(answer: str) -> str | None:
    """The SQL in a free-text answer: the last fenced code block that holds a SELECT/WITH statement; otherwise the
    last run of SQL-like paragraphs that starts with a paragraph beginning with SELECT or WITH (so a word "with"
    inside a sentence is not taken for a query, and notes after the query are left out)."""
    blocks = re.findall(r"```(?:sql)?\s*(.*?)```", answer, flags=re.S | re.I)
    for block in reversed(blocks):
        if SQL_START.match(block):
            return block.strip().rstrip(";").strip()
    paragraphs = re.split(r"\n\s*\n", answer.strip())
    runs, current = [], []
    for paragraph in paragraphs:  # maximal runs of SQL-like paragraphs, each starting at a SELECT/WITH paragraph
        if current and SQL_WORD.match(paragraph):
            current.append(paragraph)
        else:
            if current:
                runs.append(current)
            current = [paragraph] if SQL_START.match(paragraph) else []
    if current:
        runs.append(current)
    if not runs:
        return None
    return "\n\n".join(runs[-1]).strip().rstrip(";").strip()


class OWIDBench:
    def __init__(self, solutions: dict, data_sets: list[str] | None = None, levels: list[InputLevel] | None = None,
                 n_repeats: int = 3, task_ids: list[str] | None = None, database: Path = DATABASE,
                 output_dir: Path = OUTPUT_ROOT, tags: str = "", richest: bool = False):
        self.logger = get_logger("OWIDBench")
        self.solutions, self.n_repeats, self.database, self.tags = solutions, n_repeats, database, tags
        self.richest = richest  # per task, run only the last of `levels` (in the given order) that the task supports
        self.levels = levels or list(InputLevel)
        self.datasets = OWIDDatasets(data_sets)
        tasks = self.datasets.get_all_tasks()
        self.tasks = [t for t in tasks if not task_ids or t.task_id in task_ids]
        self.output_dir = output_dir
        self.processor, self.evaluator = Processor(database), QuantEvaluator()

    def levels_for(self, task) -> list[InputLevel]:
        """The levels a task runs at: those it supports (a chart page has no article level, no task has an image
        yet), or with `richest` only the last of them, e.g. article where a page shows the chart, else subtitle."""
        supported = [level for level in self.levels if task.supports(level)]
        return supported[-1:] if self.richest else supported

    def _run_dir(self) -> Path:
        stamp = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y%m%d_%H%M%S")
        models = "-".join(sorted({getattr(s, "config", {}).get("model", "unknown") for s in self.solutions.values()}))
        name = f"{stamp}_{'-'.join(self.solutions)}_{models}_repeat-{self.n_repeats}" + (f"_{self.tags}" if self.tags else "")
        return self.output_dir / name

    def _manifest(self, run_dir: Path) -> None:
        manifest = {
            "solutions": {name: getattr(s, "config", {}) for name, s in self.solutions.items()},
            "levels": [level.value for level in self.levels], "richest_level_only": self.richest,
            "n_repeats": self.n_repeats,
            "tasks": {t.task_id: {"figure": t.figure_name, "gold_sha256": _sha256(t.gold_csv),
                                  "spec_sha256": _sha256(t.spec_path)} for t in self.tasks},
            "databases": sorted({str(t.database.relative_to(REPO_ROOT)) for t in self.tasks}),
            "database_manifests_sha256": {name: _sha256(REPO_ROOT / "data/manifests" / name)
                                          for name in ("BUILD.json", "database_raw.json")
                                          if (REPO_ROOT / "data/manifests" / name).exists()},
            "prompts_sha256": {name: getattr(s, "prompt_sha256", None) for name, s in self.solutions.items()}}
        (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=str))

    def run(self, resume: Path | None = None) -> dict:
        """Run every (solution, task, level, repeat) case. With `resume`, continue an interrupted run in place:
        completed cases (those with meta.json) are kept, a case left half-written is removed and run again, and the
        run's manifest is kept."""
        if not self.tasks:
            raise ValueError("No reproducible tasks selected; run `make golden` first")
        if resume:
            run_dir = resume
            for case_dir in run_dir.glob("*/*/repeat-*"):
                if not (case_dir / "meta.json").exists():
                    shutil.rmtree(case_dir)
        else:
            run_dir = self._run_dir()
            run_dir.mkdir(parents=True, exist_ok=False)
            self._manifest(run_dir)
        self.logger.info("run %s: %d tasks x %d levels x %d repeats x %d solutions", run_dir.name, len(self.tasks),
                         len(self.levels), self.n_repeats, len(self.solutions))
        results = []
        for name, solution in self.solutions.items():
            for task in self.tasks:
                for level in self.levels_for(task):
                    for repeat in range(1, self.n_repeats + 1):
                        done = run_dir / task.task_id / level.value / f"repeat-{repeat}"
                        if resume and (done / "meta.json").exists():
                            result = self.evaluator.evaluate(task, done)
                            (done / "evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=1,
                                                                             default=str))
                            results.append(result | {"solution": name, "level": level.value, "repeat": repeat,
                                                     "category": task.category})
                            continue
                        case = self.processor.run_case(solution, task, level, repeat, run_dir)
                        result = self.evaluator.evaluate(task, case.directory)
                        (case.directory / "evaluation.json").write_text(json.dumps(result, ensure_ascii=False,
                                                                                   indent=1, default=str))
                        results.append(result | {"solution": name, "level": level.value, "repeat": repeat,
                                                 "category": task.category})
                        self.logger.info("%s %s %s #%d: %s", name, task.task_id, level.value, repeat,
                                         "correct" if result.get("correct") else "incorrect")
        return write_report(run_dir, results) | {"run_dir": str(run_dir)}

    def evaluate_lenient(self, run_dir: Path) -> dict:
        """A second reading of a run: cases that failed only because the final answer was not a bare SELECT (for
        example a sentence before the query) get the last SQL statement of their answer executed on the same
        database. Nothing recorded is changed: the query and its result are written to final.lenient.sql (also added
        to sql_calls.sql) and output.lenient.csv, and the results to evaluation_result.lenient.json and
        report.lenient.md."""
        tasks = {task.task_id: task for task in self.tasks}
        results = []
        for case_dir in sorted(run_dir.glob("*/*/repeat-*")):
            meta = json.loads((case_dir / "meta.json").read_text())
            task = tasks[case_dir.parent.parent.name]
            evaluation_dir = case_dir
            recovered = False
            if meta.get("error") == "Final answer is not a SELECT statement":
                sql = last_sql_statement((case_dir / "answer.txt").read_text())
                if sql:
                    lenient = run_dir / ".lenient" / case_dir.relative_to(run_dir)
                    lenient.mkdir(parents=True, exist_ok=True)
                    (case_dir / "final.lenient.sql").write_text(sql + "\n")
                    write_sql_calls(case_dir)
                    (lenient / "final.sql").write_text(sql + "\n")
                    state = "completed"
                    try:
                        with SQLiteQueryTool(task.database, timeout=60, max_rows=10_000_000) as host:
                            executed = host.query(sql)
                        frame = pd.DataFrame(executed["rows"], columns=executed["columns"])
                        frame.to_csv(case_dir / "output.lenient.csv", index=False)
                        frame.to_csv(lenient / "output.csv", index=False)
                    except (sqlite3.Error, ValueError) as exc:
                        state = "failed"
                        meta = meta | {"error": f"Host execution failed: {exc}"}
                    (lenient / "meta.json").write_text(json.dumps(meta | {"state": state}))
                    evaluation_dir, recovered = lenient, True
            result = self.evaluator.evaluate(task, evaluation_dir)
            results.append(result | {"solution": meta["solution"], "level": meta["level"], "repeat": meta["repeat"],
                                     "category": task.category, "answer_recovered": recovered})
        (run_dir / "evaluation_result.lenient.json").write_text(json.dumps(results, ensure_ascii=False, indent=1,
                                                                           default=str))
        summary = write_report(run_dir / ".lenient", results)
        (run_dir / ".lenient" / "report.md").rename(run_dir / "report.lenient.md")
        return summary | {"recovered": sum(r["answer_recovered"] for r in results)}

    def reevaluate(self, run_dir: Path) -> dict:
        """Evaluate the recorded cases of a run again (no solution is called), e.g. after an evaluation fix.

        The previous evaluation_result.json and report files are kept with the time of re-evaluation appended.
        """
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for name in ("evaluation_result.json", "report.json", "report.md"):
            if (run_dir / name).exists():
                (run_dir / name).rename(run_dir / f"{Path(name).stem}.before-{stamp}{Path(name).suffix}")
        tasks = {task.task_id: task for task in self.tasks}
        results = []
        for case_dir in sorted(run_dir.glob("*/*/repeat-*")):
            meta = json.loads((case_dir / "meta.json").read_text())
            task = tasks[case_dir.parent.parent.name]
            result = self.evaluator.evaluate(task, case_dir)
            (case_dir / "evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str))
            results.append(result | {"solution": meta["solution"], "level": meta["level"], "repeat": meta["repeat"],
                                     "category": task.category})
        return write_report(run_dir, results) | {"run_dir": str(run_dir), "reevaluated_at": stamp}
