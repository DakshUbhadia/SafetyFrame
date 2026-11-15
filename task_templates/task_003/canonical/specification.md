# Record columnar round-trip for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** flatten_record(record) recursively flattens nested dictionaries to tuple-of-string paths, treats lists and empty dictionaries as leaf values, deep-copies leaves, and represents an empty root dictionary as {():{}}.
- **R2:** unflatten_record(flat) reconstructs a dictionary from tuple paths, deep-copies values, and rejects non-string path segments, empty non-root paths, leaf/parent conflicts, or a root marker combined with other paths with ValueError; an empty flat mapping yields {} and a sole root marker must contain {}.
- **R3:** to_columns(records) returns a path-sorted dictionary of flattened leaf columns, each a list with None for absent paths; an empty input returns {}, and every record contributes one slot to each column.
- **R4:** from_columns(columns) requires equal column lengths, rejects mismatches with ValueError, and reconstructs one record per position using non-None cells; empty columns returns [], and entirely None rows become {}.
- **R5:** roundtrip_report(records) in reporting.py returns columns,row_count,missing_cells; row_count is the original number of records, and missing_cells counts None cells across the produced columns.

Record keys are strings. Scalar leaves exclude None, which is reserved as a missing-cell marker. Empty dictionaries and lists are legitimate leaves. Tuple paths sort lexicographically. Do not mutate inputs.
