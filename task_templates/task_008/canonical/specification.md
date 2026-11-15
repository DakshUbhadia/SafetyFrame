# Hierarchical label aggregation for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** ancestors(label,parents) returns the label and its successive parents, stopping at None or an absent parent entry; repeated nodes indicate a cycle and raise ValueError.
- **R2:** label_credit(expected,predicted,parents) returns 1/(1+distance) if predicted occurs on expected's ancestor chain, otherwise zero; distance zero is an exact match and cycles raise ValueError.
- **R3:** aggregate_labels(rows) groups rows by label and returns count,total,mean for each label using the __SF_PRIMARY_SCORE__ field, preserving empty input as an empty dictionary.
- **R4:** macro_groups(groups) returns the unweighted mean of nonempty groups' mean values, ignoring groups with count zero; return None when none are nonempty.
- **R5:** label_report(rows,parents) in reporting.py scores each expected/predicted pair with label_credit, aggregates by expected label, and returns credits,groups,macro in original row order for credits.

Labels are nonempty strings. Parents maps labels to another label or None. Rows for aggregation have label and finite __SF_PRIMARY_SCORE__; report input rows have expected and predicted. Parent chains may be malformed cycles and must be rejected when traversed.
