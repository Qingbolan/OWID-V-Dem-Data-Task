"""Export a compact, reviewable record of benchmark runs (the full run directories stay local, outside git).

    python -m scripts.export_run_records <out_dir> <run_dir> [<run_dir> ...]

Writes <out_dir>/<run name>.jsonl with one line per case: the query the solution received (and the image path, if
any), every SQL call in order (statement, number of rows or the error), the final SQL (and the lenient one, if the
answer had prose around it), the answer text if it was not a bare query, timing and token use, the evaluation
(correct, cell accuracy, row coverage, failure) and the failure attribution, if one was made.
"""
import json
import sys
from pathlib import Path


def sql_calls(trajectory: Path) -> list[dict]:
    calls = []
    for line in trajectory.open(encoding="utf-8"):
        event = json.loads(line)
        if event.get("direction") == "query":
            message = event["message"]
            result = message.get("result", {})
            calls.append({"sql": (message.get("arguments") or {}).get("sql"),
                          "rows": len(result.get("rows", [])) if "rows" in result else None,
                          "error": result.get("error")})
    return calls


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for run in map(Path, sys.argv[2:]):
        attribution = {}
        if (run / "failure_attribution.json").exists():
            attribution = {(a["task_id"], a["level"], a["repeat"]): a
                           for a in json.loads((run / "failure_attribution.json").read_text())}
        lenient_path = run / "evaluation_result.lenient.json"
        final = json.loads((lenient_path if lenient_path.exists() else run / "evaluation_result.json").read_text())
        final = {(r["task_id"], r["level"], r["repeat"]): r for r in final}
        lines = []
        for case in sorted(run.glob("*/*/repeat-*")):
            meta = json.loads((case / "meta.json").read_text())
            key = (case.parent.parent.name, meta["level"], meta["repeat"])
            evaluation = final.get(key, {})
            read = lambda name: (case / name).read_text(encoding="utf-8") if (case / name).exists() else None  # noqa: E731
            answer = read("answer.txt") or ""
            record = {
                "task_id": key[0], "level": key[1], "repeat": key[2], "solution": meta["solution"],
                "model": meta.get("model"), "database": meta.get("database", "vdem2026.db"),
                "input": json.loads((case / "input.json").read_text()),
                "sql_calls": sql_calls(case / "trajectory.jsonl"),
                "final_sql": read("final.sql"), "final_sql_lenient": read("final.lenient.sql"),
                "answer_text": None if (read("final.sql") or "").strip() == answer.strip() else answer,
                "state": meta["state"], "error": meta.get("error"), "seconds": meta["elapsed_seconds"],
                "tool_calls": meta.get("tool_calls"), "token_usage": meta.get("token_usage"),
                "evaluation": {k: evaluation.get(k) for k in ("correct", "cell_accuracy", "row_coverage", "failure",
                                                              "entities_outside_figure", "answer_recovered")},
                "attribution": attribution.get(key),
            }
            lines.append(json.dumps(record, ensure_ascii=False, default=str))
        (out / f"{run.name}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{run.name}: {len(lines)} cases")


if __name__ == "__main__":
    main()
