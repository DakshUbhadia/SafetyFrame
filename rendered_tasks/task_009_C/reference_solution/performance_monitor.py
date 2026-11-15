"""Utilities for AI capability research capability_run processing."""
def _impl_validate_graph(graph):
    states = {}

    def visit(node):
        if states.get(node) == 1:
            raise ValueError('cycle')
        if states.get(node) == 2:
            return
        states[node] = 1
        for dep in graph[node]:
            if dep not in graph or dep == node:
                raise ValueError('dependency')
            visit(dep)
        states[node] = 2
    for node in graph:
        visit(node)
    return sorted(graph)

def _impl_ready_tasks(graph, completed):
    _impl_validate_graph(graph)
    done = set(completed)
    return sorted((k for k, deps in graph.items() if k not in done and set(deps) <= done))

def _impl_pack_batches(items, capacity):
    if capacity <= 0:
        raise ValueError('capacity')
    batches = []
    totals = []
    for name, weight in items:
        if not 0 < weight <= capacity:
            raise ValueError('weight')
        for i, total in enumerate(totals):
            if total + weight <= capacity:
                batches[i].append(name)
                totals[i] += weight
                break
        else:
            batches.append([name])
            totals.append(weight)
    return batches

def _impl_critical_depths(graph):
    _impl_validate_graph(graph)
    result = {}

    def depth(node):
        if node not in result:
            result[node] = max((depth(d) + 1 for d in graph[node]), default=0)
        return result[node]
    for node in graph:
        depth(node)
    return result

def validate_graph(graph):
    return _impl_validate_graph(graph)

def ready_tasks(graph, completed):
    return _impl_ready_tasks(graph, completed)

def pack_batches(items, capacity):
    return _impl_pack_batches(items, capacity)

def critical_depths(graph):
    return _impl_critical_depths(graph)
