"""Make an offline, styled copy of a saved OWID page.

    python -m scripts.snapshot_page <source.original.html> <page_url> <out.html> <assets_dir>

The original HTML is left untouched (it is the provenance record). The copy:
- downloads stylesheets, the fonts and images they reference, images (`src`, `srcset`, `<picture><source>`) and
  icons into <assets_dir>, and rewrites references to relative local paths;
- removes scripts except JSON-LD. The interactive bundle fetches chart data at run time and the analytics beacon is
  third-party; without scripts the page shows OWID's own no-JavaScript rendering (static chart images);
- turns remaining site-relative links into absolute URLs, so navigation still reaches ourworldindata.org.
A manifest of downloaded assets (URL, local path, bytes, SHA-256) is written next to the assets.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "OWID-VDem-Data-Task/0.1 (research)"
CSS_URL = re.compile(r"url\(\s*(['\"]?)([^'\")]+)\1\s*\)")


class AssetStore:
    """Downloads each URL once into a flat directory with collision-free, readable file names."""

    def __init__(self, directory: Path):
        self.directory, self.session, self.files = directory, requests.Session(), {}
        directory.mkdir(parents=True, exist_ok=True)

    def local_name(self, url: str, content_type: str) -> str:
        parsed = urlparse(url)
        stem = Path(parsed.path).name or "index"
        suffix = Path(stem).suffix
        if not suffix:
            guessed = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/svg+xml": ".svg",
                       "image/avif": ".avif", "text/css": ".css"}.get(content_type.split(";")[0].strip(), "")
            stem += guessed
        digest = hashlib.sha1(url.encode()).hexdigest()[:10]
        return f"{Path(stem).stem}-{digest}{Path(stem).suffix}"

    def get(self, url: str) -> tuple[str, bytes] | None:
        if url in self.files:
            return self.files[url]["path"], (self.directory / self.files[url]["path"]).read_bytes()
        response = self.session.get(url, headers={"User-Agent": USER_AGENT}, timeout=120)
        time.sleep(0.5)
        if response.status_code != 200:
            print(f"skip {response.status_code} {url}", flush=True)
            return None
        name = self.local_name(url, response.headers.get("content-type", ""))
        (self.directory / name).write_bytes(response.content)
        self.files[url] = {"path": name, "bytes": len(response.content),
                           "sha256": hashlib.sha256(response.content).hexdigest()}
        return name, response.content


def localise_css(css: str, css_url: str, store: AssetStore) -> str:
    def replace(match):
        target = match.group(2)
        if target.startswith("data:"):
            return match.group(0)
        stored = store.get(urljoin(css_url, target))
        return f'url("{stored[0]}")' if stored else match.group(0)
    return CSS_URL.sub(replace, css)


def snapshot(source: Path, page_url: str, out: Path, assets: Path) -> dict:
    soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
    store = AssetStore(assets)
    prefix = assets.name

    def local(url: str) -> str | None:
        stored = store.get(urljoin(page_url, url))
        return f"{prefix}/{stored[0]}" if stored else None

    for script in soup.find_all("script"):
        if script.get("type") != "application/ld+json":
            script.decompose()
    for link in soup.find_all("link"):
        rel = set(link.get("rel") or [])
        href = link.get("href")
        if not href:
            continue
        if "stylesheet" in rel or ("preload" in rel and link.get("as") == "style"):
            css_url = urljoin(page_url, href)
            response = store.session.get(css_url, headers={"User-Agent": USER_AGENT}, timeout=120)
            response.raise_for_status()
            name = store.local_name(css_url, "text/css")
            text = localise_css(response.text, css_url, store)
            (assets / name).write_text(text, encoding="utf-8")
            store.files[css_url] = {"path": name, "bytes": len(text.encode()), "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                    "note": "url() references rewritten to local files"}
            link["href"] = f"{prefix}/{name}"
        elif rel & {"icon", "apple-touch-icon"}:
            link["href"] = local(href) or urljoin(page_url, href)
        elif rel & {"preload", "modulepreload"}:
            link.decompose()
        else:
            link["href"] = urljoin(page_url, href)
    for node in soup.find_all(["img", "source"]):
        if node.get("src"):
            node["src"] = local(node["src"]) or urljoin(page_url, node["src"])
        if node.get("srcset"):
            candidates = []
            for candidate in node["srcset"].split(","):
                parts = candidate.strip().split()
                if parts:
                    candidates.append(" ".join([local(parts[0]) or urljoin(page_url, parts[0]), *parts[1:]]))
            node["srcset"] = ", ".join(candidates)
    for anchor in soup.find_all("a", href=True):
        if not anchor["href"].startswith(("#", "mailto:", "http://", "https://")):
            anchor["href"] = urljoin(page_url, anchor["href"])
    out.write_text(str(soup), encoding="utf-8")
    manifest = {"page_url": page_url, "original": source.name,
                "original_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "removed": "all <script> elements except application/ld+json", "assets": store.files}
    (assets / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("url")
    parser.add_argument("out", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    manifest = snapshot(args.source, args.url, args.out, args.assets)
    print(f"{len(manifest['assets'])} assets -> {args.assets}")


if __name__ == "__main__":
    main()
