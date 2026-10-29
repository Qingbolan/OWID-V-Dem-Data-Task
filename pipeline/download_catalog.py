"""Download OWID catalog tables (population, regions, income groups) and record their hashes.

    python -m pipeline.download_catalog <out_dir> <path> [...]

Each <path> is a table path in OWID's public catalog, e.g. garden/demography/2024-07-15/population/population; the
table's .feather and .meta.json are fetched from https://catalog.ourworldindata.org/<path> into <out_dir>/<path>.
A manifest records URL, size, MD5 and SHA-256. OWID can re-publish a catalog table under the same path, so on a
re-run a file whose MD5 differs from the manifest aborts the download instead of replacing it silently.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from pipeline.download_snapshots import USER_AGENT, digest

CATALOG = "https://catalog.ourworldindata.org"


def download(out: Path, paths: list[str]) -> dict:
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for path in paths:
        for suffix in (".feather", ".meta.json"):
            key, target = path + suffix, out / (path + suffix)
            url = f"{CATALOG}/{key}"
            if key in manifest and target.exists() and digest(target, "md5") == manifest[key]["md5"]:
                print(f"ok {key} (already verified)", flush=True)
                continue
            response = requests.get(url, timeout=120, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.content)
            md5 = digest(target, "md5")
            if key in manifest and manifest[key]["md5"] != md5:
                raise ValueError(f"{key} changed upstream: MD5 {md5}, manifest {manifest[key]['md5']}")
            manifest[key] = {"url": url, "bytes": target.stat().st_size, "md5": md5,
                             "sha256": digest(target, "sha256"), "downloaded_at": datetime.now(timezone.utc).isoformat()}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
            print(f"ok {key} {target.stat().st_size / 1e3:.0f} kB", flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path, help="output directory, e.g. data/raw/owid-catalog")
    parser.add_argument("paths", nargs="+", help="catalog table paths")
    args = parser.parse_args()
    manifest = download(args.out, args.paths)
    print(f"done: {len(manifest)} files in manifest")


if __name__ == "__main__":
    main()
