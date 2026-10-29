"""Materialise the charts that no article shows as a figure: one folder per chart, OWID/<chart slug>-[chart]/, whose
source page is the chart's own page on ourworldindata.org.

    python -m scripts.build_chart_pages <charts.json> <OWID root> [--figures data/cache/OWID-by-chart]

A chart is materialised here when it is one of the V-Dem charts (charts.json) and no folder in <OWID root> already
has a figure showing it (an article figure or an identified data-insight image), so run scripts.build_owid_article
for the articles first. The folder has the layout of an article folder:
  source.original.html, source.html, source_files/   the chart page as retrieved, and its offline snapshot
  meta.json                                           as for articles, with "chart_page": true
  figs/01 <title>.{csv,png,txt}                       the chart's default view (no page gives another view)
There is no article.md: the chart page has no report text, so the task has title and subtitle levels only.
The figure files are taken from --figures when present (a previous capture), otherwise downloaded.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from scripts.build_owid_article import GRAPHER
from scripts.owid_pages import get, safe_name
from scripts.snapshot_page import snapshot


def shown_in_articles(root: Path) -> set[str]:
    shown = set()
    for meta in root.glob("*/meta.json"):
        for record in json.loads(meta.read_text())["figures"]:
            slug = (record.get("embed") or {}).get("slug") or (record.get("view_url") or "").split("/")[-1].split("?")[0]
            if slug:
                shown.add(slug)
    return shown


def figure_files(slug: str, figs: Path, previous: Path) -> tuple[str, dict]:
    """The default view's figure files, copied from a previous capture or downloaded."""
    old = previous / slug
    if (old / "meta.json").exists():
        record = json.loads((old / "meta.json").read_text())["figures"][0]
        name = record["name"]
        for suffix in (".csv", ".png", ".txt"):
            shutil.copy(old / "figs" / f"{name}{suffix}", figs / f"{name}{suffix}")
        return name, record
    config = get(f"{GRAPHER}/{slug}.config.json").json()
    name = f"01 {safe_name(config.get('title') or slug)}"
    (figs / f"{name}.csv").write_bytes(get(f"{GRAPHER}/{slug}.csv?csvType=filtered").content)
    (figs / f"{name}.png").write_bytes(get(f"{GRAPHER}/{slug}.png").content)
    lines = [f"Figure 01: {name}", f"Title: {config.get('title', '')}", f"Subtitle: {config.get('subtitle', '')}",
             f"Note: {config.get('note', '')}", f"Chart: {GRAPHER}/{slug}"]
    (figs / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return name, {"config_title": config.get("title"), "config_subtitle": config.get("subtitle")}


def build_one(slug: str, root: Path, previous: Path) -> Path:
    folder = root / f"{slug}-[chart]"
    if (folder / "meta.json").exists():
        return folder
    figs = folder / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    url = f"{GRAPHER}/{slug}"
    html = get(url).text
    (folder / "source.original.html").write_text(html, encoding="utf-8")
    page = snapshot(folder / "source.original.html", url, folder / "source.html", folder / "source_files")
    name, old = figure_files(slug, figs, previous)
    text = (figs / f"{name}.txt").read_text(encoding="utf-8").replace(
        "Article: none (no page shows this chart)", f"Article: none; source page is the chart page {url}")
    (figs / f"{name}.txt").write_text(text, encoding="utf-8")
    files = {kind: f"figs/{name}.{kind}" for kind in ("txt", "csv", "png")}
    record = {"index": 1, "name": name, "embed": {"slug": slug, "query": {}, "image": None}, "view_url": url,
              "csv_url": f"{url}.csv?csvType=filtered", "png_url": f"{url}.png", "data_available": True,
              "config_title": old.get("config_title"), "config_subtitle": old.get("config_subtitle"),
              "files": {k: {"path": p, "sha256": hashlib.sha256((folder / p).read_bytes()).hexdigest()}
                        for k, p in files.items()}}
    meta = {"title": old.get("config_title") or slug, "url": url, "date_published": None, "chart_page": True,
            "authors": [], "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "materialised_at": datetime.now(timezone.utc).isoformat(),
            "source_original_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "offline_snapshot": {"page": "source.html", "assets": "source_files/",
                                 "assets_manifest": "source_files/manifest.json", "asset_count": len(page["assets"]),
                                 "removed": page["removed"]},
            "figures": [record]}
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("charts", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("--figures", type=Path, default=Path("data/cache/OWID-by-chart"))
    args = parser.parse_args()
    charts = [c["slug"] for c in json.loads(args.charts.read_text())["charts"]]
    shown = shown_in_articles(args.root)
    todo = [slug for slug in charts if slug not in shown]
    print(f"{len(charts)} charts: {len(charts) - len(todo)} shown in articles, {len(todo)} get a chart page", flush=True)
    for slug in todo:
        print(build_one(slug, args.root, args.figures).name, flush=True)


if __name__ == "__main__":
    main()
