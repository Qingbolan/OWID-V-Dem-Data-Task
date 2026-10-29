"""Benchmark datasets built from the article folders in OWID/.

A dataset (dataset/<name>/dataset.json) lists article folders: OWID articles, data insights and topic pages, and the
chart pages of charts no article shows (`<slug>-[chart]`, without article.md). Every figure whose golden program verified becomes
one Task: `match` (the program reproduces the figure) or `inputs_match` (the figure is computed by code that cannot
be included; the program reproduces its inputs and the figure data are captured from the page). Figures that are not
reproducible, or whose golden program has not been run or does not verify, are skipped and reported. The task never carries gold data into a solution's input (see Task.payload).
"""
import json
import re
from pathlib import Path

from ..utils.logger import get_logger
from ..utils.path import DATASET_ROOT, GOLDEN_FOLDER, OWID_ROOT, REPO_ROOT
from ..utils.struct import Task

logger = get_logger("OWIDDatasets")
VERIFIED = {"match", "inputs_match"}
FIGURE_MARKER = re.compile(r"\[FIG (\d{2}): [^\]]*\]")


def _figure_text(path: Path) -> dict:
    """Title and subtitle as published (glossary links removed)."""
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(": ")
        if key in ("Title", "Subtitle") and key.lower() not in fields:
            fields[key.lower()] = re.sub(r"\[([^\]]+)\]\(#dod:[^)]+\)", r"\1", value.strip())
    return fields


def _supplement(spec: dict) -> str:
    """Supplementary material given with every query: the output columns, in order, and their precision."""
    lines = ["Return one row per entity and year with these columns:", "- Entity", "- Year"]
    for column in spec.get("solution_columns", spec["columns"]):
        precision = spec.get("output_precision", {}).get(column)
        if precision == "text":
            lines.append(f"- {column} (text)")
        elif precision == 0:
            lines.append(f"- {column} (whole number)")
        elif precision is not None:
            lines.append(f"- {column} ({precision} decimal places)")
        else:
            lines.append(f"- {column}")
    return "\n".join(lines)


def _report_text(article_md: str, figure_index: int) -> str:
    """The report's prose with neutral figure placeholders; the requested figure is marked.

    article.md names figures with display names chosen for this repository (which state the view); those are not
    part of the report and are replaced by [Figure n]. The site's citation and licence boilerplate is dropped.
    """
    lines = article_md.splitlines()
    if lines and lines[0].startswith("Source: "):
        lines = lines[2:]
    if "### Cite this work" in lines:  # site boilerplate (citation, past versions, reuse licence) follows
        lines = lines[:lines.index("### Cite this work")]

    def placeholder(match):
        n = int(match.group(1))
        return f"[Figure {n}: the requested chart]" if n == figure_index else f"[Figure {n}]"
    return FIGURE_MARKER.sub(placeholder, "\n".join(lines)).strip()


class OWIDDatasets:
    """Collection of benchmark datasets (mirrors GemBench's GemDatasets)."""

    def __init__(self, data_set_names: list[str] | None = None, root: Path = DATASET_ROOT):
        self.root = root
        available = sorted(p.parent.name for p in root.glob("*/dataset.json"))
        self.data_set_names = data_set_names or available
        unknown = set(self.data_set_names) - set(available)
        if unknown:
            raise ValueError(f"Unknown datasets: {sorted(unknown)}; available: {available}")

    def get_all_data_set_names(self) -> list[str]:
        return sorted(p.parent.name for p in self.root.glob("*/dataset.json"))

    def get_data_set_names(self) -> list[str]:
        return list(self.data_set_names)

    def get_definition(self, name: str) -> dict:
        return json.loads((self.root / name / "dataset.json").read_text())

    def get_categories(self, name: str) -> dict[str, str]:
        path = self.root / name / "categories.json"
        return json.loads(path.read_text())["categories"] if path.exists() else {}

    def get_tasks(self, name: str) -> list[Task]:
        definition, categories, tasks = self.get_definition(name), self.get_categories(name), []
        variant = definition.get("variant")
        database = REPO_ROOT / definition["database"]
        verification_file = f"verification_{variant}.json" if variant else "verification.json"
        for folder_name in definition["articles"]:
            folder = OWID_ROOT / folder_name
            meta = json.loads((folder / "meta.json").read_text())
            # A chart page (no article shows the chart) has no article.md and no article-level input.
            article = (folder / "article.md").read_text(encoding="utf-8") if (folder / "article.md").exists() else ""
            for figure in meta["figures"]:
                figure_name = figure["name"]
                golden = folder / "figs" / figure_name / GOLDEN_FOLDER
                spec = json.loads((golden / "spec.json").read_text())
                # A figure computed in the browser has no variant program; its gold (captured data) is the same.
                checked = "verification.json" if spec.get("reproducible") == "inputs" else verification_file
                status = json.loads((golden / checked).read_text()).get("status") \
                    if (golden / checked).exists() else "not_run"
                if not spec.get("reproducible", True) or status not in VERIFIED:
                    logger.info("skip %s / %s (golden status: %s)", folder_name, figure_name, status)
                    continue
                gold_csv = folder / "figs" / f"{figure_name}.csv"
                text = _figure_text(folder / "figs" / f"{figure_name}.txt")
                tasks.append(Task(
                    task_id=f"{folder_name.split('-[')[0][:60]}__{figure_name[:2]}",
                    dataset=name, article_folder=folder, figure_name=figure_name,
                    category=categories.get(figure_name, "uncategorised"), title=text.get("title", figure_name),
                    subtitle=text.get("subtitle", ""),
                    article_text=_report_text(article, figure["index"]) if article else "",
                    output_columns=list(spec.get("solution_columns", spec["columns"])), gold_csv=gold_csv,
                    spec_path=golden / "spec.json", database=database, variant=variant,
                    image=(str((folder / figure["redaction"]["image"]).relative_to(REPO_ROOT))
                           if "redaction" in figure else None),
                    supplement=_supplement(spec)))
        return tasks

    def get_all_tasks(self) -> list[Task]:
        return [task for name in self.data_set_names for task in self.get_tasks(name)]
