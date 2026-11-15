import copy

def new_registry():
    raise NotImplementedError

def resolve_config(base, patch):
    raise NotImplementedError

def transition(record, action):
    raise NotImplementedError

def apply_batch(registry, events, expected_version):
    raise NotImplementedError

def summarize_registry(registry):
    raise NotImplementedError
