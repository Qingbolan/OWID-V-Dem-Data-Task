"""Aggregate evaluation results of a run into report.json and report.md."""
import json
from collections import defaultdict
from pathlib import Path


def summarise(results: list[dict]) -> dict:
    groups: dict[tuple, list[bool]] = defaultdict(list)
    for r in results:
        groups[(r["solution"], r["level"], r["category"])].append(bool(r.get("correct")))
        groups[(r["solution"], r["level"], "all")].append(bool(r.get("correct")))
    return {"cases": len(results), "correct": sum(bool(r.get("correct")) for r in results),
            "by_solution_level_category": [{"solution": solution, "level": level, "category": category,
                                            "correct": sum(flags), "cases": len(flags)}
                                           for (solution, level, category), flags in sorted(groups.items())]}


def write_report(run_dir: Path, results: list[dict]) -> dict:
    summary = summarise(results)
    (run_dir / "evaluation_result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1, default=str))
    (run_dir / "report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    lines = [f"# Run {run_dir.name}", "", f"{summary['correct']} of {summary['cases']} cases correct.", "",
             "| Solution | Level | Category | Correct |", "|---|---|---|---:|"]
    lines += [f"| {g['solution']} | {g['level']} | {g['category']} | {g['correct']}/{g['cases']} |"
              for g in summary["by_solution_level_category"]]
    (run_dir / "report.md").write_text("\n".join(lines) + "\n")
    return summary
