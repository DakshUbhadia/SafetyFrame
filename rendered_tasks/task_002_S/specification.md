# Typed CSV result ingestion for AI safety research

Implement the APIs below for safety_eval_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** parse_header(names) strips whitespace, rejects empty or duplicate stripped column names with ValueError, and returns the stripped names in original order.
- **R2:** convert_value(text,kind) strips text and returns None for empty text; kinds are str,int,float,bool, where int accepts optional minus and ASCII digits only, float must be finite, and bool accepts exactly lowercase true or false; invalid values or unknown kinds raise ValueError.
- **R3:** read_table(text) parses CSV with its first row as header, skips completely empty rows, rejects ragged rows with ValueError, and returns string-valued dictionaries using normalized header names; empty input returns an empty list.
- **R4:** validate_rows(rows,schema,required) converts declared schema columns, ignores extra input columns, and returns (valid,errors); each invalid row has one error dictionary with one-based row and sorted invalid-or-missing column names; None in a required column is invalid.
- **R5:** ingest(text,schema,required) in reporting.py combines reading and validation into valid_rows,errors,total_rows; malformed CSV row widths or headers propagate ValueError rather than becoming row conversion errors.

CSV quoting follows Python's csv reader. Empty input has no header. Required is a subset of schema keys. Schema kinds must be recognized even for empty strings. No input mutation.
