# 0004. Golden programs run OWID's own V-Dem code on the benchmark database

- Status: accepted
- Date: 2026-10-29

## Context

In the WPP benchmark each golden program is a hand translation of OWID's processing into SQL. OWID's V-Dem
processing is 3,500 lines of pandas: a rebuilt regime classification with hand-reconciled cases, 57 rules imputing
historical countries, election status carried between elections, population-weighted regional averages with
coverage thresholds, counts of countries and of people by category. Translating that into SQL for 100 charts would
be error-prone, and a mistranslation could not be told apart from a benchmark defect.

## Decision

The golden program of every chart has two parts:

1. **Shared**: `golden/vdem_pipeline.py` runs OWID's code unchanged (`data/reference/owid_etl/vdem/`, copied from
   owid/etl at the commit in `PROVENANCE.json`) with its inputs redirected to the benchmark database: the meadow table
   is rebuilt from the V-Dem section tables (the columns OWID's meadow step keeps), and OWID's region and population
   datasets are read from `owid_regions` and `owid_population`. Only `etl.helpers.PathFinder` and `etl.paths` are
   replaced by small stand-ins; `etl.data_helpers.geo` is OWID's file. It runs in its own environment with OWID's
   libraries at the same commit (`make golden-env`).
2. **Per figure**: `spec.json` names, for every figure column, the column of OWID's output tables it plots (resolved from
   the indicator's short name), and the view settings that transform it ([0003](0003-figure-view-as-ground-truth.md)).

`make golden` compares the result with the published CSV cell by cell: one unit in the last printed decimal or 1e-6
relative (OWID publishes some values as 32-bit floats). All 124 V-Dem figures (the 100 charts, in their page views) match.

## Which commit

The published charts (captured 2026-10-29) match owid/etl master of 2026-10-28 (`bac9e16`), not the older local clone
(`f1ffd5e`, 2026-10-17). Commit `37060a1` (2026-10-28) added, among others, the rule that a country without regularly
scheduled legislative elections (`v2xlg_elecreg`) is a closed autocracy; with the older code, six stacked charts of
regime counts and populations differed (e.g. Baden, Iran and Peru in 1789-1791 have no regime instead of closed
autocracy). The V-Dem snapshot is the same at both commits. The pandas version (2.3.3 vs 3.0.6) was checked and is not
the cause.

## Consequences

- Reproducibility is proven against OWID's exact code, not a re-implementation; the per-chart spec documents which
  output column and view rule each figure uses.
- The golden programs need an owid/etl clone containing `bac9e16` and OWID's libraries; the benchmark harness does not.
- The specs do not read as SQL. Where a readable account of a convention is needed (failure analysis), it should cite
  OWID's code in `data/reference/owid_etl/vdem/`.
