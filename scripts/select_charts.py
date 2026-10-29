"""Select the OWID charts built only on V-Dem v16 and the page each task is taken from.

    python -m scripts.select_charts <mapping.json> <crawl.json> <out.json>

A chart is selected when it is a direct chart of the snapshot group `democracy/2026-03-17` (docs/owid-mapping.md)
and every indicator it plots comes from OWID's V-Dem dataset (`grapher/democracy/2026-03-17/vdem`); OWID's region
table, which only colours maps, is allowed. Charts that also plot another dataset (GDP, child mortality, other
democracy indices, ...) are listed under "excluded" with the datasets they need.

Host page: of the pages that embed the chart, the one with the fewest embedded charts (the most focused prose), then
the most recent. A chart no page embeds has no host page; its task has title and subtitle levels only.
"""
import argparse
import json
from pathlib import Path

GROUP = "democracy/2026-03-17"
VDEM = "grapher/democracy/2026-03-17/vdem"
ALLOWED = {VDEM, "grapher/regions/2023-01-01/regions"}


def select(mapping: dict, crawl: dict) -> dict:
    group = next(g for g in mapping["groups"] if g["group"] == GROUP)
    indicators, chart_indicators = crawl["indicators"], crawl["chart_indicators"]
    hosts: dict[str, list] = {}
    for url, page in crawl["articles"].items():
        for slug in page.get("embedded", []):
            hosts.setdefault(slug, []).append({"url": url, "title": page["title"].replace(" | Our World in Data", ""),
                                               "published": page.get("published"), "charts": len(page["embedded"])})
    selected, excluded = [], []
    for slug in sorted(group["direct_chart_slugs"]):
        datasets = sorted({indicators[str(i)]["dataset"] for i in chart_indicators.get(slug, []) if str(i) in indicators})
        other = [d for d in datasets if d not in ALLOWED]
        if other:
            excluded.append({"slug": slug, "other_datasets": other})
            continue
        pages = sorted(hosts.get(slug, []), key=lambda p: (p["charts"], -(int((p["published"] or "0")[:4]) or 0)))
        selected.append({"slug": slug, "host": pages[0] if pages else None, "host_candidates": len(pages)})
    return {"group": GROUP, "dataset": VDEM, "rule": __doc__.split("\n\n")[1].replace("\n", " "),
            "charts": selected, "excluded": excluded}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mapping", type=Path)
    parser.add_argument("crawl", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = select(json.loads(args.mapping.read_text()), json.loads(args.crawl.read_text()))
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    hosted = sum(1 for c in result["charts"] if c["host"])
    print(f"{len(result['charts'])} charts selected ({hosted} with a host page), {len(result['excluded'])} excluded")


if __name__ == "__main__":
    main()
