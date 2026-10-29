"""Map every attributed failure onto the categories used for the GCB benchmark, one primary cause per case.

    python -m scripts.categorise_failures <attribution.json> <out.json>

The attribution (task / agent / both, with reasons; scripts.aggregate_attribution) answers whether the input
determined the figure. The categories answer what was missing, so that the two benchmarks can be compared:

- underspecified: the input leaves the choice open and the agent's choice was reasonable (open_choice_ok, and the
  reviewed overrides that accept a scope);
- institutional: a convention of OWID's processing that neither input nor database reveals (hidden), e.g. the
  peak year as a third state, "the present" as 2025, OWID's Europe including Cyprus;
- valid_alternative: a standard method that differs from the published one, here the UN's median-age convention on
  the raw database (H-raw1: single age a counted as [a-1, a)); the textbook interpolation is equally defensible;
- conflict: the input contradicts the figure, or the figure needs what the data cannot give (figures 5 and 6);
- agent: the agent's own error (attribution "agent");
- evaluation: the values are right and the form is not recognised (an estimate/projection split at the peak).

A case attributed to the task or to both gets the primary category of its task-side reasons, in the order
conflict, institutional, valid_alternative, underspecified; "both" cases are also counted as having an agent error.
Reasons about the image label "Latin America" are dropped: the evaluator accepts that label since decision 0010.
"""
import collections
import json
import sys

ORDER = ["conflict", "institutional", "valid_alternative", "underspecified", "evaluation"]


MEDIAN_AGE = ("europe-is-older-but-latin-america-is-aging-faster__01",
              "the-median-age-in-china-has-rapidly-caught-up-with-the-unite__01")


def reason_category(reason: dict, case: dict) -> str | None:
    rule, dimension = reason["rule"], str(reason.get("dimension") or "")
    evidence = reason.get("evidence", "")
    median_age_raw = case["task_id"] in MEDIAN_AGE and case["dataset"].endswith("raw")
    if median_age_raw and (rule == "wrong_values" or "H-raw1" in evidence or "textbook" in evidence):
        return "valid_alternative"  # the UN's [a-1, a) convention vs the textbook interpolation (H-raw1)
    if rule == "conflict":
        return "conflict"
    if rule == "hidden":
        if dimension == "entity label":
            return None
        if "column split" in dimension:
            return "evaluation"
        return "institutional"
    if rule == "open_choice_ok":
        return "underspecified"
    return None


def categorise(case: dict) -> str:
    if case["attribution"] == "agent":
        return "agent"
    found = {c for r in case["reasons"] if (c := reason_category(r, case))}
    for category in ORDER:
        if category in found:
            return category
    # task-side only through a reviewed override (an accepted scope) or a dropped label reason
    return "underspecified" if case["attribution"] == "task" else "agent"


def main() -> None:
    cases = json.load(open(sys.argv[1]))["cases"]
    out = []
    for case in cases:
        out.append({k: case[k] for k in ("run", "dataset", "solution", "task_id", "level", "repeat", "attribution")}
                   | {"category": categorise(case), "also_agent_error": case["attribution"] == "both"})
    summary = collections.defaultdict(collections.Counter)
    for c in out:
        summary[c["solution"]][c["category"]] += 1
        summary[c["solution"]]["total"] += 1
        summary[c["solution"]]["both"] += c["also_agent_error"]
    json.dump({"summary": {k: dict(v) for k, v in summary.items()}, "cases": out}, open(sys.argv[2], "w"), indent=1)
    for solution, counts in summary.items():
        print(solution, dict(counts))


if __name__ == "__main__":
    main()
