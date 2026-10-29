"""Results are compared with the figure by value: columns are matched without names, keys and tolerances apply."""
import pandas as pd

from Benchmark.benchmarking.evaluator.quantitative_evaluator.quant_metrics import cells_match, compare

GOLD = pd.DataFrame({"Entity": ["A", "A", "B"], "Year": [2000, 2001, 2000], "v": [100.0, 50.0, 5.0]})
TOL = {"v": {"rel": 0.01}}


def test_cells_match():
    assert cells_match(100, 100.9, {"rel": 0.01}) and not cells_match(100, 101.1, {"rel": 0.01})
    assert cells_match(None, None, {}) and not cells_match(None, 0.0, {}) and not cells_match(1.0, None, {})
    assert not cells_match(1.0, "1.0x", {"abs": 1})


def test_columns_are_matched_by_value_not_name():
    output = pd.DataFrame({"country": ["B", "A", "A"], "yr": [2000, 2001, 2000], "noise": [1, 2, 3],
                           "value_pct": [5.0, 50.2, 100.0]})
    result = compare(GOLD, output, ["v"], TOL)
    assert result["correct"]
    assert result["alignment"]["entity"] == "country" and result["alignment"]["columns"]["v"]["output_column"] == "value_pct"


def test_entity_names_are_mapped():
    output = pd.DataFrame({"name": ["Alpha", "Alpha", "B"], "year": [2000, 2001, 2000], "x": [100.0, 50.0, 5.0]})
    assert compare(GOLD, output, ["v"], TOL, {"Alpha": "A"})["correct"]


def test_one_output_column_can_serve_split_gold_columns():
    gold = pd.DataFrame({"Entity": ["A", "A"], "Year": [2023, 2024], "est": [1.0, None], "proj": [None, 2.0]})
    output = pd.DataFrame({"year": [2023, 2024], "population": [1.0, 2.0]})  # single entity: no entity column needed
    tol = {"est": {"abs": 0}, "proj": {"abs": 0}}
    assert compare(gold, output, ["est", "proj"], tol)["correct"]


def test_categorical_columns_match_up_to_relabelling():
    gold = pd.DataFrame({"Entity": list("ABC"), "Year": [2026] * 3, "code": [-1, 0, 1]})
    output = pd.DataFrame({"country": list("ABC"), "status": ["before peak", "peak", "after peak"]})
    result = compare(gold, output, ["code"], {"code": {"abs": 0}}, categorical=frozenset({"code"}))
    assert result["correct"] and result["alignment"]["year"].startswith("(constant")
    inconsistent = output.assign(status=["before", "before", "after"])
    assert not compare(gold, inconsistent, ["code"], {"code": {"abs": 0}}, categorical=frozenset({"code"}))["correct"]
    assert not compare(gold, output, ["code"], {"code": {"abs": 0}})["correct"]  # not declared categorical


def test_extra_rows_inside_scope_fail_but_outside_scope_are_ignored():
    inside = pd.concat([GOLD, pd.DataFrame({"Entity": ["B"], "Year": [2001], "v": [6.0]})])
    outside = pd.concat([GOLD, pd.DataFrame({"Entity": ["C"], "Year": [2000], "v": [1.0]})])
    assert compare(GOLD, inside, ["v"], TOL)["extra_rows"] == 1
    assert compare(GOLD, outside, ["v"], TOL)["correct"]


def test_duplicates_missing_rows_and_wrong_values_fail():
    assert not compare(GOLD, pd.concat([GOLD, GOLD.iloc[[0]]]), ["v"], TOL)["correct"]
    result = compare(GOLD, GOLD.iloc[:2], ["v"], TOL)
    assert not result["correct"] and result["row_coverage"] == 2 / 3
    assert not compare(GOLD, GOLD.assign(v=GOLD["v"] * 1.5), ["v"], TOL)["correct"]


def test_power_of_ten_rescaling_is_accepted_and_reported():
    result = compare(GOLD, GOLD.assign(v=GOLD["v"] / 1e6), ["v"], TOL)  # e.g. people reported in millions
    assert result["correct"] and result["alignment"]["columns"]["v"]["match"]["scale"] == 1e6


