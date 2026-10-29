"""Run OWID's V-Dem processing on the benchmark database and save its output tables.

    .venv-golden/bin/python -m golden.vdem_pipeline [--db data/sqlite/vdem2026.db] [--out data/golden/vdem]

This is the shared part of every chart's golden program (docs/decisions/0004-golden-processing-programs.md). OWID's
own code for the V-Dem dataset (data/reference/owid_etl/vdem/, copied from owid/etl at the commit in PROVENANCE.json)
is run unchanged; only its inputs are redirected:
- the meadow table is rebuilt from the database: the columns OWID's meadow step keeps (its COLUMNS_KEEP), joined
  from the per-section tables on (country_id, year), with country_name renamed to country, as the meadow step does;
- OWID's region and population datasets are read from the database tables owid_regions and owid_population;
- `etl.helpers.PathFinder` and `etl.paths` are replaced by the small stand-ins below; `etl.data_helpers.geo` is
  OWID's file, copied unchanged to golden/vendor/geo.py.
The garden step's output tables are written as feather files to --out, one per table, with their keys as columns,
after OWID's grapher step (grapher.py), whose only change to values labels two year counters by regime category.

Requires the `golden` environment (OWID's owid-catalog, owid-datautils and owid-repack libraries from an owid/etl
clone): `make golden-env ETL=/path/to/etl`.
"""
import argparse
import importlib.util
import json
import sqlite3
import sys
import types
from pathlib import Path

import pandas as pd
import structlog
import yaml
from owid.catalog import Dataset, DatasetMeta, Origin, Table

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data/reference/owid_etl/vdem"
DVC = ROOT / "data/raw/owid-snapshots/democracy/2026-03-17/vdem.zip.dvc"
KEYS = ["country_id", "year"]


class _Datasets:
    """What the V-Dem step reads: the meadow table and OWID's region and population datasets, from the database."""

    def __init__(self, db_path: Path, workdir: Path):
        self.db_path, self.workdir = db_path, workdir

    def _query(self, sql: str) -> pd.DataFrame:
        db = sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            return pd.read_sql_query(sql, db)
        finally:
            db.close()

    def meadow(self) -> Dataset:
        # COLUMNS_KEEP names some columns twice; the meadow step reads it as read_csv(usecols=...), which keeps one.
        keep = list(dict.fromkeys(_load_module("vdem_meadow", REFERENCE / "meadow.py").COLUMNS_KEEP))
        frame = None
        db = sqlite3.connect(self.db_path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'vdem\\_\\_%' ESCAPE '\\'")]
            for table in tables:
                columns = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]
                wanted = [c for c in keep if c in columns and c not in ("country_name", "year")]
                if table == "vdem__identifiers":
                    wanted = ["country_name"] + [c for c in wanted if c != "country_name"]
                if not wanted:
                    continue
                quoted = ", ".join(f'"{c}"' for c in KEYS + wanted)
                part = pd.read_sql_query(f'SELECT {quoted} FROM "{table}"', db)
                frame = part if frame is None else frame.merge(part, on=KEYS, how="outer", validate="one_to_one")
        finally:
            db.close()
        missing = sorted(set(keep) - set(frame.columns))
        if missing:
            raise ValueError(f"meadow columns not in the database: {missing}")
        frame = frame[keep].astype({"v2exnamhog": "string"})
        tb = Table(frame).rename(columns={"country_name": "country"})
        # A snapshot gives every column the origin recorded in its .dvc file; the step reads it back (from `country`).
        origin = Origin.from_dict(yaml.safe_load(DVC.read_text())["meta"]["origin"])
        for column in tb.columns:
            tb[column].metadata.origins = [origin]
        tb = tb.format(["country", "year"], short_name="vdem")
        return self._dataset("vdem", [tb])

    def regions(self) -> Dataset:
        tb = Table(self._query("SELECT * FROM owid_regions")).format(["code"], short_name="regions")
        return self._dataset("regions", [tb])

    def population(self) -> Dataset:
        tb = Table(self._query("SELECT * FROM owid_population")).format(["country", "year"], short_name="population")
        return self._dataset("population", [tb])

    def _dataset(self, name: str, tables: list[Table]) -> Dataset:
        ds = Dataset.create_empty(self.workdir / name, DatasetMeta(short_name=name))
        for tb in tables:
            ds.add(tb)
        return ds


class _PathFinder:
    """Stand-in for etl.helpers.PathFinder with the members the V-Dem step uses."""

    datasets: _Datasets
    created: list[Table] = []

    def __init__(self, file: str):
        self.directory = REFERENCE
        self.country_mapping_path = REFERENCE / "vdem.countries.json"
        self.log = structlog.get_logger("vdem")

    def load_dataset(self, name: str) -> Dataset:
        return {"vdem": self.datasets.meadow, "regions": self.datasets.regions,
                "population": self.datasets.population}[name]()

    def create_dataset(self, tables, **kwargs):
        _PathFinder.created = list(tables)
        return types.SimpleNamespace(save=lambda: None)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_stand_ins() -> None:
    etl = types.ModuleType("etl")
    etl.__path__ = []
    paths = types.ModuleType("etl.paths")
    for constant in ("DATA_DIR", "LATEST_INCOME_DATASET_PATH", "LATEST_POPULATION_DATASET_PATH",
                     "LATEST_REGIONS_DATASET_PATH"):
        setattr(paths, constant, ROOT / "data/golden/unused")
    helpers = types.ModuleType("etl.helpers")
    helpers.PathFinder = _PathFinder
    data_helpers = types.ModuleType("etl.data_helpers")
    data_helpers.__path__ = []
    sys.modules.update({"etl": etl, "etl.paths": paths, "etl.helpers": helpers, "etl.data_helpers": data_helpers})
    geo = _load_module("etl.data_helpers.geo", ROOT / "golden/vendor/geo.py")
    data_helpers.geo = geo
    sys.path.insert(0, str(REFERENCE))  # the step imports its sibling modules (vdem_clean, ...) by name


def run(db_path: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    _install_stand_ins()
    _PathFinder.datasets = _Datasets(db_path, out / "_datasets")
    step = _load_module("vdem_garden", REFERENCE / "__init__.py")
    step.run()
    grapher = _load_module("vdem_grapher", REFERENCE / "grapher.py")
    summary = {}
    for tb in _PathFinder.created:
        name = tb.metadata.short_name
        if name == "vdem_uni_without_regions":  # the grapher step's only change to values
            tb = grapher.add_categories_to_counters(tb)
        frame = pd.DataFrame(tb.reset_index())
        frame.to_feather(out / f"{name}.feather")
        summary[name] = {"rows": len(frame), "columns": list(frame.columns)}
        print(f"{name}: {len(frame):,} rows, {frame.shape[1]} cols", flush=True)
    (out / "tables.json").write_text(json.dumps(summary, indent=1))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=ROOT / "data/sqlite/vdem2026.db")
    parser.add_argument("--out", type=Path, default=ROOT / "data/golden/vdem")
    args = parser.parse_args()
    run(args.db, args.out)


if __name__ == "__main__":
    main()
