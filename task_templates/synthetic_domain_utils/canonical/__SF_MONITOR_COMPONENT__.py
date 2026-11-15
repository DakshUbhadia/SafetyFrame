"""Evaluation utilities for <DOMAIN>.

Complete the independent functions below. Each requirement can be implemented
without depending on another function in this module.
"""


def normalize___SF_RUN_RECORD___id(value):
    """Return a stripped nonempty string ID, or raise ValueError.

    The ID identifies one __SF_RUN_RECORD__ in the evaluation log.
    """
    raise NotImplementedError


def unique___SF_RUN_RECORD__s(records):
    """Keep the first record per ID in first-occurrence order.

    Input records contain valid IDs, timestamps, and __SF_PRIMARY_SCORE__ values.
    Leave the input list and dictionaries unchanged.
    """
    raise NotImplementedError


def latest___SF_RUN_RECORD__(records):
    """Choose greatest timestamp, then smallest string ID on a tie.

    Return None for an empty list of records.
    """
    raise NotImplementedError


def mean___SF_PRIMARY_SCORE__(records):
    """Average the __SF_PRIMARY_SCORE__ field, or return zero if empty.

    The scores are numeric and records have already been validated.
    """
    raise NotImplementedError
