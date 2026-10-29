"""Every golden processing program is complete and well-formed."""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPECS = sorted(ROOT.glob("OWID/*/figs/*/golden-processing-program-files/spec.json"))


@pytest.mark.parametrize("spec_path", SPECS, ids=lambda p: p.parent.parent.name)
def test_spec(spec_path):
    spec, folder = json.loads(spec_path.read_text()), spec_path.parent
    assert (folder / "README.md").exists()
    if not spec["reproducible"]:
        assert spec["reason"]
        return
    figure_csv = folder.parent.parent / f"{folder.parent.name}.csv"
    header = list(pd.read_csv(figure_csv, nrows=0).columns)
    assert spec["reproducible"] is True and spec["program"] == "golden.vdem_pipeline"
    assert set(spec["solution_columns"]) <= set(spec["columns"]) == set(spec["gold_column_index"]) == set(spec["compare"])
    assert all(header[index] == column for column, index in spec["gold_column_index"].items())
    assert (ROOT / spec["entity_mapping"]).exists()
    for column in spec["columns"]:
        source = spec["sources"][column]
        assert "original_year_of" in source or {"table", "column", "filter"} <= set(source)
