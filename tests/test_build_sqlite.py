"""Conversion rules of pipeline.build_sqlite on small fixtures shaped like the V-Dem snapshot and OWID catalog tables."""
import sqlite3
import zipfile

import pandas as pd
import pytest

from pipeline import build_sqlite
from pipeline.build_sqlite import build, split_columns


@pytest.fixture()
def dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(build_sqlite, "MIN_SECTION", 2)  # small fixture: two columns make a section
    src, catalog = tmp_path / "snapshots", tmp_path / "catalog" / "garden" / "regions"
    src.mkdir()
    catalog.mkdir(parents=True)
    frame = pd.DataFrame({"country_name": ["Sweden", "Sweden", "Baden"], "country_text_id": ["SWE", "SWE", "BAD"],
                          "country_id": [5, 5, 349], "year": [1900, 2025, 1790], "histname": ["", "", "Duchy"],
                          "v2x_polyarchy": [0.316, 0.889, None], "v2x_libdem": [0.2, 0.8, None],
                          "v2elfrfair_osp": [2.1, 3.9, None], "v2elmulpar_osp": [2.0, 3.8, None],
                          "e_wbgi_gee": [None, 1.2, None]})
    with zipfile.ZipFile(src / "vdem.zip", "w") as archive:
        archive.writestr(build_sqlite.CSV_NAME, frame.to_csv(index=False))
    pd.DataFrame({"code": ["SWE"], "name": ["Sweden"], "members": ['["SWE"]']}).to_feather(catalog / "regions.feather")
    return src, tmp_path / "catalog"


def test_split_keeps_identifiers_apart_and_repeats_keys(monkeypatch):
    monkeypatch.setattr(build_sqlite, "MIN_SECTION", 2)
    columns = ["country_name", "country_text_id", "country_id", "year", "histname",
               "v2x_polyarchy", "v2x_libdem", "v2elfrfair_osp", "e_wbgi_gee"]
    tables = split_columns(columns)
    assert tables["vdem__identifiers"] == columns[:5]
    assert tables["vdem__v2x"] == build_sqlite.KEYS + ["v2x_polyarchy", "v2x_libdem"]
    assert set(tables["vdem__misc"]) == set(build_sqlite.KEYS + ["v2elfrfair_osp", "e_wbgi_gee"])  # small sections
    indicators = [c for name, cols in tables.items() if name != "vdem__identifiers" for c in cols if c not in build_sqlite.KEYS]
    assert sorted(indicators) == sorted(columns[5:])  # every indicator in exactly one table


def test_conversion_rules(dirs, tmp_path):
    src, catalog = dirs
    db_path = tmp_path / "out.db"
    summary = build(src, catalog, db_path)
    db = sqlite3.connect(db_path)
    assert db.execute("SELECT v2x_polyarchy FROM vdem__v2x WHERE country_name='Sweden' AND year=2025").fetchone() == (0.889,)
    assert db.execute("SELECT v2x_polyarchy FROM vdem__v2x WHERE country_name='Baden'").fetchone() == (None,)
    assert db.execute("SELECT histname FROM vdem__identifiers WHERE year=1790").fetchone() == ("Duchy",)
    assert db.execute("SELECT members FROM owid_regions").fetchone() == ('["SWE"]',)
    assert {name: t["rows"] for name, t in summary["tables"].items() if name.startswith("vdem__")} == \
        {"vdem__identifiers": 3, "vdem__v2x": 3, "vdem__v2el": 3, "vdem__misc": 3}
    assert "vdem_documents" not in summary["tables"]  # no PDF in the fixture
