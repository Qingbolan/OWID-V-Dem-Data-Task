"""Attach chart and report counts to the snapshot index.

    python -m scripts.owid_mapping.merge_counts <snapshot_index.json> <crawl.json> <out.json>

Definitions:
- charts_downstream: charts with at least one indicator whose ETL dataset (indicator catalogPath) is a downstream
  grapher dataset of the group. Includes charts that use the group only for grouping or per-capita denominators.
- charts_direct: the subset where an indicator in such a dataset lists the group's producer AND a matching dataset
  title among its origins (separates e.g. different UN agencies or different World Bank databases).
- articles / articles_2026: OWID articles and topic pages (site-root URLs) embedding at least one direct chart;
  2026 means JSON-LD datePublished in 2026. data_insights are counted separately. Country profiles (/profile/),
  team and other non-analysis pages are excluded.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

EXCLUDED_SECTIONS = {"profile", "team", "about", "search", "donate", "subscribe", "explorers", "faqs", "latest",
                     "funding", "jobs"}
STOPWORDS = {"the", "of", "and", "for", "by", "in", "on", "a", "an", "data", "database", "dataset", "update", "interim"}


def normalise(text) -> str:
    return " ".join(str(text or "").replace("–", " ").replace("-", " ").split()).casefold()


def significant_words(title: str) -> set[str]:
    return {w for w in title.split() if w not in STOPWORDS and len(w) > 2}


def title_match(a: str, b: str) -> bool:
    """Two dataset titles name the same dataset: containment, or >= 75 % of the shorter title's significant words."""
    if a in b or b in a:
        return True
    wa, wb = significant_words(a), significant_words(b)
    return bool(wa and wb) and len(wa & wb) / min(len(wa), len(wb)) >= 0.75


def page_kind(url: str):
    parts = url.rstrip("/").split("/")[3:]
    if not parts or parts[0] in EXCLUDED_SECTIONS:
        return None
    if parts[0] == "data-insights":
        return "data_insight"
    return "article" if len(parts) == 1 else None


def merge(index: dict, crawl: dict) -> dict:
    indicators = crawl["indicators"]
    dataset_charts = defaultdict(set)
    for slug, ids in crawl["chart_indicators"].items():
        for indicator in ids:
            dataset = (indicators.get(str(indicator)) or {}).get("dataset")
            if dataset:
                dataset_charts[dataset].add((slug, str(indicator)))
    chart_pages = defaultdict(set)
    for url, page in crawl["articles"].items():
        if page_kind(url):
            for slug in page["embedded"]:
                chart_pages[slug].add(url)

    def published(url: str) -> str:
        return crawl["articles"][url]["published"] or ""

    for group in index["groups"]:
        producers = {normalise(p) for p in group["producers"]}
        titles = {normalise(t) for t in group["titles"]}
        downstream, direct = set(), set()
        for step in group["grapher_datasets"]:
            for slug, indicator in dataset_charts.get(step.replace("data://", ""), ()):
                downstream.add(slug)
                for origin in indicators[indicator]["origins"]:
                    producer, title = normalise(origin.get("producer")), normalise(origin.get("title"))
                    if producer and title and any(p in producer or producer in p for p in producers) \
                            and any(title_match(title, t) for t in titles):
                        direct.add(slug)
                        break
        pages = {url for slug in direct for url in chart_pages.get(slug, ())}
        articles = sorted((u for u in pages if page_kind(u) == "article"), key=published, reverse=True)
        insights = sorted((u for u in pages if page_kind(u) == "data_insight"), key=published, reverse=True)
        group.update(
            charts_downstream=len(downstream), charts_direct=len(direct), direct_chart_slugs=sorted(direct),
            articles=len(articles), articles_2026=sum(published(u).startswith("2026") for u in articles),
            data_insights=len(insights), data_insights_2026=sum(published(u).startswith("2026") for u in insights),
            pages=[{"url": u, "kind": page_kind(u), "published": published(u), "title": crawl["articles"][u]["title"],
                    "direct_charts": sorted(set(crawl["articles"][u]["embedded"]) & direct)}
                   for u in articles + insights])
    index["groups"].sort(key=lambda g: (-g["charts_direct"], -g["charts_downstream"], g["group"]))
    index["crawl"] = {"charts": len(crawl["chart_indicators"]), "indicators": len(indicators), "pages": len(crawl["articles"])}
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("index", type=Path)
    parser.add_argument("crawl", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    merged = merge(json.loads(args.index.read_text()), json.loads(args.crawl.read_text()))
    args.out.write_text(json.dumps(merged, ensure_ascii=False, indent=1))
    for g in merged["groups"][:10]:
        print(f"{g['group']:34s} direct={g['charts_direct']:4d} downstream={g['charts_downstream']:4d} "
              f"articles={g['articles']:3d} (2026: {g['articles_2026']})")


if __name__ == "__main__":
    main()
