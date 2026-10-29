"""Analyse benchmark runs: accuracy with confidence intervals, sensitivity to evaluation rules, cost and time.

    python -m scripts.analyze_runs <out.json> <run_dir>:<dataset> [<run_dir>:<dataset> ...]

Reads the recorded cases of each run (nothing is re-run). Every case is scored in two readings:
- strict: the benchmark result as recorded (`evaluation.json`): a final answer that is not a bare SELECT fails;
- lenient: `evaluation_result.lenient.json` where it exists (the SQL read out of a non-bare answer, see
  `python -m Benchmark.cli evaluate --lenient`), otherwise the strict result.
The lenient reading is then re-scored under alternative evaluation rules (tolerance 0.1 % or 5 %, no power-of-ten
rescaling, no unpivoting of wide results, over-wide answers counted wrong) to show which conclusions depend on
which rule. Accuracy intervals are Wilson 95 % intervals over cases.
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from Benchmark.benchmarking import OWIDDatasets
from Benchmark.benchmarking.evaluator.quantitative_evaluator.quant_evaluator import (
    HARDCODED_MIN_CELLS, hardcoded_cells, load_gold, solution_tolerance)
from Benchmark.benchmarking.evaluator.quantitative_evaluator.quant_metrics import compare
from Benchmark.benchmarking.utils.path import REPO_ROOT

OVER_WIDE = 50  # entities outside the figure beyond which a correct answer counts as over-wide
VARIANTS = {
    "tolerance 0.1 %": {"rel_floor": 0.001},
    "tolerance 5 %": {"rel_floor": 0.05},
    "no power-of-ten rescaling": {"rescale": False},
    "no unpivoting of wide results": {"unpivot_wide": False},
    "over-wide counted wrong": {"over_wide_wrong": True},
}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def score(task, case_dir: Path, output: Path, sql: str, rel_floor: float = 0.01, rescale: bool = True,
          unpivot_wide: bool = True, over_wide_wrong: bool = False) -> bool:
    if not output.exists():
        return False
    frame = pd.read_csv(output)
    if frame.empty:
        return False
    spec = json.loads(task.spec_path.read_text())
    mapping = json.loads((REPO_ROOT / spec["entity_mapping"]).read_text())
    gold = load_gold(task, spec)
    tolerances = {}
    for c in task.output_columns:
        tol = solution_tolerance(spec, c, task.variant)
        if c not in spec.get("encodings", {}) and "classes_at" not in tol:
            golden_rel = (spec.get(task.variant, {}).get("compare", spec["compare"]) if task.variant else spec["compare"]).get(c, {}).get("rel", 0.0)
            tol = tol | {"rel": max(golden_rel, rel_floor)}
        tolerances[c] = tol
    result = compare(gold, frame, task.output_columns, tolerances, mapping, frozenset(spec.get("encodings", {})),
                     rescale=rescale, unpivot_wide=unpivot_wide)
    correct = result["correct"]
    if hardcoded_cells(sql, gold, task.output_columns, result.get("alignment", {})) >= HARDCODED_MIN_CELLS:
        correct = False
    if over_wide_wrong and result.get("entities_outside_figure", 0) > OVER_WIDE:
        correct = False
    return correct


def tokens(usage: dict | None, solution: str) -> tuple[int, int, int]:
    if not usage:
        return (0, 0, 0)
    if solution == "SQLAgent":
        total = usage.get("total", {})
        return (total.get("inputTokens", 0), total.get("cachedInputTokens", 0), total.get("outputTokens", 0))
    cached = usage.get("cache_read_input_tokens", 0)
    return (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + cached, cached,
            usage.get("output_tokens", 0))


def claude_cost(case_dir: Path) -> float:
    for line in (case_dir / "trajectory.jsonl").open(encoding="utf-8"):
        if '"total_cost_usd"' in line:
            event = json.loads(line)["message"]
            if event.get("type") == "result":
                return float(event.get("total_cost_usd") or 0)
    return 0.0


def main() -> None:
    out = Path(sys.argv[1])
    rows = []
    for spec in sys.argv[2:]:
        run, dataset = spec.rsplit(":", 1)
        run = Path(run)
        tasks = {t.task_id: t for t in OWIDDatasets([dataset]).get_all_tasks()}
        lenient_path = run / "evaluation_result.lenient.json"
        lenient = ({(r["task_id"], r["level"], r["repeat"]): r for r in json.loads(lenient_path.read_text())}
                   if lenient_path.exists() else {})
        for case in sorted(run.glob("*/*/repeat-*")):
            meta = json.loads((case / "meta.json").read_text())
            task = tasks[case.parent.parent.name]
            strict = json.loads((case / "evaluation.json").read_text())
            key = (task.task_id, meta["level"], meta["repeat"])
            recovered = bool(lenient.get(key, {}).get("answer_recovered"))
            output = case / ("output.lenient.csv" if recovered else "output.csv")
            sql_file = case / ("final.lenient.sql" if recovered else "final.sql")
            sql = sql_file.read_text() if sql_file.exists() else ""
            row = {"solution": meta["solution"], "dataset": dataset, "level": meta["level"], "repeat": meta["repeat"],
                   "task_id": task.task_id, "figure": task.figure_name, "category": task.category,
                   "strict": bool(strict.get("correct")), "lenient": bool(lenient.get(key, strict).get("correct")),
                   "recovered": recovered, "format_failure": meta.get("error") == "Final answer is not a SELECT statement",
                   "over_wide": strict.get("entities_outside_figure", 0) > OVER_WIDE
                   or lenient.get(key, {}).get("entities_outside_figure", 0) > OVER_WIDE,
                   "seconds": meta["elapsed_seconds"], "tool_calls": meta.get("tool_calls", 0)}
            row["tokens_in"], row["tokens_cached"], row["tokens_out"] = tokens(meta.get("token_usage"), meta["solution"])
            row["cost_usd"] = claude_cost(case) if meta["solution"] == "ClaudeSQLAgent" else None
            for name, options in VARIANTS.items():
                row[name] = score(task, case, output, sql, **options)
            rows.append(row)
    frame = pd.DataFrame(rows)
    summary = []
    for (solution, dataset, level), group in frame.groupby(["solution", "dataset", "level"]):
        n = len(group)
        entry = {"solution": solution, "dataset": dataset, "level": level, "cases": n}
        for reading in ["strict", "lenient", *VARIANTS]:
            k = int(group[reading].sum())
            low, high = wilson(k, n)
            entry[reading] = {"correct": k, "rate": k / n, "ci95": [round(low, 3), round(high, 3)]}
        entry["over_wide_correct"] = int((group["lenient"] & group["over_wide"]).sum())
        entry["format_failures"] = int(group["format_failure"].sum())
        entry["minutes_per_case"] = round(group["seconds"].mean() / 60, 2)
        entry["tool_calls_per_case"] = round(group["tool_calls"].mean(), 1)
        entry["tokens_in"], entry["tokens_out"] = int(group["tokens_in"].sum()), int(group["tokens_out"].sum())
        entry["cached_share"] = round(group["tokens_cached"].sum() / max(group["tokens_in"].sum(), 1), 2)
        entry["cost_usd"] = round(group["cost_usd"].sum(), 2) if group["cost_usd"].notna().any() else None
        summary.append(entry)
    per_task = defaultdict(dict)
    for (solution, dataset, level, task_id), group in frame.groupby(["solution", "dataset", "level", "task_id"]):
        per_task[f"{solution}|{dataset}|{task_id}"][level] = int(group["lenient"].sum())
    out.write_text(json.dumps({"summary": summary, "per_task": per_task,
                               "figures": dict(frame.groupby("task_id")["figure"].first())}, indent=1, ensure_ascii=False))
    frame.to_csv(out.with_suffix(".cases.csv"), index=False)
    print(f"{len(frame)} cases from {len(sys.argv) - 2} runs -> {out}")


if __name__ == "__main__":
    main()
