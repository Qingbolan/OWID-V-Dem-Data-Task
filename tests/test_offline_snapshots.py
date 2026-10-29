"""Offline page snapshots are self-contained: no executable scripts, every local asset exists."""
from pathlib import Path
from urllib.parse import unquote

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob("OWID/*/source.html"))


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.parent.name[:40])
def test_snapshot_is_self_contained(page):
    soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
    assert all(s.get("type") == "application/ld+json" for s in soup.find_all("script"))
    references = [link["href"] for link in soup.find_all("link", href=True) if "stylesheet" in (link.get("rel") or [])]
    references += [node["src"] for node in soup.find_all(["img", "source"], src=True)]
    references += [c.split()[0] for node in soup.find_all(["img", "source"], srcset=True) for c in node["srcset"].split(",")]
    for reference in references:
        assert not reference.startswith("/"), f"site-relative reference left: {reference}"
        if not reference.startswith(("http://", "https://", "data:")):
            assert (page.parent / unquote(reference)).exists(), f"missing local asset: {reference}"
    assert (page.parent / "source.original.html").exists()
