# Calibration task for AI capability research

This is an excluded pilot task.

- **R1:** new_registry() returns a fresh dictionary with version=0,runs={},seen={} and no shared mutable state between calls.
- **R2:** resolve_config(base,patch) recursively merges dictionaries, treats None as key deletion, replaces lists and scalar values, and deep-copies output without mutating inputs.
- **R3:** transition(record,action) accepts start from queued to running, complete from running to completed, fail from running to failed, and retry from failed to queued while incrementing attempts; other state/action combinations raise ValueError, and unchanged fields and inputs are preserved by deep copying.
- **R4:** apply_batch(registry,events,expected_version) first rejects a version mismatch, then atomically applies events in input order on a deep copy; register creates a missing run with id,state='queued',attempts=0, other actions use transition; each event has a unique event_id,id,action and an already-seen identical event is skipped, while a conflicting reuse raises ValueError; version increments exactly once if any new event applied, otherwise stays unchanged; invalid batches must leave the original registry unchanged.
- **R5:** summarize_registry(registry) returns counts for queued,running,completed,failed including zero counts, completed_ids sorted lexicographically, and total_retries equal to the sum of attempts; this function must not mutate the registry.

All supplied registries have version integer, runs keyed by string id, and seen keyed by string event_id storing the original event dictionaries. Records contain id,state,attempts plus optional metadata. Event actions are register,start,complete,fail,retry. Reject register of an existing run or non-register action for a missing run with ValueError. All malformed action/state cases raise ValueError. expected_version is checked even when all events would be replays. Implement in performance_monitor.py.
