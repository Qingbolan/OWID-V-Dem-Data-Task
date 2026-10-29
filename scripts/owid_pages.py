"""Helpers for reading ourworldindata.org, and the figure lists of the pages that show V-Dem charts.

    python -m scripts.owid_pages <charts.json> <crawl.json> <figure_lists_dir> [--pages data/cache/pages]

Of the pages the crawl lists for the selected V-Dem charts (data/reference/charts.json), keeps those that show at least
one of them as a figure in their prose (a topic page's "all charts" grid and related-chart thumbnails only link to a
chart) and writes each page's figure list, <figure_lists_dir>/<page slug>.json, as scripts.build_owid_article reads
it. Data insights show a chart as a static image; their lists identify the chart by hand and are not overwritten.
Pages are cached in --pages (fetched there when missing).
"""
import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scripts.build_owid_article import article_blocks, embed_of, page_root

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


def safe_name(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r'[/\\:*?"<>|]', "-", title)).strip()[:120]


def figure_embeds(pages: Path, urls: list[str]) -> dict[str, list[str]]:
    """Page URL -> the chart slugs it shows as figures in its prose, in document order."""
    shown = {}
    for url in urls:
        root = page_root(BeautifulSoup(page_path(pages, url).read_text(encoding="utf-8"), "html.parser"))
        _, figures = article_blocks(root)
        shown[url] = [embed_of(node)["slug"] for node in figures]
    return shown


def main() -> None:
    from scripts.list_page_figures import figure_names

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("charts", type=Path)
    parser.add_argument("crawl", type=Path)
    parser.add_argument("figure_lists", type=Path)
    parser.add_argument("--pages", type=Path, default=Path("data/cache/pages"))
    parser.add_argument("--cache", type=Path, default=Path("data/cache/grapher"))
    args = parser.parse_args()
    for directory in (args.pages, args.cache, args.figure_lists):
        directory.mkdir(parents=True, exist_ok=True)
    slugs = {c["slug"] for c in json.loads(args.charts.read_text())["charts"]}
    crawl = json.loads(args.crawl.read_text())
    urls = sorted({u for u, a in crawl["articles"].items() if slugs & set(a.get("embedded", []))})
    for url, shown in figure_embeds(args.pages, urls).items():
        if not slugs & set(shown) or "/data-insights/" in url:
            continue
        target = args.figure_lists / f"{url.rstrip('/').split('/')[-1]}.json"
        names = figure_names(page_path(args.pages, url).read_text(encoding="utf-8"), args.cache)
        target.write_text(json.dumps({"url": url, "figures": names}, ensure_ascii=False, indent=1) + "\n")
        print(f"{target}: {len(names)} figures, {len(slugs & set(shown))} V-Dem charts", flush=True)


if __name__ == "__main__":
    main()
