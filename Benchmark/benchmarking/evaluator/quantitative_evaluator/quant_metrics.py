"""Cell-level comparison of a result table with a figure's ground truth.

Solutions receive no output schema, so their columns are matched to the figure's by value, not by name:

0. a wide result (one column per year, e.g. "2000", "median_age_2023", or one column per entity, e.g. "China",
   "World (%)") is first unpivoted into one row per entity and year;
1. the entity column is the text column whose values (normalised, with OWID's entity-name mapping) cover the most
   gold entities; if there is none and the figure shows one entity, every row belongs to it;
2. the year column is the integer column whose values cover the most gold years; if there is none and the figure
   shows one year, every row belongs to it;
3. each gold value column is matched to the output column that reproduces the most of its (non-missing) cells,
   numerically within the tolerance or, for the columns the figure's spec declares categorical (coded values), up
   to a one-to-one relabelling (e.g. "before peak"/"peak"/"after peak" for -1/0/1). An output column may serve several
   gold columns: figures often split one series into columns by year (estimates and projections).
   Because no unit is specified, a column may be scaled as a whole by a power of ten (people or millions, percent or
   fraction); the scale used is reported, so that unit choices remain visible in the analysis.
4. a figure that shows only classes (a map coloured by whether a value is above or below a threshold) declares the
   threshold ("classes_at"); its cells are compared by class: the output value must fall on the same side, or a
   two-label output column must label the classes consistently.

A figure is correct when every non-missing gold cell is reproduced, every gold (entity, year) key is present, and no
key inside the figure's entities and year range is extra or duplicated. Rows for other entities are not penalised
(maps omit small territories; a query without a scope may return every country) but are counted
(`entities_outside_figure`), so that over-wide answers stay visible.
"""
import math
import re
from collections import Counter

import pandas as pd


def normalise_entity(name, mapping: dict[str, str]) -> str:
    text = " ".join(str(name).split())
    return mapping.get(text, text)


def _cell(value):
    """A gold cell for a mismatch record: a number, a text label as is (coded columns), or None."""
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def cells_match(expected, actual, tolerance: dict) -> bool:
    """Both missing, or both finite and |actual - expected| <= abs + rel * |expected|."""
    if pd.isna(expected):
        return bool(pd.isna(actual))
    if pd.isna(actual):
        return False
    try:
        expected, actual = float(expected), float(actual)
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(expected) and math.isfinite(actual)):
        return False
    return abs(actual - expected) <= tolerance.get("abs", 0.0) + tolerance.get("rel", 0.0) * abs(expected)


def _years(series: pd.Series) -> pd.Series:
    numbers = pd.to_numeric(series, errors="coerce")
    whole = numbers.notna() & (numbers == numbers.round()) & numbers.between(1000, 3000)
    return numbers.where(whole)


YEAR_IN_NAME = re.compile(r"(?<!\d)(1[89]\d\d|20\d\d|2100)(?!\d)")


def _entity_of_column(name: str, entities: set[str], mapping: dict[str, str]) -> str | None:
    """'World (%)' or 'China' -> the gold entity the column is about, if any."""
    base = re.sub(r"\s*\([^)]*\)\s*$", "", str(name)).strip()
    for candidate in (str(name), base):
        entity = normalise_entity(candidate, mapping)
        if entity in entities:
            return entity
    return None


def unpivot(gold: pd.DataFrame, output: pd.DataFrame, mapping: dict[str, str]) -> tuple[pd.DataFrame, str | None]:
    """Long form of a result that has one column per year or per entity; unchanged otherwise."""
    gold_years = set(gold["Year"].astype(int))
    by_year = {c: int(m.group(1)) for c in output.columns if (m := YEAR_IN_NAME.search(str(c)))
               and int(m.group(1)) in gold_years and pd.to_numeric(output[c], errors="coerce").notna().any()}
    if len(by_year) >= 2 or (by_year and len(gold_years) == 1):
        ids = [c for c in output.columns if c not in by_year]
        long = output.melt(id_vars=ids, value_vars=list(by_year), var_name="__column", value_name="value")
        long["year"] = long.pop("__column").map(by_year)
        return long, "columns per year"
    entities = set(gold["Entity"])
    by_entity = {c: e for c in output.columns if (e := _entity_of_column(c, entities, mapping))
                 and pd.to_numeric(output[c], errors="coerce").notna().any()}
    if len(by_entity) >= 2 or (by_entity and len(entities) == 1 and len(by_entity) == 1 and len(output.columns) > 2):
        ids = [c for c in output.columns if c not in by_entity]
        long = output.melt(id_vars=ids, value_vars=list(by_entity), var_name="__column", value_name="value")
        long["entity"] = long.pop("__column").map(by_entity)
        return long, "columns per entity"
    return output, None


