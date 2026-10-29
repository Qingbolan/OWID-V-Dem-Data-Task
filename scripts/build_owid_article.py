"""Materialise one OWID article into OWID/<slug>-[YYYY-MM-DD]/.

    python -m scripts.build_owid_article <source.html> <article_url> <figures.json> <out_root>
    python -m scripts.build_owid_article --refresh-prose <article folder>

Writes source.original.html (the page exactly as retrieved), source.html with source_files/ (an offline, styled
snapshot made by scripts.snapshot_page), article.md (prose with [FIG nn] placeholders where figures were),
meta.json, and for each figure in document order figs/<name>.{txt,png,html,csv}:
  .txt   chart text as published (title, subtitle, note, unit, source) plus the embed URL and surrounding prose
  .png   OWID's rendering of exactly this view (grapher .png with the embed's query string, or the static image)
  .html  the figure's HTML fragment from source.html
  .csv   OWID's data for exactly this view (grapher .csv?csvType=filtered with the embed's query string); for map
         views this is the set of entities the map displays, which excludes small territories shown in the table view
Both page types are supported: articles (<article>) and data insights (.standalone-post-body).

figures.json lists the figures in document order. An entry is either the figure's display name, or an object
{"name", "view", "image_title", "image_subtitle", "identification"} for a static image (typically a designed chart
in a data insight) whose underlying OWID chart was identified by hand: `view` is that chart's URL with the query
string of the view the image shows, `image_title`/`image_subtitle` are transcribed from the image, and
`identification` says how the view was matched to the image. For such figures .csv comes from the identified view
and .png is the published image. An optional "scope" ({"entities": [...], "years": [...]}) keeps only the rows the
image shows, when it shows part of the view (for example two years of a time series, or one continent of a map).
An optional "derive" ({"difference": column, "from_year", "to_year", "name"}) replaces the rows by the change of
`column` between the two years, when the image shows that change rather than the view's values. Figures without a data endpoint (in-browser components such as the population
simulation) get .txt/.html here, with the component's authored settings in .txt; their data and image come from
scripts.capture_svg_figure.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

import requests
from bs4 import BeautifulSoup

from scripts.snapshot_page import snapshot

USER_AGENT = "OWID-VDem-Data-Task/0.1 (research)"
GRAPHER = "https://ourworldindata.org/grapher"


def get(url: str) -> requests.Response:
    response = requests.get(url, timeout=120, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    time.sleep(1)
    return response


def is_figure(node) -> bool:
    classes = node.get("class", [])
    joined = " ".join(classes)
    if node.name == "figure" and ("chart" in classes or "article-block__image" in joined):
        return True
    return node.name == "div" and ("pull-chart" in classes or "bespoke-component" in joined)


def embed_of(node) -> dict:
    """Grapher slug and query string of the view a figure node shows."""
    html = str(node)
    image = re.search(r'grapher/([a-z0-9-]+)\.png(\?[^"\s]*)?', html)
    link = re.search(r'href="https://ourworldindata\.org/grapher/([a-z0-9-]+)(\?[^"\s]*)?"', html)
    found = image or link
    if not found:
        return {"slug": None, "query": {}, "image": (node.find("img") or {}).get("src")}
    query = dict(parse_qsl((found.group(2) or "").lstrip("?").replace("&amp;", "&")))
    query.pop("imWidth", None)
    static = None if image else (node.find("img") or {}).get("src")
    return {"slug": found.group(1), "query": query, "image": static}


def bespoke_blocks(html: str) -> list[dict]:
    """Bespoke components of the page in document order: bundle, variant and the authored config."""
    decoder, blocks = json.JSONDecoder(), []
    for match in re.finditer(r'"type":"bespoke-component"', html):
        # The block is the innermost JSON object around the match; its other keys may precede "type".
        start = html.rfind("{", 0, match.start())
        while start >= 0:
            try:
                block, end = decoder.raw_decode(html, start)
                if end > match.start() and block.get("type") == "bespoke-component":
                    break
            except json.JSONDecodeError:
                pass
            start = html.rfind("{", 0, start)
        blocks.append({"bundle": block.get("bundle"), "variant": block.get("variant"), "config": block.get("config", {})})
    return blocks


def bespoke_text(block: dict, article_title: str, published: str, index: int, name: str,
                 rendered: dict | None = None) -> list[str]:
    """Figure text of a bespoke component: authored config, plus what the rendered component shows when available."""
    config, rendered = block["config"], rendered or {}
    lines = [f"Figure {index:02d}: {name}", f"Article: {article_title} ({published})", "",
             f"Title: {config.get('title', '')}", f"Subtitle: {config.get('subtitle', '')}",
             f"Note: {rendered.get('note', '')}", f"Source: {rendered.get('source', '')}",
             f"Units: {rendered.get('units', '')}",
             f"Component: {block['bundle']}/{block['variant']} (computed in the reader's browser)",
             "Settings: " + json.dumps(config, ensure_ascii=False)]
    if rendered.get("panel"):
        lines.append(f"Chart: {rendered['panel']}")
    if rendered.get("assumptions"):
        lines += ["Assumptions shown:", *[f"  {row}" for row in rendered["assumptions"]]]
    return lines


def page_root(soup):
    """The element holding the report: <article> for articles, the post body for data insights."""
    return soup.find("article") or soup.select_one(".standalone-post-body__blocks")


def figure_spec(entry) -> dict:
    return {"name": entry} if isinstance(entry, str) else dict(entry)


def image_source(node) -> str | None:
    """Largest published variant of a figure's image."""
    img = node.find("img")
    if img is None:
        return None
    candidates = [c.strip().split() for c in (node.find("source") or img).get("srcset", "").split(",") if c.strip()]
    if candidates:
        return max(candidates, key=lambda c: int(c[1].rstrip("w")) if len(c) > 1 else 0)[0]
    return img.get("src")


