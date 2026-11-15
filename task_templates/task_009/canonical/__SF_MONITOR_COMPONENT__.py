"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
def validate_graph(graph):
    """validate_graph(graph) returns sorted task IDs after rejecting unknown dependencies,
self-dependencies, or any directed cycle with ValueError; repeated dependencies are
allowed and ignored."""
    raise NotImplementedError

def ready_tasks(graph, completed):
    """ready_tasks(graph,completed) validates graph and returns sorted uncompleted tasks whose
dependencies are all completed; unknown completed IDs are ignored."""
    raise NotImplementedError

def pack_batches(items, capacity):
    """pack_batches(items,capacity) uses first-fit packing in input order: each (id,weight)
enters the first existing batch with sufficient remaining capacity, or a new batch;
return lists of IDs, require positive capacity and 0<weight<=capacity or raise
ValueError."""
    raise NotImplementedError

def critical_depths(graph):
    """critical_depths(graph) validates graph and returns depth per task, assigning roots depth
0 and each other task 1+maximum dependency depth."""
    raise NotImplementedError
