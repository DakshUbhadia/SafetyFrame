import re
from decimal import Decimal

def parse_duration(value):
    raise NotImplementedError

def coalesce_intervals(intervals):
    raise NotImplementedError

def subtract_intervals(inclusions, exclusions):
    raise NotImplementedError

def coverage_by_group(records, windows):
    raise NotImplementedError
