"""Download OWID ETL snapshot files from the public snapshot store and verify them.

    python -m pipeline.download_snapshots <etl_repo> <out_dir> <namespace/version> [...]

Each file is fetched from https://snapshots.owid.io/<md5[:2]>/<md5[2:]>, i.e. the exact bytes OWID's ETL uses, and
checked against the MD5 in the ETL `.dvc` file. Files are stored as <out_dir>/<namespace/version>/<file> next to a
copy of their `.dvc`. A manifest records URL, size, MD5, SHA-256 and producer metadata. Files already verified are
left untouched, so re-running is a no-op.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

STORE = "https://snapshots.owid.io"
USER_AGENT = "OWID-VDem-Data-Task/0.1 (research)"


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, target: Path, md5: str) -> None:
    partial = target.with_suffix(target.suffix + ".part")
    with requests.get(url, stream=True, timeout=120, headers={"User-Agent": USER_AGENT}) as response:
        response.raise_for_status()
        with open(partial, "wb") as f:
            for chunk in response.iter_content(1 << 20):
                f.write(chunk)
    if digest(partial, "md5") != md5:
        partial.unlink()
        raise ValueError(f"MD5 mismatch for {target}")
    partial.replace(target)


def download(etl: Path, out: Path, groups: list[str]) -> dict:
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for group in groups:
        for dvc in sorted((etl / "snapshots" / group).glob("*.dvc")):
            meta = yaml.safe_load(dvc.read_text()) or {}
            md5 = (meta.get("outs") or [{}])[0].get("md5")
            name, key = dvc.name[: -len(".dvc")], f"{group}/{dvc.name[: -len('.dvc')]}"
            target = out / group / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(dvc, target.parent / dvc.name)
            if key in manifest and target.exists() and digest(target, "md5") == md5:
                print(f"ok {key} (already verified)", flush=True)
                continue
            url = f"{STORE}/{md5[:2]}/{md5[2:]}"
            if not (target.exists() and digest(target, "md5") == md5):
                fetch(url, target, md5)
            origin = (meta.get("meta") or {}).get("origin") or {}
            manifest[key] = {"url": url, "bytes": target.stat().st_size, "md5": md5, "sha256": digest(target, "sha256"),
                             "producer": origin.get("producer"), "title": origin.get("title"),
                             "date_published": str(origin.get("date_published") or ""),
                             "url_download_producer": origin.get("url_download"),
                             "downloaded_at": datetime.now(timezone.utc).isoformat()}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
            print(f"ok {key} {target.stat().st_size / 1e6:.1f} MB", flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("etl", type=Path, help="local clone of github.com/owid/etl")
    parser.add_argument("out", type=Path, help="output directory, e.g. data/raw/owid-snapshots")
    parser.add_argument("groups", nargs="+", help="snapshot groups, e.g. un/2024-07-12")
    args = parser.parse_args()
    manifest = download(args.etl, args.out, args.groups)
    print(f"done: {len(manifest)} files in manifest")


if __name__ == "__main__":
    main()
