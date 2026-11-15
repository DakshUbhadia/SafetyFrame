"""Utilities for AI capability research capability_run processing."""
def decide(probabilities, threshold):
    """decide(probabilities,threshold) returns integer decisions using probability>=threshold,
preserving input order."""
    raise NotImplementedError

def confusion(labels, decisions):
    """confusion(labels,decisions) requires equal lengths or raises ValueError, and returns
tp,fp,tn,fn counts for binary integer lists, including empty lists."""
    raise NotImplementedError

def decision_cost(counts, costs):
    """decision_cost(counts,costs) returns the sum of each confusion count times its cost,
where omitted count or cost keys contribute zero; inputs may be partial dictionaries."""
    raise NotImplementedError

def best_threshold(labels, probabilities, candidates, costs):
    """best_threshold(labels,probabilities,candidates,costs) evaluates every distinct candidate
using decision cost and returns threshold,cost; ties choose the largest threshold, empty
candidates or unequal data lengths raise ValueError."""
    raise NotImplementedError
