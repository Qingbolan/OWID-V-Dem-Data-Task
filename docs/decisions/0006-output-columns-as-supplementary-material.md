# 0006. Output columns and their precision are given as supplementary material

- Status: accepted
- Date: 2026-10-30

## Context

In the WPP benchmark the query is natural language only: no output schema, no column names. A failure can then come
from not knowing what to return (which columns, in what unit or precision) as well as from computing it wrongly. This
benchmark is used to study the second kind, the publisher's processing conventions, so the first kind should not
dominate.

## Decision

Every task's query, at every input level, ends with supplementary material: one row per entity and year, the columns
`Entity`, `Year` and the figure's own columns in the published order (spec `solution_columns`, which leaves out a
map's "(Original Year)" column), each with its precision: the number of decimal places OWID prints, "whole number",
or "text" (spec `output_precision`, written by `scripts.write_golden_specs` from the figure CSV). The task's
`supplement` holds it; `Task.payload` appends it after the title, subtitle, page text or image note.

## Consequences

- The supplement is derived from the published figure, but carries no value of it: names and decimal places only.
  The harness's test of payloads (no row of the figure CSV in any input) still holds.
- Evaluation is unchanged: columns are still matched by value, and the tolerance stays at least 1 % relative, so a
  result printed at another precision is not penalised for that alone.
- Results are not directly comparable with the WPP benchmark's, which gives no output schema.
