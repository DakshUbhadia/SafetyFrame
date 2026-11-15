"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import math

def match_pairs(left, right):
    """match_pairs(left,right) matches dictionaries by shared string IDs, sorts IDs, and
returns (id,right-left) tuples, ignoring unshared IDs."""
    raise NotImplementedError

def sign_summary(deltas, tolerance):
    """sign_summary(deltas,tolerance) counts positive values above tolerance, negative values
below -tolerance, and ties in the inclusive middle; tolerance must be nonnegative or
raise ValueError."""
    raise NotImplementedError

def trimmed_mean(values, fraction):
    """trimmed_mean(values,fraction) sorts values, removes floor(n*fraction) from each end, and
averages the remainder; require 0<=fraction<0.5 or raise ValueError, and return None for
empty input."""
    raise NotImplementedError

def leave_one_out(values):
    """leave_one_out(values) returns the mean after omitting each index, preserving omission
order; empty or singleton inputs return an empty list."""
    raise NotImplementedError
