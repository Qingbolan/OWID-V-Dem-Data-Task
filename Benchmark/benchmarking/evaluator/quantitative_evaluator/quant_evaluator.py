"""Quantitative evaluator: executed result vs. the figure's published data (docs/task-definition.md)."""
import json
import math
import re
from pathlib import Path

import pandas as pd

from ...utils.path import REPO_ROOT
from ...utils.struct import Task
from ..base_evaluator import BaseEvaluator
from .quant_metrics import compare


def load_gold(task: Task, spec: dict) -> pd.DataFrame:
    """Gold columns selected positionally (OWID CSVs may repeat a header for an indicator's label and code)."""
    raw = pd.read_csv(task.gold_csv, header=None, skiprows=1)
    header = list(pd.read_csv(task.gold_csv, nrows=0).columns)
    selected = [header.index("Entity"), header.index("Year"), *[spec["gold_column_index"][c] for c in task.output_columns]]
    gold = raw.iloc[:, selected].copy()
    gold.columns = ["Entity", "Year", *task.output_columns]
    return gold


EVALUATION_ALIASES = REPO_ROOT / "data/reference/evaluation_aliases.json"


def entity_mapping(spec: dict) -> dict[str, str]:
    """OWID's UN-to-OWID name mapping, plus names a figure prints for an entity (data/reference/evaluation_aliases.json)."""
    mapping = json.loads((REPO_ROOT / spec["entity_mapping"]).read_text())
    for alias, name in json.loads(EVALUATION_ALIASES.read_text()).items():
        mapping[alias] = mapping.get(name, name)
    return mapping


DEFAULT_RELATIVE = 0.01  # docs/task-definition.md: numeric cells match within 1 % relative unless the spec says more


def solution_tolerance(spec: dict, column: str, variant: str | None = None) -> dict:
    """Tolerance for a solution's cell. `compare` is the golden program's check, which is far stricter (exact
    reproduction of OWID's ETL); solutions are held to the task definition: at least 1 % relative, any absolute
    tolerance of the golden check, and exact codes for categorical columns. `evaluation` refines it per column
    (e.g. a figure that shows only classes, see the figure README)."""
    golden = spec["compare"].get(column, {})
    if variant and variant in spec:  # the variant's golden program may only approximate the published values
        golden = spec[variant]["compare"].get(column, golden)
    if column in spec.get("encodings", {}):
        tolerance = dict(golden)
    else:
        tolerance = {"abs": golden.get("abs", 0.0), "rel": max(golden.get("rel", 0.0), DEFAULT_RELATIVE)}
    return tolerance | spec.get("evaluation", {}).get(column, {})


HARDCODED_MIN_CELLS = 3
LITERAL = re.compile(r"(?<![\w.'])-?\d+(?:\.\d+)?(?![\w.'])")


def hardcoded_cells(sql: str, gold: pd.DataFrame, columns: list[str], alignment: dict) -> int:
    """Gold cells whose value is written into the SQL as a number literal (at the column's matched scale), rather
    than read or computed from the database: values copied from the figure image or the article. Years
    (1900-2100), small integers and powers of ten are ignored; a literal must equal the cell to 1e-4 relative."""
    text = re.sub(r"'(?:[^']|'')*'", "''", sql)  # string literals are not values
    literals = []
    for match in LITERAL.findall(text):
        value = float(match)
        if value.is_integer() and (abs(value) <= 10 or 1900 <= value <= 2100 or math.log10(abs(value)).is_integer()):
            continue
        literals.append(value)
    if not literals:
        return 0
    hits = set()
    for column in columns:
        match = (alignment.get("columns", {}).get(column) or {}).get("match")
        scale = match.get("scale", 1.0) if isinstance(match, dict) else 1.0
        for index, expected in pd.to_numeric(gold[column], errors="coerce").dropna().items():  # text cells are labels
            if any(abs(lit * scale - expected) <= 1e-4 * abs(expected) for lit in literals):
                hits.add((index, column))
    return len(hits)


class QuantEvaluator(BaseEvaluator):
    name = "quantitative"

    def evaluate(self, task: Task, case_dir: Path) -> dict:
        spec = json.loads(task.spec_path.read_text())
        mapping = entity_mapping(spec)
        gold = load_gold(task, spec)
        meta = json.loads((case_dir / "meta.json").read_text())
        base = {"task_id": task.task_id, "evaluator": self.name, "state": meta["state"]}
        output_path = case_dir / "output.csv"
        if meta["state"] != "completed" or not output_path.exists():
            return base | {"correct": False, "failure": "execution_failure", "error": meta.get("error")}
        output = pd.read_csv(output_path)
        if output.empty:
            return base | {"correct": False, "failure": "empty_result"}
        tolerances = {c: solution_tolerance(spec, c, task.variant) for c in task.output_columns}
        categorical = frozenset(spec.get("encodings", {}))
        result = base | compare(gold, output, task.output_columns, tolerances, mapping, categorical)
        sql = (case_dir / "final.sql").read_text() if (case_dir / "final.sql").exists() else ""
        literal_cells = hardcoded_cells(sql, gold, task.output_columns, result.get("alignment", {}))
        result["literal_value_cells"] = literal_cells
        if literal_cells >= HARDCODED_MIN_CELLS:
            result |= {"correct": False, "failure": "hardcoded_values"}
        return result
