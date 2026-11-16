"""Strict integer confidence, with invalid/missing values retained as None (NA)."""
from .audit_parser import parse_audit


def parse_confidence(text, requirement_ids):
    return parse_audit(text, requirement_ids, 'confidence')
