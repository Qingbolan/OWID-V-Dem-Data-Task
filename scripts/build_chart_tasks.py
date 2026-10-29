"""Materialise one task folder per selected V-Dem chart: OWID/<chart slug>/.

    python -m scripts.build_chart_tasks <charts.json> <crawl.json> <out_root> [--pages data/cache/pages]

The unit is one OWID chart (data/reference/charts.json, written by scripts.select_charts). For each chart:

Host page. Of the pages the crawl lists for the chart, only those that show it as a figure in their prose count; a
topic page's "all charts" grid only links to a chart. Among those: the fewest figures, then the most recent. The
host page fixes the view (the embed's query string, e.g. tab=chart or a country selection) and the article-level
text. A chart no page shows as a figure is taken in its default view and has no article-level text.

Files, in the layout of the WPP benchmark (one figure per folder):
  meta.json          chart, host page, view, files and their SHA-256
  article.md         the host page's prose with [FIG nn: <chart slug>] placeholders (absent without a host page)
  figs/01 <title>.txt   chart text as published (title, subtitle, note, source, units) and the view URL
  figs/01 <title>.csv   OWID's data for exactly this view (grapher .csv?csvType=filtered with the view's query)
  figs/01 <title>.png   OWID's rendering of this view
  figs/01 <title>/chart.config.json, chart.metadata.json   grapher config and indicator metadata (for golden programs)
meta.json also maps each figure CSV column to OWID's indicator short name (the same view downloaded with short column
names), which names the column of OWID's V-Dem tables the figure plots.
Pages are read from --pages (fetched there when missing). Existing folders are left untouched; delete one to rebuild it.
"""
import argparse
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from scripts.build_owid_article import article_blocks, context_of, embed_of, page_root

USER_AGENT = "OWID-VDem-Data-Task/0.1 (research)"
GRAPHER = "https://ourworldindata.org/grapher"


def get(url: str) -> requests.Response:
    for attempt in range(4):
        response = requests.get(url, timeout=120, headers={"User-Agent": USER_AGENT})
        if response.status_code < 500:
            response.raise_for_status()
            time.sleep(1)
            return response
        time.sleep(5 * (attempt + 1))
    response.raise_for_status()
    return response


def page_path(pages: Path, url: str) -> Path:
    path = pages / f"{url.rstrip('/').split('/')[-1]}.html"
    if not path.exists() or path.stat().st_size == 0:
        path.write_text(get(url).text, encoding="utf-8")
    return path


def figure_embeds(pages: Path, urls: list[str], crawl: dict) -> dict[str, list[dict]]:
    """chart slug -> the pages that show it as a figure, with the figure's position, the page's figure count and query."""
    shown: dict[str, list[dict]] = {}
    for url in urls:
        root = page_root(BeautifulSoup(page_path(pages, url).read_text(encoding="utf-8"), "html.parser"))
        _, figures = article_blocks(root)
        page = crawl["articles"].get(url, {})
        for index, node in enumerate(figures, 1):
            embed = embed_of(node)
            if embed["slug"]:
                shown.setdefault(embed["slug"], []).append(
                    {"url": url, "title": page.get("title", "").replace(" | Our World in Data", ""),
                     "published": page.get("published"), "index": index, "figures": len(figures), "query": embed["query"]})
    return shown


def choose_host(candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    return sorted(candidates, key=lambda c: (c["figures"], -int((c["published"] or "0000")[:4]), c["url"]))[0]


def safe_name(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r'[/\\:*?"<>|]', "-", title)).strip()[:120]


def short_names(slug: str, query: dict, csv_path: Path) -> dict[str, str]:
    """The figure CSV's column headers -> OWID's indicator short names, from the same view with short column names."""
    url = f"{GRAPHER}/{slug}.csv?" + urlencode({"csvType": "filtered", "useColumnShortNames": "true", **query})
    short = get(url).text.splitlines()[0].split(",")
    published = csv_path.read_text(encoding="utf-8").splitlines()[0]
    long = next(csv.reader([published]))
    if len(long) != len(short):
        raise ValueError(f"{slug}: {len(long)} columns with display names but {len(short)} with short names")
    return dict(zip(long, short))


