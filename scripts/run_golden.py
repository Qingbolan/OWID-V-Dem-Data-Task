"""Check every chart's golden program against OWID's published figure data.

    python -m scripts.run_golden <OWID root or chart folder> [--tables data/golden/vdem]

The shared part of the programs, OWID's V-Dem step run on the benchmark database, writes its output tables to
--tables (`make golden-pipeline`). For every figs/<figure>/golden-processing-program-files/spec.json:
  1. build the figure's columns from those tables (spec "sources": table, column, dimension filter) for the
     figure's (Entity, Year) keys, as the chart's view shows them (spec "scale", "stack_relative",
     "time_tolerance"; see scripts/write_golden_specs.py); a key with no value in any column is missing;
  2. compare with figs/<figure>.csv on the figure's (Entity, Year) keys, cell by cell, with the spec tolerances
     (numeric: absolute difference; text: equality); a missing key is a mismatch, a value the figure leaves empty
     must be empty in the rebuilt data too;
  3. write expected_output.csv (the rebuilt rows of the figure's keys) and verification.json next to the spec.
Figures whose spec declares "reproducible": false are reported and skipped. Exit status is non-zero if any figure
that is checked does not match.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "golden-processing-program-files"


def series(source: dict, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One indicator from OWID's output tables: Entity, Year, value (dimension filter applied)."""
    frame = tables[source["table"]]
    for dimension, value in source["filter"].items():
        frame = frame[frame[dimension] == value]
    part = frame[["country", "year", source["column"]]].rename(
        columns={"country": "Entity", "year": "Year", source["column"]: "value"}).dropna(subset=["value"])
    if part.duplicated(["Entity", "Year"]).any():
        raise ValueError(f"several rows per (Entity, Year) in {source}")
    return part


def closest_within(part: pd.DataFrame, keys: pd.DataFrame, tolerance: int) -> pd.DataFrame:
    """For each (Entity, Year) key, the value of the closest year within `tolerance` (the earlier on a tie), and that
    year; as a map with a time tolerance shows it."""
    candidates = keys.merge(part.rename(columns={"Year": "source_year"}), on="Entity")
    candidates["distance"] = (candidates["source_year"] - candidates["Year"]).abs()
    candidates = candidates[candidates["distance"] <= tolerance]
    best = candidates.sort_values(["distance", "source_year"]).drop_duplicates(["Entity", "Year"])
    return best[["Entity", "Year", "value", "source_year"]]


def rebuild(spec: dict, tables: dict[str, pd.DataFrame], keys: pd.DataFrame) -> pd.DataFrame:
    """The figure's columns for the figure's (Entity, Year) keys, as the chart's view shows them (spec "scale",
    "stack_relative", "time_tolerance")."""
    result, source_years = keys.copy(), {}
    for column, source in spec["sources"].items():
        if "original_year_of" in source:
            continue
        part = series(source, tables)
        if spec.get("time_tolerance"):
            part = closest_within(part, keys, spec["time_tolerance"])
            source_years[column] = part[["Entity", "Year", "source_year"]]
        part = part[["Entity", "Year", "value"]].rename(columns={"value": column})
        if column in spec.get("scale", {}):
            part[column] = pd.to_numeric(part[column]) * spec["scale"][column]
        result = result.merge(part, on=["Entity", "Year"], how="left")
    if spec.get("stack_relative"):
        values = [c for c in spec["columns"] if "original_year_of" not in spec["sources"][c]]
        total = result[values].apply(pd.to_numeric).sum(axis=1)
        for column in values:
            result[column] = 100 * pd.to_numeric(result[column]) / total.where(total != 0)
    for column, source in spec["sources"].items():
        if "original_year_of" in source:
            years = source_years[source["original_year_of"]]
            merged = result[["Entity", "Year"]].merge(years, on=["Entity", "Year"], how="left")
            result[column] = merged["source_year"].where(merged["source_year"] != merged["Year"]).values
    return result


