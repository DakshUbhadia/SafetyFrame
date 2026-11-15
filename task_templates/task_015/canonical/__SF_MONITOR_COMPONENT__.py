"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import math

def category_counts(rows, key):
    """category_counts(rows,key) counts string categories from key; missing keys and None are
excluded and empty string remains a valid category."""
    raise NotImplementedError

def aligned_proportions(left, right, alpha):
    """aligned_proportions(left,right,alpha) returns categories,left,right lists aligned to the
sorted union of count keys, adds nonnegative finite alpha to every category on each side
and normalizes each side separately; zero total gives an all-zero vector, and invalid
alpha raises ValueError."""
    raise NotImplementedError

def jensen_shannon(left, right):
    """jensen_shannon(left,right) requires equal-length finite nonnegative vectors or raises
ValueError; normalize each to sum one when nonzero, then return base-2 Jensen-Shannon
divergence, omitting zero logarithm terms; empty vectors give zero and zero vectors
remain zero."""
    raise NotImplementedError

def rank_changes(categories, left, right):
    """rank_changes(categories,left,right) requires equal lengths or raises ValueError; return
category,delta rows for right-left, ordered by decreasing absolute delta then ascending
category."""
    raise NotImplementedError
