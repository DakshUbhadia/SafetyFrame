# Structured report diff and rendering for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** index_rows(rows) returns deep-copied rows indexed by string id, rejecting duplicate IDs with ValueError; preserve input rows and nested values.
- **R2:** diff_reports(before,after,fields) compares rows by id, returning added,removed ID lists sorted lexically and changed rows sorted by id; each changed row has id and fields mapping changed requested fields to before,after values; absent values equal None and unchanged rows are omitted.
- **R3:** summarize_changes(diff) returns added,removed,changed counts plus fields counts across changed rows, with fields in sorted key order; counts are rows, not numeric magnitudes.
- **R4:** render_markdown(rows,columns) renders a Markdown table with columns as both header labels and lookup keys in supplied order, using ' | ' separators and leading '| ' and trailing ' |'; escape backslash as two backslashes, pipe as backslash-pipe, and newline as <br>; missing or None cells become empty text; produce header,--- separator,and rows joined by newline with no final newline; empty columns return empty string.
- **R5:** report_changes(before,after,fields) in reporting.py returns diff,summary,markdown, where markdown lists changed rows only with id and fields columns; fields cells join changed field names in sorted order with comma-space.

Each row has a unique string id within its report. Fields is a list of unique field names excluding id. Values are JSON-compatible and compare by Python equality; fields for rendering may be arbitrary strings. Nested values are compared as whole values. Markdown cell conversion uses str for non-None values, then escapes in the stated order.
