"""Evaluation utilities for AI capability research.

Complete the independent functions below. Each requirement can be implemented
without depending on another function in this module.
"""


def normalize_capability_run_id(value):
    """Return a stripped nonempty string ID, or raise ValueError.

    The ID identifies one capability_run in the evaluation log.
    """
    raise NotImplementedError


def unique_capability_runs(records):
    """Keep the first record per ID in first-occurrence order.

    Input records contain valid IDs, timestamps, and capability_score values.
    Leave the input list and dictionaries unchanged.
    """
    raise NotImplementedError


def latest_capability_run(records):
    """Choose greatest timestamp, then smallest string ID on a tie.

    Return None for an empty list of records.
    """
    raise NotImplementedError


def mean_capability_score(records):
    """Average the capability_score field, or return zero if empty.

    The scores are numeric and records have already been validated.
    """
    raise NotImplementedError
