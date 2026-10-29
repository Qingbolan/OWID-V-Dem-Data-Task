# 0003. The published chart view is the ground truth

- Status: accepted
- Date: 2026-10-29

## Context

A grapher chart's full CSV contains every entity and year, while a reader sees one view: the chart's default tab
(often a map of the latest year), or, on a page, the embed's own settings (a tab, a stack mode, a selection).

## Decision

Each chart's `.csv` is downloaded from OWID with `csvType=filtered` and the view's query string: the embed's query on
the host page ([0005](0005-chart-selection-and-host-pages.md)), or none for the chart's default view. The expected
data is exactly what the view displays, including what the view does to the values: relative stacking (shares of
100), a map's time tolerance (the closest year within N years, with an "(Original Year)" column), and display
conversion factors. Evaluation compares on that view's (Entity, Year) keys.

## Consequences

- 75 of the 100 views are maps of the latest year; their keys are one row per country drawn on the map.
- The ground truth follows OWID's chart data when it was captured (2026-10-29); `meta.json` records download URLs and
  hashes, and golden programs prove the data is reproducible from the pinned V-Dem snapshot.
- A solution is not asked for a map's "(Original Year)" column (spec `solution_columns`), only for the values.