def trim_to_scope(csv_path: Path, scope: dict) -> None:
    """Keep the rows of a figure CSV whose entity and year the figure shows; fail if a scoped key is missing."""
    import pandas as pd

    frame = pd.read_csv(csv_path, header=None, skiprows=1, dtype=str, keep_default_na=False)
    header = pd.read_csv(csv_path, nrows=0).columns
    entity, year = list(header).index("Entity"), list(header).index("Year")
    keep = pd.Series(True, index=frame.index)
    if "entities" in scope:
        keep &= frame[entity].isin(scope["entities"])
        missing = set(scope["entities"]) - set(frame[entity])
        if missing:
            raise ValueError(f"{csv_path.name}: scoped entities not in the view: {sorted(missing)}")
    if "years" in scope:
        keep &= frame[year].astype(int).isin(scope["years"])
    frame = frame[keep]
    frame.columns = header
    frame.to_csv(csv_path, index=False)


def derive_difference(csv_path: Path, derive: dict) -> None:
    """Rewrite a figure CSV as the change of one column between two years (one row per entity, at `to_year`)."""
    import pandas as pd

    frame = pd.read_csv(csv_path)
    wide = frame.pivot_table(index=["Entity", "Code"], columns="Year", values=derive["difference"], aggfunc="first")
    change = (wide[derive["to_year"]] - wide[derive["from_year"]]).dropna().reset_index(name=derive["name"])
    change.insert(2, "Year", derive["to_year"])
    change.to_csv(csv_path, index=False)


def text_of(node) -> str:
    return " ".join(node.get_text(" ", strip=True).split())


def text_blocks(node) -> list[str]:
    """Headings, paragraphs and list items under `node`, in document order, as markdown lines."""
    blocks = []
    for child in node.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if any(p.name in {"p", "li"} for p in child.parents) or (child.name == "li" and child.find(["p", "li"])):
            continue
        text = text_of(child)
        if text:
            blocks.append(("#" * int(child.name[1]) + " " if child.name.startswith("h") else "") + text)
    return blocks


def article_blocks(article) -> tuple[list[str], list]:
    """The article as markdown blocks with [FIG nn] markers, and the figure nodes in document order.

    Site chrome (newsletter banners, navigation) is dropped. A pull-chart block pairs a chart with prose set beside
    it; the prose belongs to the article and follows the figure marker, as it follows the chart in the page.
    """
    for node in article.select("script, style, nav, aside, footer, .subscribe-banner, [class*='subscribe-banner']"):
        node.decompose()
    blocks, figures = [], []
    for node in article.find_all(True):
        if any(is_figure(p) for p in node.parents if p is not article):
            continue
        if is_figure(node):
            figures.append(node)
            blocks.append(f"[FIG {len(figures):02d}]")
            for content in node.select(".pull-chart__content"):
                blocks += text_blocks(content)
        elif node.name in {"h1", "h2", "h3", "h4", "p", "li"} and not any(p.name in {"p", "li"} for p in node.parents):
            if node.name == "li" and node.find(["p", "li"]):
                continue
            text = text_of(node)
            if text:
                blocks.append(("#" * int(node.name[1]) + " " if node.name.startswith("h") else "") + text)
    return blocks, figures