def same(gold, rebuilt, rule: dict) -> bool:
    if pd.isna(gold) or gold == "":
        return pd.isna(rebuilt) or rebuilt == ""
    if pd.isna(rebuilt) or rebuilt == "":
        return False
    try:  # numbers, including numbers in a text column ("42" and 42.0)
        gold_number, rebuilt_number = float(gold), float(rebuilt)
    except (TypeError, ValueError):
        return str(gold) == str(rebuilt)
    if rule.get("equal"):
        return gold_number == rebuilt_number
    allowed = rule.get("abs", 0.0) * 1.0001 + rule.get("rel", 0.0) * abs(gold_number)
    return abs(rebuilt_number - gold_number) <= allowed


def run_one(spec_path: Path, tables: dict[str, pd.DataFrame]) -> dict:
    spec = json.loads(spec_path.read_text())
    folder = spec_path.parent
    figure_csv = folder.parent.parent / f"{folder.parent.name}.csv"
    record = {"figure": folder.parent.name, "checked_at": datetime.now(timezone.utc).isoformat()}
    if not spec.get("reproducible", True):
        record.update(status="not_reproducible", reason=spec.get("reason"))
        (folder / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=1))
        return record
    gold = pd.read_csv(figure_csv, dtype=str, keep_default_na=False, na_values=[""])
    gold["Year"] = gold["Year"].astype(int)
    result = rebuild(spec, tables, gold[["Entity", "Year"]].drop_duplicates())
    present = result[[c for c in spec["columns"]]].notna().any(axis=1)
    merged = gold[["Entity", "Year", *spec["columns"]]].merge(result[present],
                                                               on=["Entity", "Year"], how="left",
                                                               suffixes=("_gold", "_ref"), indicator=True)
    missing = int((merged["_merge"] == "left_only").sum())
    expected = merged[["Entity", "Year"]].copy()
    mismatches, counts = [], {}
    for column in spec["columns"]:
        rule = spec["compare"][column]
        ok = [same(g, r, rule) for g, r in zip(merged[f"{column}_gold"], merged[f"{column}_ref"])]
        bad = merged[[not x for x in ok]]
        counts[column] = len(bad)
        expected[column] = merged[f"{column}_ref"]
        for _, row in bad.head(10).iterrows():
            mismatches.append({"entity": row["Entity"], "year": int(row["Year"]), "column": column,
                               "gold": row[f"{column}_gold"], "reference": None if pd.isna(row[f"{column}_ref"]) else row[f"{column}_ref"]})
    expected.to_csv(folder / "expected_output.csv", index=False)
    ok = missing == 0 and sum(counts.values()) == 0
    record.update(status="match" if ok else "mismatch", gold_rows=len(gold), gold_rows_missing_in_reference=missing,
                  mismatched_cells=counts, tolerance=spec["compare"], first_mismatches=mismatches,
                  program=spec["program"])
    (folder / "verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=1, default=str))
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--tables", type=Path, default=ROOT / "data/golden/vdem")
    args = parser.parse_args()
    tables = {p.stem: pd.read_feather(p) for p in sorted(args.tables.glob("*.feather"))}
    specs = sorted(args.root.rglob(f"{FOLDER}/spec.json"))
    status = {}
    for spec in specs:
        record = run_one(spec, tables)
        status[record["status"]] = status.get(record["status"], 0) + 1
        detail = record.get("mismatched_cells") or record.get("reason", "")
        if record.get("gold_rows_missing_in_reference"):
            detail = f"{detail}; {record['gold_rows_missing_in_reference']} figure rows missing"
        print(f"{record['status']:16s} {record['figure']}  {detail}", flush=True)
    print(f"{len(specs)} figures: " + ", ".join(f"{v} {k}" for k, v in sorted(status.items())))
    sys.exit(1 if status.get("mismatch") else 0)


if __name__ == "__main__":
    main()
