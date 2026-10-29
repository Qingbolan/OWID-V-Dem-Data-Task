"""Write scripts/articles/<slug>.json, the figure list scripts.build_owid_article needs, for pages that embed charts.

    python -m scripts.list_page_figures <page.html> <page_url> <out.json> [--cache data/cache/grapher]

Figures are listed in document order, as build_owid_article finds them. A figure that embeds a grapher chart is named
"NN <chart title>" (the title from the chart's config); any other figure (a static image, a bespoke component) is
named "NN <kind>". Static images that show a chart (data insights) are identified by hand instead, as in the WPP
benchmark: their entry gives the identified view (see build_owid_article's docstring).
"""
import argparse
import json
from pathlib import Path

from bs4 import BeautifulSoup

from scripts.build_owid_article import GRAPHER, article_blocks, embed_of, page_root
from scripts.owid_pages import get, safe_name


def chart_title(slug: str, cache: Path) -> str:
    path = cache / f"{slug}.config.json"
    if not path.exists():
        path.write_text(get(f"{GRAPHER}/{slug}.config.json").text, encoding="utf-8")
    return json.loads(path.read_text()).get("title") or slug


def figure_names(html: str, cache: Path) -> list[str]:
    _, figures = article_blocks(page_root(BeautifulSoup(html, "html.parser")))
    names = []
    for index, node in enumerate(figures, 1):
        slug = embed_of(node)["slug"]
        kind = "bespoke component" if "bespoke-component" in str(node) else "image"
        names.append(f"{index:02d} {safe_name(chart_title(slug, cache)) if slug else kind}")
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("page", type=Path)
    parser.add_argument("url")
    parser.add_argument("out", type=Path)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/grapher"))
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    names = figure_names(args.page.read_text(encoding="utf-8"), args.cache)
    args.out.write_text(json.dumps({"url": args.url, "figures": names}, ensure_ascii=False, indent=1) + "\n")
    print(f"{args.out}: {len(names)} figures")


if __name__ == "__main__":
    main()
