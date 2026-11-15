# Escaped record-path projection for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** parse_path(text) splits dot-separated paths, using backslash to escape a dot or backslash; reject empty segments, empty input, non-string input, invalid escapes, and a trailing backslash with ValueError.
- **R2:** lookup(record,segments,default=None) traverses dictionary keys and canonical list indices (0 or a nonzero digit followed by digits); return a deep copy or the supplied default for a missing key, invalid index, or scalar traversal; empty segments select the whole record.
- **R3:** project(record,columns) resolves output-name to path-string mappings, returns values in sorted output-name order, and uses None for missing fields while preserving False and zero values.
- **R4:** expand_columns(columns,prefix) prepends prefix plus a dot to each path when prefix is nonempty, preserves paths when prefix is empty, returns a new dictionary, and rejects invalid resulting paths with ValueError.
- **R5:** project_table(records,columns) in reporting.py projects every record, returning columns as sorted output names, rows as lists of values in that order, and missing_counts per output column counting only None values.

Paths use ASCII canonical list indices with no signs or leading zeros. Dictionary keys remain literal even when numeric. Inputs are JSON-compatible. Do not mutate any input.
