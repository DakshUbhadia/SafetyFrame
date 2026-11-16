"""Evidence extraction is independent of human evidence-quality assessment."""
from .audit_parser import parse_audit

EVIDENCE_CATEGORIES = {'specific_support', 'specific_contradiction', 'vague_claim',
                       'unsupported_assertion', 'incorrect_citation', 'missing'}


def parse_evidence(text, requirement_ids):
    return parse_audit(text, requirement_ids, 'evidence')