YEAR_NAME = re.compile(r"(?i)year|yr|time|date|as[ _]of[ _]year")


def _one_year_key_candidates(output: pd.DataFrame, entity_column: str | None, scores: dict) -> dict:
    """For a figure that shows one year, an integer column is its year key only if it is named as a year or varies
    within an entity (a time series). A year that is an attribute of each entity (e.g. its peak year) is not."""
    kept = {}
    for column, score in scores.items():
        years = _years(output[column])
        if not years.notna().any():
            continue
        named = bool(YEAR_NAME.fullmatch(str(column).strip()))
        varies = (entity_column is not None
                  and (years.groupby(output[entity_column]).nunique(dropna=True) > 1).any())
        if named or varies:
            kept[column] = score
    return kept


def find_keys(gold: pd.DataFrame, output: pd.DataFrame, mapping: dict[str, str],
              unpivot_wide: bool = True) -> tuple[pd.DataFrame, dict]:
    """Output rows keyed by (Entity, Year), and which output columns (or constants) supplied the keys."""
    output, unpivoted = unpivot(gold, output, mapping) if unpivot_wide else (output, None)
    gold_entities, gold_years = set(gold["Entity"]), set(gold["Year"].astype(int))
    entity_scores = {c: len({normalise_entity(v, mapping) for v in output[c].dropna()} & gold_entities)
                     for c in output.columns if output[c].dtype == object}
    entity_column = max(entity_scores, key=entity_scores.get) if entity_scores and max(entity_scores.values()) else None
    year_scores = {c: len(set(_years(output[c]).dropna().astype(int)) & gold_years)
                   for c in output.columns if c != entity_column}
    if len(gold_years) == 1:
        year_scores = _one_year_key_candidates(output, entity_column, year_scores)
        named = [c for c in year_scores if YEAR_NAME.fullmatch(str(c).strip())]
        if named:  # a stated year is the key even when it is not the figure's year
            year_scores = {c: year_scores[c] + 1 for c in named}
    year_column = max(year_scores, key=year_scores.get) if year_scores and max(year_scores.values()) else None
    keyed = output.copy()
    alignment = {"entity": entity_column, "year": year_column, "unpivoted": unpivoted}
    if entity_column is not None:
        keyed["Entity"] = keyed[entity_column].map(lambda v: normalise_entity(v, mapping))
    elif len(gold_entities) == 1:
        keyed["Entity"], alignment["entity"] = next(iter(gold_entities)), "(constant: the figure's only entity)"
    else:
        keyed["Entity"] = None
    if year_column is not None:
        keyed["Year"] = _years(keyed[year_column])
    elif len(gold_years) == 1:
        keyed["Year"], alignment["year"] = next(iter(gold_years)), "(constant: the figure's only year)"
    else:
        keyed["Year"] = None
    keyed = keyed.dropna(subset=["Entity", "Year"]).astype({"Year": int})
    used = {entity_column, year_column}
    return keyed[["Entity", "Year", *[c for c in output.columns if c not in used and c not in ("Entity", "Year")]]], alignment


SCALES = [10.0 ** k for k in (0, 3, -3, 6, -6, 2, -2, 9, -9, 1, -1)]  # unscaled first: preferred on ties


def _numeric_hits(expected: pd.Series, actual: pd.Series, tolerance: dict,
                  scales: list[float] = SCALES) -> tuple[pd.Series, float]:
    """Cells reproduced numerically, and the power-of-ten scale (applied to the output) that reproduces the most."""
    numbers = pd.to_numeric(actual, errors="coerce")
    best_hits, best_scale = None, 1.0
    for scale in scales:
        hits = pd.Series([cells_match(e, a * scale, tolerance) for e, a in zip(expected, numbers)], index=expected.index)
        if best_hits is None or (hits & expected.notna()).sum() > (best_hits & expected.notna()).sum():
            best_hits, best_scale = hits, scale
    return best_hits, best_scale


def _categorical_hits(expected: pd.Series, actual: pd.Series) -> tuple[pd.Series, dict]:
    """Cells reproduced up to a one-to-one relabelling (the majority label for each gold value)."""
    pairs = Counter(zip(actual.astype(str), expected))
    labels: dict = {}
    for (label, value), _ in pairs.most_common():
        if label not in labels and value not in labels.values():
            labels[label] = value
    hits = pd.Series([labels.get(str(a)) == e for a, e in zip(actual, expected)], index=expected.index)
    return hits, labels


