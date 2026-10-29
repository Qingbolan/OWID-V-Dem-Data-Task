"""Write each figure's golden-program spec: which column of OWID's V-Dem tables every figure column plots, and how
the chart's view turns those values into the figure's.

    python -m scripts.write_golden_specs <OWID root> [--tables data/golden/vdem]

For figs/<figure>/golden-processing-program-files/ of every figure of every folder (articles, data insights, chart
pages), writes spec.json and README.md. A figure is not reproducible when it has no data series (a static image; the
reason recorded in the figure list, scripts/articles/<slug>.json, is used when there is one) or when its chart is not
one of the V-Dem-only charts (data/reference/charts.json; the datasets it also plots are named). A data insight
whose image shows only some columns of its view lists them in the figure's scope ("columns"); only those are used.

Sources. A figure column is resolved from its OWID short name (meta.json "column_short_names"). OWID's grapher names
a column of a table with dimensions `<column>__<underscore(dimension + "_" + value)>` (e.g.
`num_countries_regime__category_closed_autocracy`, `population_regime__category__1` for category -1), and a column
without dimensions by its name. `underscore` is OWID's function (owid.catalog), ported below for ASCII text.
OWID's region column (`owid_region`, which colours maps and scatter plots) is not a V-Dem indicator and is not
compared. A figure with a column that resolves to no table is marked not reproducible, with the reason.

View. Three settings of the chart turn table values into what the figure shows, all read from the chart's config and
indicator metadata (never from the figure data):
- "scale": the indicator's display conversion factor (e.g. a share stored in % and shown as a fraction);
- "stack_relative": a stacked chart in relative mode shows each column as a percentage of the row's total;
- "time_tolerance": a map shows, for each entity, the value of the closest year within the map's tolerance; the
  figure's "(Original Year)" column (short name `<column>__original_year`) is the year that value comes from, left
  empty when it is the year shown ("original_year_of").

Tolerance: one unit in the last decimal place the published CSV prints for the column, or 1e-6 relative (OWID
publishes some values as 32-bit floats); text columns must be equal. Text columns and indicators OWID types as
ordinal or categorical (regime codes) are listed under "encodings", which the evaluator compares up to a one-to-one
relabelling.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

import pandas as pd

FOLDER = "golden-processing-program-files"
AUXILIARY = {"owid_region": "OWID's world region (map and scatter colour), not a V-Dem indicator"}
ORIGINAL_YEAR = "__original_year"
STACKED = {"stackedarea", "stackedbar", "stackeddiscretebar"}  # grapher chart types that stack columns
# V-Dem country names -> OWID entity names, used by the evaluator to read a solution's entity column
ENTITY_MAPPING = "data/reference/owid_etl/vdem/vdem.countries.json"
KEYS = {"country", "year"}


def underscore(name: str) -> str:
    """owid.catalog.core.utils.underscore (owid/etl commit in data/reference/owid_etl/PROVENANCE.json), ASCII input."""
    name = name.lower()
    for old, new in ((" ", "_"), ("-", "_"), (",", "_"), (".", "_"), ("\t", "_"), ("?", "_"), ("!", "_"), ('"', ""),
                     ("'", ""), ("\xa0", "_"), ("`", ""), ("*", "_"), ("#", ""), ("^", ""), ("(", "__"), (")", "__"),
                     (":", "__"), (";", "__"), ("[", "__"), ("]", "__"), ("/", "_"), ("|", "_"), ("=", "_"),
                     ("%", "pct"), ("+", "plus"), ("us$", "usd"), ("$", "dollar"), ("&", "_and_"), ("<", "_lt_"),
                     (">", "_gt_")):
        name = name.replace(old, new)
    name = re.sub("__+", "__", name).strip("_")
    return f"_{name}" if re.match("^[0-9]", name) else name


def load_tables(root: Path) -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_feather(p) for p in sorted(root.glob("*.feather"))}


def resolve(short: str, tables: dict[str, pd.DataFrame]) -> dict | None:
    base, _, rest = short.partition("__")
    for name, frame in tables.items():
        if base not in frame.columns:
            continue
        if not rest:
            return {"table": name, "column": base, "filter": {}}
        dimensions = [c for c in frame.columns if c not in KEYS and frame[c].dtype == object and c != base]
        for dimension in dimensions:
            values = [v for v in frame[dimension].dropna().unique() if underscore(f"{dimension}_{v}") == rest]
            if len(values) == 1:
                return {"table": name, "column": base, "filter": {dimension: values[0]}}
    return None


def decimals(series: pd.Series) -> int:
    text = series.dropna().astype(str)
    return int(text.map(lambda v: len(v.split(".")[1]) if "." in v and "e" not in v.lower() else 0).max() or 0)


def view_settings(record: dict, config: dict) -> dict:
    """Tab, stack mode and map tolerance of the view (the view's query string overrides the chart's defaults)."""
    query = dict(parse_qsl(urlparse(record["view_url"]).query))
    tab = query.get("tab") or config.get("tab") or "chart"
    stack = query.get("stackMode") or config.get("stackMode") or "absolute"
    # A stack mode in the query only matters for stacked chart types; a line or bar view ignores it.
    kind = (config.get("chartTypes") or ["LineChart"])[0] if tab == "chart" else tab
    stacked = kind.replace("-", "").lower() in STACKED
    tolerance = (config.get("map") or {}).get("timeTolerance", 0) if tab == "map" else 0
    return {"tab": tab, "stack_relative": stacked and stack == "relative", "time_tolerance": int(tolerance or 0)}


def not_reproducible(record: dict, reason: str) -> dict:
    return {"reproducible": False, "reason": reason, "view": record.get("view_url"), "chart_slug": record.get("chart_slug")}


def spec_for(folder: Path, record: dict, tables: dict[str, pd.DataFrame], vdem: set[str], datasets: dict,
             notes: dict) -> tuple[Path, dict]:
    figure = folder / "figs" / record["name"]
    if not record.get("view_url"):
        return figure / FOLDER, not_reproducible(record, notes.get(record["name"]) or "static image without a data series")
    if record["chart_slug"] not in vdem:
        other = [d for d in datasets.get(record["chart_slug"], []) if "democracy/2026-03-17/vdem" not in d]
        reason = "the chart is not one of the V-Dem-only charts (data/reference/charts.json)"
        return figure / FOLDER, not_reproducible(record, reason + (": it plots " + ", ".join(other) if other else ""))
    gold = pd.read_csv(folder / record["files"]["csv"]["path"], dtype=str, keep_default_na=False, na_values=[""])
    shown = (record.get("scope") or {}).get("columns")  # a static image may show only some columns of its view
    shorts = record["column_short_names"]
    config = json.loads((figure / "chart.config.json").read_text())
    indicators = {c.get("shortName"): c for c in json.loads((figure / "chart.metadata.json").read_text())
                  .get("columns", {}).values()}
    by_short = {short: column for column, short in shorts.items()}
    view = view_settings(record, config)
    columns, sources, compare, encodings, scale, original_years, auxiliary, unresolved = [], {}, {}, {}, {}, {}, {}, []
    for position, column in enumerate(gold.columns):
        if column in ("Entity", "Code", "Year", "Day") or (shown and column not in shown):
            continue
        short = shorts.get(column, column)
        if short in AUXILIARY:
            auxiliary[column] = AUXILIARY[short]
            continue
        if short.endswith(ORIGINAL_YEAR) and by_short.get(short[: -len(ORIGINAL_YEAR)]):
            columns.append(column)
            original_years[column] = by_short[short[: -len(ORIGINAL_YEAR)]]
            compare[column] = {"abs": 0.0}
            sources[column] = {"original_year_of": original_years[column], "short_name": short, "gold_index": position}
            continue
        source = resolve(short, tables)
        if source is None:
            unresolved.append(f"{column} ({short})")
            continue
        columns.append(column)
        sources[column] = dict(source, short_name=short, gold_index=position)
        factor = (indicators.get(short) or {}).get("conversionFactor")
        if factor not in (None, 1):
            scale[column] = factor
        values = pd.to_numeric(gold[column], errors="coerce")
        if values.notna().sum() == gold[column].notna().sum():
            compare[column] = {"abs": 10.0 ** -decimals(gold[column]), "rel": 1e-6}
        else:
            compare[column] = {"equal": True}
        kind = (indicators.get(short) or {}).get("type")
        if compare[column].get("equal") or kind in ("Ordinal", "Categorical"):
            labels = sorted(gold[column].dropna().unique())
            encodings[column] = f"{kind or 'text'} values: " + ", ".join(labels[:20])
    spec = {"reproducible": not unresolved and bool(columns), "program": "golden.vdem_pipeline",
            "chart_slug": record["chart_slug"], "view": record["view_url"], "columns": columns,
            # A solution is scored on the indicator values; the map's "(Original Year)" column only annotates them.
            "solution_columns": [c for c in columns if c not in original_years],
            # Given to solutions as supplementary material: the decimal places OWID prints, or "text"
            "output_precision": {c: ("text" if compare[c].get("equal") else decimals(gold[c]))
                                 for c in columns if c not in original_years},
            "sources": sources,
            "gold_column_index": {c: s["gold_index"] for c, s in sources.items()},
            "entity_mapping": ENTITY_MAPPING, "compare": compare, "encodings": encodings, "scale": scale,
            "stack_relative": view["stack_relative"], "time_tolerance": view["time_tolerance"],
            "not_compared": auxiliary}
    if unresolved:
        spec["reason"] = "figure columns not in OWID's V-Dem output tables: " + ", ".join(unresolved)
    elif not columns:
        spec["reason"] = "no V-Dem indicator among the figure columns"
    return figure / FOLDER, spec


def readme(name: str, spec: dict) -> str:
    if not spec["reproducible"] and "sources" not in spec:
        return (f"# Golden processing program: {name}\n\nView: {spec['view'] or 'none'}\n\n"
                f"Not reproducible: {spec['reason']}\n")
    lines = [f"# Golden processing program: {name}", "", f"View: {spec['view']}", "",
             "## How OWID computes it",
             "OWID's V-Dem step (data/reference/owid_etl/vdem/, owid/etl commit in PROVENANCE.json) is run on the "
             "benchmark database by `golden.vdem_pipeline` (shared by every chart); this figure reads:", ""]
    for column, source in spec["sources"].items():
        if "original_year_of" in source:
            lines.append(f"- `{column}`: the year the value of `{source['original_year_of']}` comes from (map tolerance)")
            continue
        where = ", ".join(f"{k} = '{v}'" for k, v in source["filter"].items())
        line = f"- `{column}`: table `{source['table']}`, column `{source['column']}`" + (f", rows where {where}" if where else "")
        if column in spec["scale"]:
            line += f", multiplied by {spec['scale'][column]} (display conversion)"
        lines.append(line)
    for column, why in spec["not_compared"].items():
        lines.append(f"- `{column}`: not compared ({why})")
    if spec["stack_relative"]:
        lines.append("- The chart stacks the columns in relative mode: each value is shown as a percentage of the row total.")
    if spec["time_tolerance"]:
        lines.append(f"- The map shows, per entity, the value of the closest year within {spec['time_tolerance']} years.")
    if not spec["reproducible"]:
        lines += ["", f"Not reproducible: {spec['reason']}"]
    lines += ["", "## Files", "- `spec.json`; `expected_output.csv` and `verification.json` are written by `make golden`."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--tables", type=Path, default=Path("data/golden/vdem"))
    parser.add_argument("--charts", type=Path, default=Path("data/reference/charts.json"))
    parser.add_argument("--crawl", type=Path, default=Path("docs/owid-mapping/crawl.json"))
    parser.add_argument("--figure-lists", type=Path, default=Path("scripts/articles"))
    args = parser.parse_args()
    tables = load_tables(args.tables)
    vdem = {c["slug"] for c in json.loads(args.charts.read_text())["charts"]}
    crawl = json.loads(args.crawl.read_text())
    datasets = {slug: sorted({crawl["indicators"][str(i)]["dataset"] for i in ids if str(i) in crawl["indicators"]})
                for slug, ids in crawl["chart_indicators"].items()}
    notes = {}  # reasons recorded by hand in the figure lists (e.g. data insights whose image is not V-Dem data)
    for path in args.figure_lists.glob("*.json"):
        notes.update(json.loads(path.read_text()).get("not_reproducible", {}))
    counts = {True: 0, False: 0}
    for meta in sorted(args.root.glob("*/meta.json")):
        for record in json.loads(meta.read_text())["figures"]:
            target, spec = spec_for(meta.parent, record, tables, vdem, datasets, notes)
            target.mkdir(parents=True, exist_ok=True)
            (target / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1))
            (target / "README.md").write_text(readme(target.parent.name, spec), encoding="utf-8")
            counts[spec["reproducible"]] += 1
    print(f"{counts[True]} figures reproducible, {counts[False]} not")


if __name__ == "__main__":
    main()
