# Failure evaluator (planned)

Assigns one primary failure category (docs/task-definition.md) to each incorrect case, with evidence from the
trajectory: tables and columns read, the final SQL, and the cells that differ.

Not implemented yet: categories are assigned manually from `trajectory.jsonl` and `final.sql` until enough labelled
failures exist to specify reliable rules.