def test_figures_showing_classes_are_compared_by_class():
    gold = pd.DataFrame({"Entity": list("ABC"), "Year": [2023] * 3, "rate": [-0.4, 0.2, 1.5]})
    tol = {"rate": {"abs": 1e-4, "classes_at": 0}}
    absolute = pd.DataFrame({"country": list("ABC"), "change": [-5000, 120, 90000]})  # same signs, other measure
    labels = pd.DataFrame({"country": list("ABC"), "status": ["shrinking", "growing", "growing"]})
    wrong = pd.DataFrame({"country": list("ABC"), "change": [-5000, -120, 90000]})
    assert compare(gold, absolute, ["rate"], tol)["correct"]
    assert compare(gold, labels, ["rate"], tol)["correct"]
    assert not compare(gold, wrong, ["rate"], tol)["correct"]


def test_duplicates_outside_the_figure_are_ignored_but_counted():
    other = pd.DataFrame({"Entity": ["Z", "Z"], "Year": [2000, 2000], "v": [1.0, 1.0]})
    result = compare(GOLD, pd.concat([GOLD, other]), ["v"], TOL)
    assert result["correct"] and result["duplicate_rows"] == 0 and result["entities_outside_figure"] == 1


def test_wide_results_are_unpivoted():
    gold = pd.DataFrame({"Entity": ["A", "A", "B", "B"], "Year": [2000, 2023] * 2, "v": [1.0, 2.0, 3.0, 4.0]})
    per_year = pd.DataFrame({"region": ["A", "B"], "median_2000": [1.0, 3.0], "median_2023": [2.0, 4.0]})
    per_entity = pd.DataFrame({"year": [2000, 2023], "A (%)": [1.0, 2.0], "B": [3.0, 4.0]})
    for wide in (per_year, per_entity):
        result = compare(gold, wide, ["v"], {"v": {"abs": 1e-9}})
        assert result["correct"] and result["alignment"]["unpivoted"]


def test_values_written_into_the_sql_are_detected():
    from Benchmark.benchmarking.evaluator.quantitative_evaluator.quant_evaluator import hardcoded_cells
    gold = pd.DataFrame({"Entity": ["A", "A", "B"], "Year": [2000, 2001, 2000], "v": [33.6, 21.7, 5.25]})
    copied = "SELECT 'A' AS e, 2000 AS y, 33.6 AS v UNION ALL SELECT 'A', 2001, 21.7 UNION ALL SELECT 'B', 2000, 5.25"
    computed = "SELECT Location, Time, SUM(Births) * 1000 / 2.5 FROM t WHERE Time BETWEEN 1950 AND 2023 GROUP BY 1, 2"
    assert hardcoded_cells(copied, gold, ["v"], {}) == 3
    assert hardcoded_cells(computed, gold, ["v"], {}) == 0


def test_an_attribute_year_is_not_taken_as_the_key_of_a_one_year_figure():
    gold = pd.DataFrame({"Entity": list("ABC"), "Year": [2026] * 3, "code": [-1, 0, 1]})
    output = pd.DataFrame({"country": list("ABC"), "peak_year": [2100, 2026, 2010],
                           "status": ["before peak", "peak", "after peak"]})
    result = compare(gold, output, ["code"], {"code": {"abs": 0}}, categorical=frozenset({"code"}))
    assert result["correct"] and result["alignment"]["year"].startswith("(constant")
    stated = output.assign(year=2024)  # a stated year other than the figure's is still the key, and wrong
    assert not compare(gold, stated, ["code"], {"code": {"abs": 0}}, categorical=frozenset({"code"}))["correct"]
    series = pd.DataFrame({"country": list("AABBCC"), "yr": [2025, 2026] * 3,
                           "status": ["before peak"] * 2 + ["before peak", "peak", "after peak", "after peak"]})
    assert compare(gold, series, ["code"], {"code": {"abs": 0}}, categorical=frozenset({"code"}))["correct"]
