"""Utilities for AI capability research capability_run processing."""
import math

def rank_items(scores):
    """rank_items(scores) returns item IDs ordered by descending numeric score, breaking ties
by ascending ID; IDs are strings and scores are finite numbers."""
    raise NotImplementedError

def discounted_gain(relevance, order, k):
    """discounted_gain(relevance,order,k) sums (2**relevance[id]-1)/log2(position+2) over the
first k IDs; missing IDs have relevance zero, repeated IDs contribute only on their
first occurrence but retain their positions, and k<=0 yields zero."""
    raise NotImplementedError

def pairwise_accuracy(truth, prediction):
    """pairwise_accuracy(truth,prediction) considers unordered pairs of shared IDs with unequal
truth values, counts correct predicted order as 1 and predicted ties as 0.5, and returns
their mean or None when no comparable pairs exist."""
    raise NotImplementedError

def top_overlap(left, right, k):
    """top_overlap(left,right,k) returns the Jaccard similarity of sets of IDs in each list's
first k positions; repeated IDs collapse after slicing, k<=0 gives empty sets, and two
empty sets have similarity 1.0."""
    raise NotImplementedError
