# Versioned score-table migration for AI capability research

Implement the APIs below for capability_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** convert_score(value,unit) accepts finite non-bool numbers, converts unit fraction unchanged and percent by dividing by 100, then requires the result in [0,1]; invalid units or values raise ValueError.
- **R2:** rename_fields(row,mapping) performs simultaneous key renaming on a deep copy, preserving unmapped keys, and raises ValueError if two existing source keys would collide at one destination; mappings for absent keys are ignored.
- **R3:** migrate_row(row) accepts version 1 rows with run_id and percent score, or version 2 rows with id and capability_score; outputs version=2,id stripped nonempty string,capability_score as fraction, and metadata as a deep copy defaulting to {}; unsupported versions or invalid IDs/scores raise ValueError.
- **R4:** migrate_table(rows) returns (valid,errors), migrating independently and recording one-based input indices of ValueError failures while preserving successful order and not mutating inputs.
- **R5:** migration_report(rows) in reporting.py returns migrated,errors,duplicate_ids; duplicate_ids is a sorted list of IDs occurring more than once among successful migrations, each listed once.

For migrate_row, required version-1 fields are version,run_id,score; version-2 fields are version,id,capability_score. Missing required fields raise ValueError. Extra top-level fields are omitted from migrated rows; metadata is JSON-compatible. Version must be int excluding bool.
