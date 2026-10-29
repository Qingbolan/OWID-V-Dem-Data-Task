"""Add what the golden specs need to every figure with data in OWID/: the chart's config, its indicator metadata and
the figure columns' short names.

    python -m scripts.add_figure_sources <OWID root> [--cache data/cache/grapher]

For each figure of each folder's meta.json that has a view (an embedded chart, or a static image whose chart was
identified), writes figs/<figure>/chart.config.json and chart.metadata.json, and records in meta.json the chart's
slug ("chart_slug") and, per figure CSV column, OWID's indicator short name ("column_short_names", from the same view
downloaded with short column names). Figures already done are skipped.
"""
import argparse
import csv
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

from scripts.build_owid_article import GRAPHER
from scripts.owid_pages import get


def cached(url: str, path: Path) -> str:
    if not path.exists():
        path.write_text(get(url).text, encoding="utf-8")
    return path.read_text(encoding="utf-8")


def view_of(record: dict) -> tuple[str, dict]:
    view = urlparse(record["view_url"])
    return view.path.rstrip("/").split("/")[-1], dict(parse_qsl(view.query))


def add(folder: Path, cache: Path) -> int:
    meta_path = folder / "meta.json"
    meta = json.loads(meta_path.read_text())
    added = 0
    for record in meta["figures"]:
        if not record.get("view_url") or "column_short_names" in record:
            continue
        slug, query = view_of(record)
        target = folder / "figs" / record["name"]
        target.mkdir(parents=True, exist_ok=True)
        for kind in ("config", "metadata"):
            text = cached(f"{GRAPHER}/{slug}.{kind}.json", cache / f"{slug}.{kind}.json")
            (target / f"chart.{kind}.json").write_text(json.dumps(json.loads(text), ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
        url = f"{GRAPHER}/{slug}.csv?" + urlencode({"csvType": "filtered", "useColumnShortNames": "true", **query})
        short = next(csv.reader([get(url).text.splitlines()[0]]))
        published = next(csv.reader([(folder / record["files"]["csv"]["path"]).read_text(encoding="utf-8").splitlines()[0]]))
        if len(short) != len(published):  # a scoped figure keeps every column of the view
            raise ValueError(f"{folder.name} / {record['name']}: {len(published)} columns but {len(short)} short names")
        record.update(chart_slug=slug, column_short_names=dict(zip(published, short)))
        added += 1
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return added


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/grapher"))
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    total = 0
    for meta in sorted(args.root.glob("*/meta.json")):
        n = add(meta.parent, args.cache)
        total += n
        print(f"{meta.parent.name}: {n} figures", flush=True)
    print(f"done: {total} figures")


if __name__ == "__main__":
    main()
