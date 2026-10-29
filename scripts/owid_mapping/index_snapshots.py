"""Index the raw data OWID added to its ETL in a period, with each group's downstream ETL steps.

    python -m scripts.owid_mapping.index_snapshots <etl_repo> <out.json> [--since 2026-01-01]

1. Snapshot files added since --since: `git log --diff-filter=A` over `snapshots/**/*.dvc`, grouped by
   `<namespace>/<version>`. Producer, title, publication date, citation and size come from each `.dvc`; the
   addition date is the first commit that added the file.
2. Downstream steps: `dag/**/*.yml` parsed into a dependency graph. Dependency lists may nest steps inline
   (`- step: [its dependencies]`) and use `-private` URIs (`data-private://`, `snapshot-private://`); both are
   normalised. For each group the transitive dependants are collected and split into grapher datasets
   (`data://grapher/...`) and exports/visualisations (`export://`, `viz://`).
"""
import argparse
import collections
import json
import re
import subprocess
from pathlib import Path

import yaml

PRIVATE = re.compile(r"^([a-z]+)-private://")


def normalise(step: str) -> str:
    return PRIVATE.sub(r"\1://", step)


def added_snapshots(etl: Path, since: str) -> dict[str, str]:
    """Snapshot .dvc path -> date of the first commit that added it (since `since`)."""
    log = subprocess.run(["git", "-C", str(etl), "log", f"--since={since}", "--diff-filter=A", "--format=@@%cs",
                          "--name-only", "--", "snapshots/"], capture_output=True, text=True, check=True).stdout
    added, date = {}, None
    for line in log.splitlines():
        if line.startswith("@@"):
            date = line[2:]
        elif line.endswith(".dvc"):
            added[line] = date  # log is newest first, so the last assignment is the earliest commit
    return added


def dependency_graph(etl: Path) -> dict[str, set[str]]:
    deps: dict[str, list[str]] = {}

    def add(step, values):
        step = normalise(step)
        deps.setdefault(step, [])
        for value in values or []:
            if isinstance(value, str):
                deps[step].append(normalise(value))
            elif isinstance(value, dict):
                for nested, nested_values in value.items():
                    deps[step].append(normalise(nested))
                    add(nested, nested_values)

    for path in (etl / "dag").rglob("*.yml"):
        data = yaml.safe_load(path.read_text()) or {}
        for step, values in ((data.get("steps") if isinstance(data, dict) else None) or {}).items():
            add(step, values)
    children: dict[str, set[str]] = collections.defaultdict(set)
    for step, values in deps.items():
        for value in values:
            children[value].add(step)
    return children


def downstream(children: dict[str, set[str]], start: str) -> set[str]:
    seen, stack = set(), [start]
    while stack:
        for child in children.get(stack.pop(), ()):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def index(etl: Path, since: str) -> list[dict]:
    added = added_snapshots(etl, since)
    children = dependency_graph(etl)
    groups: dict[str, dict] = collections.defaultdict(lambda: {"files": [], "bytes": 0, "producers": set(), "titles": set(),
                                                                "date_published": set(), "added": set(), "citations": set()})
    for path, date in added.items():
        file = etl / path
        if not file.exists():  # added and later removed
            continue
        meta = yaml.safe_load(file.read_text()) or {}
        info = meta.get("meta") or {}
        origin = info.get("origin") or info
        group = "/".join(path.split("/")[1:3])
        g = groups[group]
        g["files"].append(path[len("snapshots/"):-len(".dvc")])
        g["bytes"] += sum(out.get("size") or 0 for out in meta.get("outs") or [])
        g["producers"].add(str(origin.get("producer") or ""))
        g["titles"].add(str(origin.get("title") or ""))
        g["date_published"].add(str(origin.get("date_published") or ""))
        g["citations"].add(" ".join(str(origin.get("citation_full") or "").split()))
        g["added"].add(date or "")
    rows = []
    for group, g in groups.items():
        steps = set()
        for snapshot in g["files"]:
            steps |= downstream(children, f"snapshot://{snapshot}")
        rows.append({
            "group": group, "files": sorted(g["files"]), "megabytes": round(g["bytes"] / 1e6, 1),
            "producers": sorted(p for p in g["producers"] if p), "titles": sorted(t for t in g["titles"] if t),
            "date_published": sorted(d for d in g["date_published"] if d), "added_to_repo": min(d for d in g["added"] if d),
            "citations": sorted(c for c in g["citations"] if c), "downstream_steps": len(steps),
            "grapher_datasets": sorted(s for s in steps if s.startswith("data://grapher/")),
            "exports": sorted(s for s in steps if s.startswith(("export://", "viz://")))})
    return sorted(rows, key=lambda r: (-len(r["grapher_datasets"]), r["group"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("etl", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--since", default="2026-01-01")
    args = parser.parse_args()
    rows = index(args.etl, args.since)
    commit = subprocess.run(["git", "-C", str(args.etl), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"etl_commit": commit, "since": args.since, "groups": rows}, ensure_ascii=False, indent=1))
    print(f"{len(rows)} groups, {sum(len(r['files']) for r in rows)} files, etl {commit[:9]}")


if __name__ == "__main__":
    main()