def add_short_names(folder: Path) -> None:
    """Record the figure columns' short names in meta.json (folders built before this step existed)."""
    meta_path = folder / "meta.json"
    meta = json.loads(meta_path.read_text())
    record = meta["figures"][0]
    if "column_short_names" not in record:
        record["column_short_names"] = short_names(meta["chart_slug"], record["embed"]["query"],
                                                   folder / record["files"]["csv"]["path"])
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def build_one(chart: dict, host: dict | None, out_root: Path, pages: Path) -> Path:
    slug = chart["slug"]
    folder = out_root / slug
    if (folder / "meta.json").exists():
        add_short_names(folder)
        return folder
    config = get(f"{GRAPHER}/{slug}.config.json").json()
    metadata = get(f"{GRAPHER}/{slug}.metadata.json").json()
    query = dict(host["query"]) if host else {}
    name = f"01 {safe_name(config.get('title') or slug)}"
    figs = folder / "figs"
    (figs / name).mkdir(parents=True, exist_ok=True)
    (figs / name / "chart.config.json").write_text(json.dumps(config, ensure_ascii=False, indent=1), encoding="utf-8")
    (figs / name / "chart.metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=1), encoding="utf-8")

    view_url = f"{GRAPHER}/{slug}" + (f"?{urlencode(query)}" if query else "")
    csv_url = f"{GRAPHER}/{slug}.csv?" + urlencode({"csvType": "filtered", **query})
    png_url = f"{GRAPHER}/{slug}.png" + (f"?{urlencode(query)}" if query else "")
    (figs / f"{name}.csv").write_bytes(get(csv_url).content)
    (figs / f"{name}.png").write_bytes(get(png_url).content)

    columns = metadata.get("columns", {})
    lines = [f"Figure 01: {name}",
             f"Article: {host['title']} ({host['published']})" if host else "Article: none (no page shows this chart)", "",
             f"Title: {config.get('title', '')}", f"Subtitle: {config.get('subtitle', '')}",
             f"Note: {config.get('note', '')}",
             f"Source: {config.get('sourceDesc') or metadata.get('chart', {}).get('citation', '')}",
             "Units: " + "; ".join(sorted({c.get('unit') or '' for c in columns.values()} - {""})),
             f"Chart: {view_url}"]
    files = {"txt": f"figs/{name}.txt", "csv": f"figs/{name}.csv", "png": f"figs/{name}.png",
             "config": f"figs/{name}/chart.config.json", "metadata": f"figs/{name}/chart.metadata.json"}
    if host:
        html = page_path(pages, host["url"]).read_text(encoding="utf-8")
        blocks, figures = article_blocks(page_root(BeautifulSoup(html, "html.parser")))
        names = {f"[FIG {i:02d}]": embed_of(node)["slug"] or "image" for i, node in enumerate(figures, 1)}
        prose = [f"[FIG {b[5:7]}: {names[b]}]" if b in names else b for b in blocks]
        (folder / "article.md").write_text(f"Source: {host['url']}\n\n" + "\n\n".join(prose) + "\n", encoding="utf-8")
        before, after = context_of(blocks, host["index"])
        lines += ["", f"Text before the figure: {before}", f"Text after the figure: {after}"]
        files["article"] = "article.md"
    (figs / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    record = {"index": host["index"] if host else 1, "name": name, "embed": {"slug": slug, "query": query},
              "view_url": view_url, "csv_url": csv_url, "png_url": png_url, "data_available": True,
              "config_title": config.get("title"), "config_subtitle": config.get("subtitle"),
              "files": {k: {"path": p, "sha256": hashlib.sha256((folder / p).read_bytes()).hexdigest()}
                        for k, p in files.items()}}
    meta = {"title": config.get("title"), "chart_slug": slug, "chart_url": f"{GRAPHER}/{slug}",
            "url": host["url"] if host else f"{GRAPHER}/{slug}", "date_published": host["published"] if host else None,
            "host": host, "authors": [], "retrieved_at": datetime.now(timezone.utc).isoformat(), "figures": [record]}
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    add_short_names(folder)
    return folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("charts", type=Path)
    parser.add_argument("crawl", type=Path)
    parser.add_argument("out_root", type=Path)
    parser.add_argument("--pages", type=Path, default=Path("data/cache/pages"))
    args = parser.parse_args()
    args.pages.mkdir(parents=True, exist_ok=True)
    selection, crawl = json.loads(args.charts.read_text()), json.loads(args.crawl.read_text())
    slugs = {c["slug"] for c in selection["charts"]}
    urls = sorted({u for u, a in crawl["articles"].items() if slugs & set(a.get("embedded", []))})
    shown = figure_embeds(args.pages, urls, crawl)
    hosted = 0
    for chart in selection["charts"]:
        host = choose_host(shown.get(chart["slug"], []))
        hosted += host is not None
        folder = build_one(chart, host, args.out_root, args.pages)
        print(f"{chart['slug']}: {'host ' + host['url'].split('/')[-1] if host else 'no host page'} -> {folder.name}",
              flush=True)
    print(f"done: {len(selection['charts'])} charts, {hosted} with a host page")


if __name__ == "__main__":
    main()
