"""Tasks are built only from verified figures and never expose gold data to solutions."""
import json

import pytest

from Benchmark.benchmarking import InputLevel, OWIDDatasets


@pytest.fixture(scope="module")
def tasks():
    return OWIDDatasets().get_all_tasks()


def test_only_verified_figures_become_tasks(tasks):
    assert tasks, "run `make golden` before the tests"
    for task in tasks:
        verification = json.loads((task.spec_path.parent / "verification.json").read_text())
        assert verification["status"] in {"match", "inputs_match"}


@pytest.mark.parametrize("level", list(InputLevel))
def test_payload_contains_no_gold(tasks, level):
    for task in (t for t in tasks if t.supports(level)):
        text = json.dumps(task.payload(level))
        gold = task.gold_csv.read_text()
        assert str(task.gold_csv) not in text and "golden-processing" not in text
        assert gold.splitlines()[1] not in text  # no data row of the figure CSV
        assert ("The chart appears in this report" in text) == level.value.endswith("article")
        if "image" in task.payload(level):
            assert task.payload(level)["image"].endswith(".redacted.png")


def test_inputs_are_one_query_with_the_supplement(tasks):
    for task in tasks:
        for level in (level for level in InputLevel if task.supports(level)):
            payload = task.payload(level)
            assert set(payload) <= {"query", "image"} and payload["query"].startswith(task.title)
            assert ("image" in payload) == level.value.startswith("image")
            assert payload["query"].endswith(task.supplement)
        assert task.payload(InputLevel.TITLE)["query"] == f"{task.title}\n\nSupplementary material:\n{task.supplement}"
        if task.supports(InputLevel.ARTICLE):
            article = task.payload(InputLevel.ARTICLE)["query"]
            assert "the requested chart]" in article and "[FIG" not in article and task.figure_name not in article


def test_supplement_names_every_scored_column_with_its_precision(tasks):
    for task in tasks:
        lines = task.supplement.splitlines()
        assert lines[1:3] == ["- Entity", "- Year"]
        assert [line[2:].rsplit(" (", 1)[0] for line in lines[3:]] == task.output_columns
        assert all(line.endswith(("decimal places)", "(whole number)", "(text)")) for line in lines[3:])


def test_unsupported_levels_are_refused_not_degraded(tasks):
    without_page = [t for t in tasks if not t.supports(InputLevel.ARTICLE)]
    assert without_page and len(without_page) < len(tasks)
    with pytest.raises(ValueError):
        without_page[0].payload(InputLevel.ARTICLE)


def test_last_sql_statement_is_read_from_prose():
    from Benchmark.benchmarking.OWIDBench import last_sql_statement
    assert last_sql_statement("I found the data.\n\nSELECT a FROM t;") == "SELECT a FROM t"
    assert last_sql_statement("Here:\n```sql\nWITH x AS (SELECT 1) SELECT * FROM x\n```") == "WITH x AS (SELECT 1) SELECT * FROM x"
    assert last_sql_statement("I cannot produce this chart from the data.") is None
    prose = "The data covers every year, with no gaps.\n\nWITH x AS (SELECT 1 AS a)\nSELECT a FROM x"
    assert last_sql_statement(prose) == "WITH x AS (SELECT 1 AS a)\nSELECT a FROM x"
    spaced = "Here is the query.\n\nWITH a AS (\n  SELECT 1 AS v\n),\n\nb AS (SELECT v FROM a)\n\nSELECT v FROM b;"
    notes_after = "SELECT a\nFROM t\n\n- **Counts:** in thousands.\n- **Togo:** uses the update."
    assert last_sql_statement(notes_after) == "SELECT a\nFROM t"
    assert last_sql_statement(spaced) == "WITH a AS (\n  SELECT 1 AS v\n),\n\nb AS (SELECT v FROM a)\n\nSELECT v FROM b"
