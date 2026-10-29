# Task definition

## Research question

Can a general-purpose agent with read-only SQL access to raw upstream data produce the data behind a published chart,
given only natural-language input? Where it fails, is the failure caused by an underspecified request, by the
publisher's processing conventions, or by query construction?

## Unit of evaluation

One **chart** in `OWID/<chart slug>/`, in the view a reader sees (its host page's embed, or its default view;
[decision 0005](decisions/0005-chart-selection-and-host-pages.md)). A chart is scored when its golden program
reproduces OWID's published data for that view from `data/sqlite/vdem2026.db` (`verification.json` status `match`);
all 100 do.

## Inputs (graded)

The input is one natural-language query, as a person describing the chart they need would write it. Nothing else is
given: no output schema, no column names, no entity or year list.

| Level | The query is | Charts |
|---|---|---:|
| `title` | the chart title | 100 |
| `subtitle` | the chart title and its subtitle | 100 |
| `article` | the title, the subtitle and the full text of the host page (figures shown as `[Figure n]`, the requested one marked), without the chart's own notes, units or source | 19 |

Charts that no page shows as a figure have no article level; image levels need redacted images, which this
repository does not have yet. The harness skips unsupported levels.

The agent always receives read-only access to the database through one SQL tool. It never receives the figure CSV,
the image, the golden program, OWID's processed data or OWID's code.

## Output

One read-only SQLite `SELECT` per chart. The harness executes it and stores the result.

## Correctness

Without a schema, the result's columns are matched to the figure's by value
(`Benchmark/benchmarking/evaluator/quantitative_evaluator/quant_metrics.py`):

- the entity column is the text column covering the most figure entities after OWID's V-Dem-to-OWID name mapping
  (`data/reference/owid_etl/vdem/vdem.countries.json`); the year column the integer column covering the most figure
  years; either may be absent when the figure shows a single entity or year;
- each figure column (spec `solution_columns`; a map's "(Original Year)" column is not asked for) is matched to the
  result column that reproduces most of its cells within 1 % relative (or the golden tolerance, if larger); coded
  columns (regime categories, spec `encodings`) may use any one-to-one labelling;
- a chart is correct when every non-missing figure cell is reproduced, every figure (entity, year) key is present, no
  key is duplicated and no extra row falls inside the figure's entities and year range. Rows for other entities or
  years are not penalised but counted (`entities_outside_figure`).

## Protocol

- Inputs, gold, database fingerprints, prompts and configuration are recorded (hashed) in each run's manifest.
- Each case is repeated (default: 3) with a fresh session.
- Run artefacts are append-only: `Benchmark/benchmarking/output/<timestamp>_<solution>_<model>_repeat-<n>_<tags>/`.
