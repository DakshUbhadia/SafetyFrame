import copy
import re

def decode_pointer(pointer):
    if not isinstance(pointer,str) or (pointer and not pointer.startswith("/")): raise ValueError("invalid pointer")
    if not pointer: return []
    result=[]
    for segment in pointer[1:].split("/"):
        if re.search(r"~(?![01])",segment): raise ValueError("invalid escape")
        result.append(segment.replace("~1","/").replace("~0","~"))
    return result

def _index(segment,length,allow_end=False):
    if not re.fullmatch(r"0|[1-9][0-9]*",segment): raise ValueError("invalid index")
    index=int(segment)
    if index>length or (index==length and not allow_end): raise ValueError("out of bounds")
    return index

def get_value(document,pointer):
    node=document
    for segment in decode_pointer(pointer):
        if isinstance(node,dict):
            if segment not in node: raise ValueError("missing key")
            node=node[segment]
        elif isinstance(node,list): node=node[_index(segment,len(node))]
        else: raise ValueError("scalar traversal")
    return copy.deepcopy(node)
