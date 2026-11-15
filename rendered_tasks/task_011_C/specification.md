# Checkpoint replay and reconciliation for AI capability research

Implement the APIs below for capability_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** latest_checkpoints(events) chooses the event with greatest integer sequence per job, with later input occurrence winning equal sequences; return deep-copied events by job ID.
- **R2:** resume_jobs(jobs,checkpoints) returns sorted unique job IDs whose checkpoint is absent or status is not complete; ignore checkpoint IDs outside jobs.
- **R3:** reconcile_artifacts(expected,observed) compares path-to-hash dictionaries and returns sorted missing,changed,unexpected path lists; changed paths are present in both with unequal hashes.
- **R4:** plan_retries(jobs,checkpoints,max_attempts) requires a positive integer limit excluding booleans or raises ValueError; return sorted eligible job IDs with absent checkpoint or status pending/failed and attempts below limit, treating absent attempts as zero; running/complete jobs are excluded.
- **R5:** recovery_report(jobs,events,expected,observed,max_attempts) in reporting.py returns latest,resume,artifacts,retry from the four core functions.

Job IDs and paths are strings; sequence and attempts are nonnegative integers. Status is one of pending,running,failed,complete. Job lists may repeat IDs. Reconciliation compares supplied hashes exactly and never reads the filesystem.
