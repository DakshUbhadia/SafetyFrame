"""Evaluation utilities for AI safety research.

Complete the independent functions below. Each requirement can be implemented
without depending on another function in this module.
"""


def normalize_safety_eval_run_id(value):
    """Return a stripped nonempty string ID, or raise ValueError.

    The ID identifies one safety_eval_run in the evaluation log.
    """
    raise NotImplementedError


def unique_safety_eval_runs(records):
    """Keep the first record per ID in first-occurrence order.

    Input records contain valid IDs, timestamps, and alignment_score values.
    Leave the input list and dictionaries unchanged.
    """
    raise NotImplementedError


def latest_safety_eval_run(records):
    """Choose greatest timestamp, then smallest string ID on a tie.

    Return None for an empty list of records.
    """
    raise NotImplementedError


def mean_alignment_score(records):
    """Average the alignment_score field, or return zero if empty.

    The scores are numeric and records have already been validated.
    """
    raise NotImplementedError
