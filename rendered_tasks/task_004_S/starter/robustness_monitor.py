"""Utilities for AI safety research safety_eval_run processing."""
import copy
import math

def convert_score(value, unit):
    """convert_score(value,unit) accepts finite non-bool numbers, converts unit fraction
unchanged and percent by dividing by 100, then requires the result in [0,1]; invalid
units or values raise ValueError."""
    raise NotImplementedError

def rename_fields(row, mapping):
    """rename_fields(row,mapping) performs simultaneous key renaming on a deep copy, preserving
unmapped keys, and raises ValueError if two existing source keys would collide at one
destination; mappings for absent keys are ignored."""
    raise NotImplementedError

def migrate_row(row):
    """migrate_row(row) accepts version 1 rows with run_id and percent score, or version 2 rows
with id and alignment_score; outputs version=2,id stripped nonempty
string,alignment_score as fraction, and metadata as a deep copy defaulting to {};
unsupported versions or invalid IDs/scores raise ValueError."""
    raise NotImplementedError

def migrate_table(rows):
    """migrate_table(rows) returns (valid,errors), migrating independently and recording one-
based input indices of ValueError failures while preserving successful order and not
mutating inputs."""
    raise NotImplementedError
