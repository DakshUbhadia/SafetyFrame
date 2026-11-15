import copy
from pointer import decode_pointer, get_value, _index

def _equal(left,right):
    if isinstance(left,bool) or isinstance(right,bool): return type(left) is type(right) and left==right
    if isinstance(left,(int,float)) and isinstance(right,(int,float)): return left==right
    if type(left) is not type(right): return False
    if isinstance(left,dict): return left.keys()==right.keys() and all(_equal(left[k],right[k]) for k in left)
    if isinstance(left,list): return len(left)==len(right) and all(_equal(a,b) for a,b in zip(left,right))
    return left==right

def apply_basic(document,operation):
    if not isinstance(operation,dict) or operation.get("op") not in {"add","remove","replace","test"} or "path" not in operation: raise ValueError("invalid operation")
    action=operation["op"]; segments=decode_pointer(operation["path"])
    if action in {"add","replace","test"} and "value" not in operation: raise ValueError("missing value")
    if action=="test":
        if not _equal(get_value(document,operation["path"]),operation["value"]): raise ValueError("failed test")
        return copy.deepcopy(document)
    if not segments: return None if action=="remove" else copy.deepcopy(operation["value"])
    out=copy.deepcopy(document); parent=out
    for segment in segments[:-1]:
        if isinstance(parent,dict) and segment in parent: parent=parent[segment]
        elif isinstance(parent,list): parent=parent[_index(segment,len(parent))]
        else: raise ValueError("missing parent")
    key=segments[-1]
    if isinstance(parent,dict):
        if action in {"replace","remove"} and key not in parent: raise ValueError("missing target")
        if action=="remove": del parent[key]
        else: parent[key]=copy.deepcopy(operation["value"])
    elif isinstance(parent,list):
        index=len(parent) if action=="add" and key=="-" else _index(key,len(parent),action=="add")
        if action=="add": parent.insert(index,copy.deepcopy(operation["value"]))
        elif action=="replace": parent[index]=copy.deepcopy(operation["value"])
        else: parent.pop(index)
    else: raise ValueError("scalar parent")
    return out

def apply_move_copy(document,operation):
    if not isinstance(operation,dict) or operation.get("op") not in {"move","copy"} or "from" not in operation or "path" not in operation: raise ValueError("invalid operation")
    source=decode_pointer(operation["from"]); target=decode_pointer(operation["path"])
    value=get_value(document,operation["from"])
    if operation["op"]=="move":
        if source==target: return copy.deepcopy(document)
        if len(target)>len(source) and target[:len(source)]==source: raise ValueError("descendant move")
        base=apply_basic(document,{"op":"remove","path":operation["from"]})
    else: base=copy.deepcopy(document)
    return apply_basic(base,{"op":"add","path":operation["path"],"value":value})

def apply_patch(document,operations):
    if not isinstance(operations,list): raise ValueError("operations must be a list")
    out=copy.deepcopy(document)
    for operation in operations:
        if not isinstance(operation,dict): raise ValueError("invalid operation")
        out=apply_move_copy(out,operation) if operation.get("op") in {"move","copy"} else apply_basic(out,operation)
    return out
