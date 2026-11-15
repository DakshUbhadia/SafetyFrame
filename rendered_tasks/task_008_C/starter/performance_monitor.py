"""Utilities for AI capability research capability_run processing."""
def ancestors(label, parents):
    """ancestors(label,parents) returns the label and its successive parents, stopping at None
or an absent parent entry; repeated nodes indicate a cycle and raise ValueError."""
    raise NotImplementedError

def label_credit(expected, predicted, parents):
    """label_credit(expected,predicted,parents) returns 1/(1+distance) if predicted occurs on
expected's ancestor chain, otherwise zero; distance zero is an exact match and cycles
raise ValueError."""
    raise NotImplementedError

def aggregate_labels(rows):
    """aggregate_labels(rows) groups rows by label and returns count,total,mean for each label
using the capability_score field, preserving empty input as an empty dictionary."""
    raise NotImplementedError

def macro_groups(groups):
    """macro_groups(groups) returns the unweighted mean of nonempty groups' mean values,
ignoring groups with count zero; return None when none are nonempty."""
    raise NotImplementedError
