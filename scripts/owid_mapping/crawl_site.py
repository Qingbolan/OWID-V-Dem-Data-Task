"""Crawl ourworldindata.org: charts -> indicators -> ETL datasets, and pages -> embedded charts.

    python -m scripts.owid_mapping.crawl_site <cache_dir> <out.json>

1. The sitemap lists grapher chart slugs and site pages.
2. Each chart's `.metadata.json` gives its indicator ids; the indicator API
   (`api.ourworldindata.org/v1/indicators/<id>.metadata.json`) gives the indicator's ETL dataset (`catalogPath`)
   and origins (producer, title, publication date).
3. Each page's HTML gives its JSON-LD `datePublished` and the charts it embeds (grapher images and embeds) or links.
Every response is cached under <cache_dir>, so re-runs are offline and resumable. Requests use four workers with a
pause between requests.
"""
import argparse
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

USER_AGENT = "OWID-WPP-Data-Task/0.1 (research)"
SITEMAP = "https://ourworldindata.org/sitemap.xml"


class CachedFetcher:
    def __init__(self, cache: Path):
        self.cache, self.session = cache, requests.Session()

    def get(self, url: str, kind: str) -> str | None:
        path = self.cache / kind / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
        if path.exists():
            return path.read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(4):
            try:
                response = self.session.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
                if response.status_code == 404:
                    path.write_text("", encoding="utf-8")
                    return ""
                response.raise_for_status()
                path.write_text(response.text, encoding="utf-8")
                time.sleep(0.25)
                return response.text
            except requests.RequestException:
                time.sleep(2 * (attempt + 1))
        return None


def parallel(function, items: list, label: str) -> dict:
    results = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for n, (item, value) in enumerate(zip(items, pool.map(function, items)), 1):
            results[item] = value
            if n % 250 == 0:
                print(f"{label}: {n}/{len(items)}", flush=True)
    return results


def chart_indicator_ids(text: str | None) -> list[int]:
    try:
        columns = json.loads(text)["columns"].values() if text else []
    except (ValueError, KeyError):
        return []
    return sorted({c["owidVariableId"] for c in columns if c.get("owidVariableId")})


def indicator_record(text: str | None) -> dict:
    try:
        data = json.loads(text) if text else {}
    except ValueError:
        data = {}
    path = data.get("catalogPath") or ""
    return {"dataset": path.split("#")[0].rsplit("/", 1)[0] if path else None, "dataset_name": data.get("datasetName"),
            "origins": [{"producer": o.get("producer"), "title": o.get("title"), "date_published": o.get("datePublished")}
                        for o in data.get("origins") or []]}


def page_record(html: str | None) -> dict:
    html = html or ""
    published = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html)
    title = re.search(r"<title>([^<]+)</title>", html)
    embedded = set(re.findall(r"grapher/([a-z0-9-]+)\.png", html)) | \
        set(re.findall(r'data-grapher-src="[^"]*?/grapher/([a-z0-9-]+)', html))
    linked = set(re.findall(r'href="https://ourworldindata\.org/grapher/([a-z0-9-]+)', html))
    return {"published": published.group(1)[:10] if published else None, "title": title.group(1) if title else None,
            "embedded": sorted(embedded), "linked": sorted(linked - embedded)}


def crawl(cache: Path) -> dict:
    fetcher = CachedFetcher(cache)
    urls = re.findall(r"<loc>([^<]+)</loc>", fetcher.get(SITEMAP, "sitemap") or "")
    slugs = sorted({u.split("/grapher/")[1] for u in urls if "/grapher/" in u})
    pages = sorted(u for u in urls if "/grapher/" not in u and "/explorers/" not in u)
    print(f"charts={len(slugs)} pages={len(pages)}", flush=True)
    chart_meta = parallel(lambda s: fetcher.get(f"https://ourworldindata.org/grapher/{s}.metadata.json", "chart_meta"),
                          slugs, "chart metadata")
    chart_indicators = {slug: chart_indicator_ids(text) for slug, text in chart_meta.items()}
    ids = sorted({i for values in chart_indicators.values() for i in values})
    indicator_meta = parallel(
        lambda i: fetcher.get(f"https://api.ourworldindata.org/v1/indicators/{i}.metadata.json", "indicator_meta"),
        ids, "indicator metadata")
    articles = parallel(lambda u: page_record(fetcher.get(u, "pages")), pages, "pages")
    return {"chart_indicators": chart_indicators,
            "indicators": {str(i): indicator_record(text) for i, text in indicator_meta.items()},
            "articles": articles}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cache", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = crawl(args.cache)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False))
    print(f"done: {len(result['chart_indicators'])} charts, {len(result['indicators'])} indicators, "
          f"{len(result['articles'])} pages")


if __name__ == "__main__":
    main()
