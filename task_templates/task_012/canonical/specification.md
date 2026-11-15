# Balanced condition assignment for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** rotate_conditions(conditions,offset) requires a nonempty list of unique string conditions or raises ValueError; return a left rotation by offset modulo length, supporting negative integer offsets.
- **R2:** assign_blocks(tasks,conditions) requires unique task IDs and valid conditions or raises ValueError; preserve task order and return task,condition,position rows with each task's condition order rotated left by its task index and one-based positions.
- **R3:** validate_assignments(rows,tasks,conditions) returns True exactly when task and condition lists are unique, conditions nonempty, each task/condition pair occurs once, no unknown IDs occur, and positions per task are exactly integers 1..number_of_conditions excluding booleans; otherwise return False.
- **R4:** assignment_counts(rows) counts occurrences by condition, including repeated rows, returning a sorted-key dictionary; empty rows return an empty dictionary.
- **R5:** assignment_report(tasks,conditions) in reporting.py returns rows,valid,counts,position_counts, where position_counts maps each condition to a list of counts at each position 1..number_of_conditions.

Task and condition identifiers are strings. validate_assignments checks coverage and position uniqueness but does not require a particular rotation order. Assignment rows have exactly task,condition,position keys; unknown extra fields are outside the input contract. No randomization is performed: this is infrastructure for deterministic balanced assignment.
