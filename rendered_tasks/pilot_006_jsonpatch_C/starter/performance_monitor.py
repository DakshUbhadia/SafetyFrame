import copy
from pointer import decode_pointer, get_value, _index

def _equal(left, right):
    raise NotImplementedError

def apply_basic(document, operation):
    raise NotImplementedError

def apply_move_copy(document, operation):
    raise NotImplementedError

def apply_patch(document, operations):
    raise NotImplementedError