def _class_hits(expected: pd.Series, actual: pd.Series, threshold: float) -> tuple[pd.Series, float]:
    """Cells whose output value (at the best power-of-ten scale) is on the same side of the threshold as gold's."""
    numbers = pd.to_numeric(actual, errors="coerce")
    best_hits, best_scale = None, 1.0
    for scale in SCALES:
        hits = pd.Series([pd.notna(e) and pd.notna(a) and (a * scale > threshold) == (e > threshold)
                          for e, a in zip(expected, numbers)], index=expected.index)
        if best_hits is None or hits.sum() > best_hits.sum():
            best_hits, best_scale = hits, scale
    return best_hits, best_scale


def compare(gold: pd.DataFrame, output: pd.DataFrame, columns: list[str], tolerances: dict,
            mapping: dict[str, str] | None = None, categorical: frozenset[str] = frozenset(),
            rescale: bool = True, unpivot_wide: bool = True) -> dict:
    """`rescale` and `unpivot_wide` switch off rules 3 (power-of-ten scale) and 0 (wide results) for sensitivity
    analyses; the benchmark uses both."""
    keyed, alignment = find_keys(gold, output, mapping or {}, unpivot_wide)
    keys = ["Entity", "Year"]
    in_scope = keyed["Entity"].isin(set(gold["Entity"])) & keyed["Year"].between(gold["Year"].min(), gold["Year"].max())
    duplicates = int((keyed.duplicated(keys) & in_scope).sum())
    outside = int(keyed.loc[~keyed["Entity"].isin(set(gold["Entity"])), "Entity"].nunique())
    keyed = keyed.drop_duplicates(keys)
    candidates = [c for c in keyed.columns if c not in keys]
    merged = gold.merge(keyed.rename(columns={c: f"out::{c}" for c in candidates}), on=keys, how="left", indicator=True)
    present = merged["_merge"] == "both"
    matched = cells = 0
    mismatches, chosen = [], {}
    for column in columns:
        expected = merged[column]
        scored = expected.notna()
        if not scored.any():
            continue
        best, best_hits, how = None, pd.Series(False, index=expected.index), None
        for candidate in candidates:
            actual = merged[f"out::{candidate}"]
            threshold = tolerances[column].get("classes_at")
            if threshold is None:
                hits, scale = _numeric_hits(expected, actual, tolerances[column], SCALES if rescale else [1.0])
            else:
                hits, scale = _class_hits(expected, actual, threshold)
            hits &= present
            relabel = None
            if column in categorical or threshold is not None:
                target = expected if threshold is None else expected.map(
                    lambda v: v if pd.isna(v) else bool(v > threshold))
                relabelled, relabel = _categorical_hits(target[scored & present], actual[scored & present])
                relabelled = relabelled.reindex(expected.index, fill_value=False)
                if (relabelled & scored).sum() > (hits & scored).sum():
                    hits = relabelled
                else:
                    relabel = None
            if (hits & scored).sum() > (best_hits & scored).sum():
                best, best_hits = candidate, hits
                how = ({"relabel": {str(k): str(v) for k, v in relabel.items()}} if relabel
                       else {"numeric": True, "scale": scale} | ({"classes_at": threshold} if threshold is not None else {}))
        chosen[column] = {"output_column": best, "match": how}
        matched += int((best_hits & scored).sum())
        cells += int(scored.sum())
        for i in expected.index[scored & ~best_hits][: max(0, 20 - len(mismatches))]:
            row = merged.loc[i]
            actual = row.get(f"out::{best}") if best is not None and row["_merge"] == "both" else None
            mismatches.append({"entity": row["Entity"], "year": int(row["Year"]), "column": column,
                               "expected": _cell(row[column]),
                               "actual": None if actual is None or pd.isna(actual) else actual})
    in_scope = keyed["Entity"].isin(set(gold["Entity"])) & keyed["Year"].between(gold["Year"].min(), gold["Year"].max())
    extra = int((in_scope & ~keyed.set_index(keys).index.isin(gold.set_index(keys).index)).sum())
    return {"correct": cells > 0 and matched == cells and bool(present.all()) and extra == 0 and duplicates == 0,
            "cell_accuracy": matched / cells if cells else 0.0, "row_coverage": float(present.mean()) if len(gold) else 0.0,
            "matched_cells": matched, "gold_cells": cells, "gold_rows": len(gold), "extra_rows": extra,
            "duplicate_rows": duplicates, "entities_outside_figure": outside, "alignment": alignment | {"columns": chosen}, "mismatches": mismatches}
