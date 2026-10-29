"""Materialise every page with a figure list in scripts/articles/ into an article folder, with WPP's tool.

    python -m scripts.build_pages <figure_lists_dir> <OWID root> [--pages data/cache/pages]

For each <page slug>.json ({"url", "figures"}), the page is read from --pages (fetched there when missing) and
scripts.build_owid_article writes OWID/<page slug>-[<date published>]/ (source.original.html, offline snapshot,
article.md, meta.json, figs/). Folders that already have a meta.json are left untouched.
"""
import argparse
import json
from pathlib import Path

from scripts.build_owid_article import build
from scripts.owid_pages import page_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("figure_lists", type=Path)
    parser.add_argument("root", type=Path)
    parser.add_argument("--pages", type=Path, default=Path("data/cache/pages"))
    args = parser.parse_args()
    args.pages.mkdir(parents=True, exist_ok=True)
    done = {p.parent.name.split("-[")[0] for p in args.root.glob("*/meta.json")}
    for path in sorted(args.figure_lists.glob("*.json")):
        if path.stem in done:
            continue
        figure_list = json.loads(path.read_text())
        print(build(page_path(args.pages, figure_list["url"]), figure_list["url"], figure_list["figures"], args.root),
              flush=True)


if __name__ == "__main__":
    main()
