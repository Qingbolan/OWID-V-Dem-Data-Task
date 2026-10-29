# 0003. The published figure view is the ground truth

- Status: accepted
- Date: 2026-10-29 (revised 2026-10-30 for the page-based layout)

## Context

A grapher chart's full CSV contains every entity and year, while a reader sees one view: on a page, the embed's own
settings (a tab, a time, a stack mode, a selection); on a chart page, the chart's default tab (often a map of the
latest year); in a data insight, a static image of some view.

## Decision

Each figure's `.csv` is downloaded from OWID with `csvType=filtered` and the view's query string: the embed's query on
the page, none for a chart page, or, for a data insight, the view identified by hand from the image (the figure list in
`scripts/articles/` records the view and how it was identified, as in the WPP benchmark; a "scope" keeps only the
entities, years and columns the image shows). The expected data is exactly what the view displays, including what the
view does to the values: relative stacking (shares of 100, only in stacked chart types), a map's time tolerance (the
closest year within N years, with an "(Original Year)" column), and display conversion factors. Evaluation compares on
that view's (Entity, Year) keys.

## Consequences

- 83 of the 124 views are maps; their keys are one row per country drawn on the map.
- The ground truth follows OWID's chart data when it was captured (2026-10-29/30); `meta.json` records download URLs
  and hashes, and golden programs prove the data is reproducible from the pinned V-Dem snapshot.
- Four data-insight images were made with earlier V-Dem releases (their source line says V-Dem 2024 or 2025); their
  printed values can differ slightly from the view's current data, which is the ground truth (the identification notes
  give an example).
- A solution is not asked for a map's "(Original Year)" column (spec `solution_columns`), only for the values.
