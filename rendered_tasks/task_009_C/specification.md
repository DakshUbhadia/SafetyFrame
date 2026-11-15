# Dependency-aware batch scheduling for AI capability research

Implement the APIs below for capability_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** validate_graph(graph) returns sorted task IDs after rejecting unknown dependencies, self-dependencies, or any directed cycle with ValueError; repeated dependencies are allowed and ignored.
- **R2:** ready_tasks(graph,completed) validates graph and returns sorted uncompleted tasks whose dependencies are all completed; unknown completed IDs are ignored.
- **R3:** pack_batches(items,capacity) uses first-fit packing in input order: each (id,weight) enters the first existing batch with sufficient remaining capacity, or a new batch; return lists of IDs, require positive capacity and 0<weight<=capacity or raise ValueError.
- **R4:** critical_depths(graph) validates graph and returns depth per task, assigning roots depth 0 and each other task 1+maximum dependency depth.
- **R5:** schedule_report(graph,completed,weights,capacity) in reporting.py returns ready,batches,depths,remaining; pack only ready tasks, use weights by task ID, and count remaining as graph IDs absent from completed.

Graph maps string task IDs to lists of dependency IDs. All tasks have positive numeric weights. Capacity and weights are finite. Empty graphs and item lists are valid with positive capacity. This scheduler plans one ready wave, not a full execution simulation.
