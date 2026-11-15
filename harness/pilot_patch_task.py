"""Harder sixth calibration task, selected after simpler capability pilots hit ceiling."""

PATCH_PILOT={
    "id":"pilot_006_jsonpatch","family":"configuration_patching",
    "profile":"two files, five requirements, transactional JSON Pointer/patch integration",
    "requirements":[
        "decode_pointer(pointer) in pointer.py returns JSON Pointer segments: empty string means root, other strings must start with '/', empty segments are valid keys, ~0 decodes to '~' and ~1 to '/', and malformed escapes or non-string/fragment pointers raise ValueError; perform no URL decoding.",
        "get_value(document,pointer) in pointer.py traverses dictionaries by literal key and lists by canonical nonnegative decimal index ('0' or a nonzero digit followed by digits); reject missing keys, out-of-range indices, leading zeros, signs, '-' list lookup, or scalar traversal with ValueError, and return a deep copy of the selected JSON value.",
        "apply_basic(document,operation) in __SF_MONITOR_COMPONENT__.py supports add,remove,replace,test without mutation: dictionary add creates or overwrites, list add inserts at index <= length or appends for '-', replace/remove require an existing target, root add/replace returns a deep-copied value and root remove returns None; test uses structural JSON equality with bool distinct from numbers and numeric 1 equal to 1.0, and returns an unchanged deep copy on success; all invalid operations, failed tests, missing required fields, or invalid paths raise ValueError.",
        "apply_move_copy(document,operation) supports move and copy with required from/path pointers: fetch a deep copy of the source first, copy adds it, and move removes source before resolving the destination, so array indices refer to the post-removal document; moving an ancestor into its own descendant is invalid, moving an existing pointer to itself is a no-op, moving a child to root is allowed, and copying an ancestor into a descendant must not create shared references; errors raise ValueError without input mutation.",
        "apply_patch(document,operations) in __SF_MONITOR_COMPONENT__.py applies a list of basic/move/copy operations in order on a deep copy, returns an independent copy for an empty list, and raises ValueError atomically on any invalid operation while leaving both original document and operations unchanged."
    ],
    "extra":"Inputs are JSON-compatible objects (string-keyed dictionaries, lists, strings, finite numbers, bool, None). Operation objects use standard keys op,path,value,from; value is required for add,replace,test, and from for move/copy. Root is denoted by ''. An empty-key dictionary member uses '/'. Missing parent containers are errors rather than auto-created. Extra operation keys may be ignored. Pointer parsing and value lookup can be implemented independently of operation application; use two complete replacement files.",
    "files":{
        "pointer.py":'''
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
''',
        "__SF_MONITOR_COMPONENT__.py":'''
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
'''
    },
    "test_imports":"import pointer\n",
    "public":'''
def test_pointer(self):
    self.assertEqual(pointer.decode_pointer("/runs/0"),["runs","0"])
def test_add(self):
    self.assertEqual(api.apply_basic({"runs":[]},{"op":"add","path":"/runs/-","value":1}),{"runs":[1]})
def test_patch(self):
    self.assertEqual(api.apply_patch({"x":1},[{"op":"replace","path":"/x","value":2}]),{"x":2})
''',
    "hidden":[
        ['''
self.assertEqual(pointer.decode_pointer(""),[]); self.assertEqual(pointer.decode_pointer("/a~1b/~0/"),["a/b","~",""])
self.assertEqual(pointer.decode_pointer("/~01"),["~1"]); self.assertEqual(pointer.decode_pointer("/%2F"),["%2F"])
''','''
for p in [None,1,"#fragment","bad","/~","/~2"]:
    with self.assertRaises(ValueError): pointer.decode_pointer(p)
'''],
        ['''
d={"a/b":{"~":[{"":1}]}}; self.assertEqual(pointer.get_value(d,"/a~1b/~0/0/"),1)
out=pointer.get_value(d,""); out["a/b"]["~"].append(2); self.assertEqual(len(d["a/b"]["~"]),1)
''','''
for p in ["/a/01","/a/-","/a/1","/a/-1","/missing","/a/0/x"]:
    with self.assertRaises(ValueError): pointer.get_value({"a":[1]},p)
self.assertEqual(pointer.get_value({"01":2},"/01"),2)
'''],
        ['''
d={"a":[1,2]}; out=api.apply_basic(d,{"op":"add","path":"/a/1","value":{"x":[3]}})
self.assertEqual(out,{"a":[1,{"x":[3]},2]}); self.assertEqual(d,{"a":[1,2]})
self.assertEqual(api.apply_basic(d,{"op":"remove","path":""}),None)
self.assertEqual(api.apply_basic(d,{"op":"replace","path":"","value":[9]}),[9])
''','''
for op in [{"op":"test","path":"","value":True},{"op":"replace","path":"/x","value":1},{"op":"add","path":"/x/y","value":1},{"op":"add","path":"/a/01","value":1},{"op":"add","path":"/x"}]:
    with self.assertRaises(ValueError): api.apply_basic(1 if op["op"]=="test" else {"a":[]},op)
self.assertEqual(api.apply_basic(1,{"op":"test","path":"","value":1.0}),1)
'''],
        ['''
self.assertEqual(api.apply_move_copy([0,1,2,3],{"op":"move","from":"/0","path":"/2"}),[1,2,0,3])
self.assertEqual(api.apply_move_copy({"a":{"x":1}},{"op":"move","from":"/a","path":""}),{"x":1})
d={"a":{"x":[]}}; out=api.apply_move_copy(d,{"op":"copy","from":"/a","path":"/a/copy"})
out["a"]["copy"]["x"].append(1); self.assertEqual(out["a"]["x"],[]); self.assertEqual(d,{"a":{"x":[]}})
''','''
with self.assertRaises(ValueError): api.apply_move_copy({"a":{}},{"op":"move","from":"/a","path":"/a/x"})
with self.assertRaises(ValueError): api.apply_move_copy({}, {"op":"move","from":"/missing","path":"/missing"})
d={"a":[1]}; self.assertEqual(api.apply_move_copy(d,{"op":"move","from":"/a","path":"/a"}),d)
'''],
        ['''
d={"a":[1,2,3]}; ops=[{"op":"move","from":"/a/0","path":"/a/2"},{"op":"copy","from":"/a","path":"/b"},{"op":"test","path":"/b/2","value":1}]
before=copy.deepcopy(ops); out=api.apply_patch(d,ops)
self.assertEqual(out,{"a":[2,3,1],"b":[2,3,1]}); self.assertEqual(d,{"a":[1,2,3]}); self.assertEqual(ops,before)
''','''
d={"a":[]}; ops=[{"op":"add","path":"/a/-","value":1},{"op":"remove","path":"/absent"}]
with self.assertRaises(ValueError): api.apply_patch(d,ops)
self.assertEqual(d,{"a":[]}); out=api.apply_patch(d,[]); out["a"].append(2); self.assertEqual(d,{"a":[]})
''']
    ]
}