def context_of(blocks: list[str], index: int) -> tuple[str, str]:
    """The prose block before and after figure `index` (1-based)."""
    position = blocks.index(f"[FIG {index:02d}]")
    before = next((b for b in reversed(blocks[:position]) if not b.startswith("[FIG")), "")
    after = next((b for b in blocks[position + 1:] if not b.startswith("[FIG")), "")
    return before, after


def write_prose(folder: Path, url: str, blocks: list[str], names: dict[str, str]) -> None:
    prose = [f"[FIG {b[5:7]}: {names[b]}]" if b in names else b for b in blocks]
    (folder / "article.md").write_text(f"Source: {url}\n\n" + "\n\n".join(prose) + "\n", encoding="utf-8")


def refresh_prose(folder: Path) -> None:
    """Re-extract article.md and each figure's surrounding prose from source.original.html, without re-downloading
    figure data, images or the offline snapshot; figure .txt hashes in meta.json are updated."""
    meta_path = folder / "meta.json"
    meta = json.loads(meta_path.read_text())
    article = page_root(BeautifulSoup((folder / "source.original.html").read_text(encoding="utf-8"), "html.parser"))
    blocks, figures = article_blocks(article)
    if len(figures) != len(meta["figures"]):
        raise ValueError(f"{len(figures)} figures in the page but {len(meta['figures'])} in meta.json")
    write_prose(folder, meta["url"], blocks, {f"[FIG {r['index']:02d}]": r["name"] for r in meta["figures"]})
    for record in meta["figures"]:
        before, after = context_of(blocks, record["index"])
        path = folder / record["files"]["txt"]["path"]
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("Text ")]
        while lines and not lines[-1]:
            lines.pop()
        lines += ["", f"Text before the figure: {before}", f"Text after the figure: {after}"]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        record["files"]["txt"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def build(source: Path, url: str, entries: list, out_root: Path) -> Path:
    html = source.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    article = page_root(soup)
    specs = [figure_spec(entry) for entry in entries]
    names = [spec["name"] for spec in specs]
    published = re.search(r'"datePublished"\s*:\s*"([^"]+)"', html).group(1)[:10]
    title = text_of(soup.find("h1"))
    authors = re.findall(r'"@type"\s*:\s*"Person"\s*,\s*"name"\s*:\s*"([^"]+)"', html)
    slug = urlparse(url).path.rstrip("/").split("/")[-1]
    folder = out_root / f"{slug}-[{published}]"
    figs = folder / "figs"
    figs.mkdir(parents=True, exist_ok=True)
    (folder / "source.original.html").write_text(html, encoding="utf-8")
    page = snapshot(folder / "source.original.html", url, folder / "source.html", folder / "source_files")

    blocks, figures = article_blocks(article)
    if len(figures) != len(names):
        raise ValueError(f"{len(figures)} figures in the page but {len(names)} names in figures.json")

    bespokes = bespoke_blocks(html)
    records = []
    for i, (node, spec) in enumerate(zip(figures, specs), 1):
        name = spec["name"]
        marker = f"[FIG {i:02d}]"
        before, after = context_of(blocks, i)
        embed = embed_of(node)
        record = {"index": i, "name": name, "embed": embed, "files": {}}
        (figs / f"{name}.html").write_text(str(node), encoding="utf-8")
        record["files"]["html"] = f"figs/{name}.html"
        lines = [f"Figure {i:02d}: {name}", f"Article: {title} ({published})", ""]
        if embed["slug"]:
            query = urlencode(embed["query"])
            view_url = f"{GRAPHER}/{embed['slug']}" + (f"?{query}" if query else "")
            config = get(f"{GRAPHER}/{embed['slug']}.config.json").json()
            metadata = get(f"{GRAPHER}/{embed['slug']}.metadata.json").json()
            columns = metadata.get("columns", {})
            lines += [f"Title: {config.get('title', '')}", f"Subtitle: {config.get('subtitle', '')}",
                      f"Note: {config.get('note', '')}",
                      f"Source: {config.get('sourceDesc') or metadata.get('chart', {}).get('citation', '')}",
                      "Units: " + "; ".join(sorted({c.get('unit') or '' for c in columns.values()} - {""})),
                      f"Chart: {view_url}"]
            csv_url = f"{GRAPHER}/{embed['slug']}.csv?" + urlencode({"csvType": "filtered", **embed["query"]})
            (figs / f"{name}.csv").write_bytes(get(csv_url).content)
            png_url = embed["image"] or (f"{GRAPHER}/{embed['slug']}.png" + (f"?{query}" if query else ""))
            (figs / f"{name}.png").write_bytes(get(png_url).content)
            record.update(view_url=view_url, csv_url=csv_url, png_url=png_url, data_available=True,
                          config_title=config.get("title"), config_subtitle=config.get("subtitle"))
            record["files"].update(csv=f"figs/{name}.csv", png=f"figs/{name}.png")
        elif spec.get("view"):
            view = urlparse(spec["view"])
            slug, query = view.path.rstrip("/").split("/")[-1], dict(parse_qsl(view.query))
            config = get(f"{GRAPHER}/{slug}.config.json").json()
            metadata = get(f"{GRAPHER}/{slug}.metadata.json").json()
            columns = metadata.get("columns", {})
            alt = " ".join((node.find("img") or {}).get("alt", "").split())
            lines += [f"Title: {spec['image_title']}", f"Subtitle: {spec.get('image_subtitle', '')}",
                      f"Note: {spec.get('image_note', '')}",
                      f"Source: {config.get('sourceDesc') or metadata.get('chart', {}).get('citation', '')}",
                      "Units: " + "; ".join(sorted({c.get('unit') or '' for c in columns.values()} - {""})),
                      f"Image description: {alt}",
                      f"Underlying chart (identified): {spec['view']}"]
            csv_url = f"{GRAPHER}/{slug}.csv?" + urlencode({"csvType": "filtered", **query})
            (figs / f"{name}.csv").write_bytes(get(csv_url).content)
            if scope := spec.get("scope"):
                trim_to_scope(figs / f"{name}.csv", scope)
                record["scope"] = scope
            if derive := spec.get("derive"):
                derive_difference(figs / f"{name}.csv", derive)
                record["derive"] = derive
            png_url = image_source(node)
            (figs / f"{name}.png").write_bytes(get(png_url).content)
            record.update(view_url=spec["view"], csv_url=csv_url, png_url=png_url, data_available=True,
                          static_image=True, identification=spec.get("identification"),
                          image_title=spec["image_title"], image_subtitle=spec.get("image_subtitle"),
                          config_title=config.get("title"), config_subtitle=config.get("subtitle"))
            record["files"].update(csv=f"figs/{name}.csv", png=f"figs/{name}.png")
        elif "bespoke-component" in str(node):
            block = bespokes[sum("bespoke-component" in str(f) for f in figures[:i - 1])]
            lines = bespoke_text(block, title, published, i, name)
            record.update(data_available=False, bespoke=block)
        else:
            lines += ["This figure is a static image without a data series."]
            record.update(data_available=False)
        lines += ["", f"Text before the figure: {before}", f"Text after the figure: {after}"]
        (figs / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        record["files"]["txt"] = f"figs/{name}.txt"
        for kind, path in record["files"].items():
            record["files"][kind] = {"path": path, "sha256": hashlib.sha256((folder / path).read_bytes()).hexdigest()}
        records.append(record)
        print(f"{marker} {name}: data={record['data_available']}", flush=True)

    write_prose(folder, url, blocks, {f"[FIG {r['index']:02d}]": r["name"] for r in records})
    meta = {"title": title, "url": url, "date_published": published, "authors": authors,
            "retrieved_at": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(),
            "materialised_at": datetime.now(timezone.utc).isoformat(),
            "source_original_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "offline_snapshot": {"page": "source.html", "assets": "source_files/", "assets_manifest": "source_files/manifest.json",
                                 "asset_count": len(page["assets"]), "removed": page["removed"]},
            "figures": records}
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return folder


def main() -> None:
    if sys.argv[1:2] == ["--refresh-prose"]:
        refresh_prose(Path(sys.argv[2]))
        return
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("url")
    parser.add_argument("figures", type=Path, help="JSON list of figures in document order (see above)")
    parser.add_argument("out_root", type=Path)
    args = parser.parse_args()
    figures = json.loads(args.figures.read_text())
    if isinstance(figures, dict):  # scripts/articles/<slug>.json: {"url": ..., "figures": [...]}
        figures = figures["figures"]
    print(build(args.source, args.url, figures, args.out_root))


if __name__ == "__main__":
    main()
