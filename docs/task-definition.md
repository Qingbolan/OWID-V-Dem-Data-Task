# Task definition

## Research question

Can a general-purpose agent with read-only SQL access to raw upstream data produce the data behind a published figure,
given a natural-language request? Where it fails, is the failure caused by an underspecified request, by the
publisher's processing conventions, or by query construction?

## Unit of evaluation

One **figure** of one folder in `OWID/`: a figure of an OWID page (topic page, article, data insight), or the default
view of a chart no page shows (its chart page, `<slug>-[chart]`;
[decision 0005](decisions/0005-chart-selection-and-host-pages.md)). A figure is scored when its golden program
reproduces OWID's published data for that view from `data/sqlite/vdem2026.db` (`verification.json` status `match`);
all 124 V-Dem figures do.

## Inputs (graded)

The input is one natural-language query, as a person describing the chart they need would write it, followed by
supplementary material: the output columns and their precision
([decision 0006](decisions/0006-output-columns-as-supplementary-material.md)). No entity or year list is given.

| Level | The query is | Tasks |
|---|---|---:|
| `title` | the chart title | 124 |
| `subtitle` | the chart title and its subtitle | 124 |
| `article` | the title, the subtitle and the full text of the page (figures shown as `[Figure n]`, the requested one marked), without the chart's own notes, units or source | 43 |

The supplementary material, appended at every level:

```
Supplementary material:
Return one row per entity and year with these columns:
- Entity
- Year
- <figure column> (<n> decimal places | whole number | text)
...
```

The columns are the figure's own column names, in the published order (spec `solution_columns`); the precision is the
number of decimal places OWID prints (spec `output_precision`). For a data insight, the title and subtitle are those
printed on the image. A chart page has no article level; image levels need redacted images, which this repository
does not have yet. The harness skips unsupported levels (`Task.supports`); `--richest` runs only the last given
level a task supports.

The agent always receives read-only access to the database through one SQL tool. It never receives the figure CSV,
the image, the golden program, OWID's processed data or OWID's code.

## Output

One read-only SQLite `SELECT` per task. The harness executes it and stores the result.

## Correctness

The result's columns are matched to the figure's by value
(`Benchmark/benchmarking/evaluator/quantitative_evaluator/quant_metrics.py`), whatever their names:

- the entity column is the text column covering the most figure entities after OWID's V-Dem-to-OWID name mapping
  (`data/reference/owid_etl/vdem/vdem.countries.json`); the year column the integer column covering the most figure
  years; either may be absent when the figure shows a single entity or year;
- each figure column (a map's "(Original Year)" column is not asked for) is matched to the result column that
  reproduces most of its cells within 1 % relative (or the golden tolerance, if larger); coded and text columns
  (regime categories, spec `encodings`) may use any one-to-one labelling;
- a figure is correct when every non-missing figure cell is reproduced, every figure (entity, year) key is present, no
  key is duplicated and no extra row falls inside the figure's entities and year range. Rows for other entities or
  years are not penalised but counted (`entities_outside_figure`).

## Protocol

- Inputs, gold, database fingerprints, prompts and configuration are recorded (hashed) in each run's manifest.
- Each case is repeated (default: 3) with a fresh session.
- Run artefacts are append-only: `Benchmark/benchmarking/output/<timestamp>_<solution>_<model>_repeat-<n>_<tags>/`.
