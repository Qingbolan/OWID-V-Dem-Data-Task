"""Combine the failure attributions of several runs, applying the reviewed rules of docs/task-requirements.md.

    python -m scripts.aggregate_attribution <out.json> <run_dir>:<dataset> [...]

Each run directory holds failure_attribution.json (one entry per failed case: attribution agent / task / both, with
reasons), written by a reviewer against docs/task-requirements.md. Some attributions were written before the
document's later revisions, and some cases were re-scored afterwards (the lenient reading's SQL extraction was
fixed; the raw-database fertility tolerance was widened). This script makes them consistent:

- cases that are now correct (in the run's final lenient or strict results) are dropped;
- conflict items (✗): figure 5 (natural growth 2060) at subtitle, article and image-article; figure 6 (US
  simulation) at every level. The conflicting dimension (scenario, simulation method) is the task's; a case with
  other agent-side findings (e.g. leaving out a panel the image shows) is "both". How the agent handled the conflict
  is kept;
- figure 10 (deaths outnumber births): at text levels, a list of the countries where deaths exceed births is an
  acceptable form, so an entity-scope finding on that alone is the task's;
- figure 16 (population change in Europe): at title and subtitle an aggregate for Europe is acceptable;
- raw database, figures 7 and 14 (median age): the UN's [a-1, a) convention is hidden at title, subtitle and image,
  and printed values reveal it in the article: task at title/subtitle/image, both at article/image-article, when
  the median-age convention is the only agent-side finding.
Every changed attribution records the rule that changed it ("override").
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

CONFLICT = {("__05", "subtitle"), ("__05", "article"), ("__05", "image-article"),
            *(("__06", level) for level in ("title", "subtitle", "article", "image", "image-article"))}
FIG10 = "where-are-more-people-dying-than-being-born__01"
FIG16 = "some-parts-of-europe-have-a-growing-population-while-others-__01"
MEDIAN = ("europe-is-older-but-latin-america-is-aging-faster__01", "the-median-age-in-china-has-rapidly-caught-up-with-the-unite__01")


def figure_key(task_id: str) -> str:
    return "__" + task_id.rsplit("__", 1)[1] if task_id.startswith("which-countries-have-already-passed") else task_id


def agent_reasons(entry: dict) -> list[dict]:
    return [r for r in entry.get("reasons", []) if r.get("rule") not in ("open_choice_ok", "hidden", "conflict")]


def override(entry: dict, dataset: str) -> dict:
    task, level = entry["task_id"], entry["level"]
    reasons = agent_reasons(entry)
    if (figure_key(task), level) in CONFLICT:
        # Only the conflicting dimension (scenario / simulation method) is the task's; other agent-side findings
        # (e.g. a panel visible in the image left out, a wrong country set) still count.
        other = [r for r in reasons if not any(w in (r.get("dimension", "") + " " + r.get("evidence", "")).lower()
                                               for w in ("scenario", "method", "model", "simulation", "variant",
                                                         "migration projection", "zero-migration", "zero migration"))]
        return entry | {"attribution": "both" if other else "task",
                        "override": "conflict item (✗): conflicting dimension is the task's"}
    if task == FIG10 and level in ("title", "subtitle", "article") and reasons and all(
            r.get("dimension", "").startswith("entit") for r in reasons):
        return entry | {"attribution": "task", "override": "figure 10: a list of qualifying countries is acceptable"}
    if task == FIG16 and level in ("title", "subtitle") and reasons and all(
            "aggregate" in r.get("evidence", "").lower() or "europe" in r.get("evidence", "").lower()
            for r in reasons if r.get("dimension", "").startswith("entit")) and all(
            r.get("dimension", "").startswith("entit") for r in reasons):
        return entry | {"attribution": "task", "override": "figure 16: an aggregate for Europe is acceptable at T/S"}
    if dataset.endswith("_raw") and task in MEDIAN and reasons and all(
            "median" in (r.get("evidence", "") + str(entry.get("computation", ""))).lower() or
            "one year" in r.get("evidence", "").lower() for r in reasons):
        attribution = "task" if level in ("title", "subtitle", "image") else "both"
        return entry | {"attribution": attribution, "override": "H-raw1: UN median-age convention"}
    return entry


def main() -> None:
    out = Path(sys.argv[1])
    rows, summary = [], {}
    for spec in sys.argv[2:]:
        run, dataset = spec.rsplit(":", 1)
        run = Path(run)
        final_path = run / ("evaluation_result.lenient.json" if (run / "evaluation_result.lenient.json").exists()
                            else "evaluation_result.json")
        final = {(r["task_id"], r["level"], r["repeat"]): r for r in json.loads(final_path.read_text())}
        attributed = json.loads((run / "failure_attribution.json").read_text())
        kept = []
        for entry in attributed:
            key = (entry["task_id"], entry["level"], entry["repeat"])
            if final.get(key, {}).get("correct"):
                continue
            kept.append(override(entry, dataset))
        missing = [k for k, r in final.items() if not r["correct"] and k not in
                   {(e["task_id"], e["level"], e["repeat"]) for e in attributed}]
        solution = json.loads(next(run.glob("*/*/repeat-*/meta.json")).read_text())["solution"]
        counts = defaultdict(Counter)
        reasons = Counter()
        handling = Counter()
        for entry in kept:
            counts[entry["level"]][entry["attribution"]] += 1
            if entry["attribution"] in ("agent", "both"):
                for r in agent_reasons(entry):
                    reasons[f"{r.get('rule')}: {r.get('dimension')}"] += 1
            if entry.get("conflict_handling"):
                handling[entry["conflict_handling"]] += 1
            rows.append(entry | {"run": run.name, "dataset": dataset, "solution": solution})
        summary[run.name] = {"solution": solution, "dataset": dataset, "failures": len(kept),
                             "unattributed_failures": [list(k) for k in missing],
                             "by_level": {level: dict(c) for level, c in counts.items()},
                             "overrides": dict(Counter(e.get("override") for e in kept if e.get("override"))),
                             "agent_reasons": dict(reasons.most_common(12)),
                             "conflict_handling": dict(handling)}
    out.write_text(json.dumps({"summary": summary, "cases": rows}, indent=1, ensure_ascii=False))
    for name, s in summary.items():
        print(name[16:], s["failures"], "failures;", {k: dict(v) for k, v in s["by_level"].items()},
              "| overrides", s["overrides"], "| unattributed", len(s["unattributed_failures"]))


if __name__ == "__main__":
    main()
