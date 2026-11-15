import copy
import json
import math
import unittest
import performance_monitor as api
import pointer



HIDDEN_ONLY_SENTINEL = "pilot_006_jsonpatch_PRIVATE_CHECKS"

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(pointer.decode_pointer(""),[]); self.assertEqual(pointer.decode_pointer("/a~1b/~0/"),["a/b","~",""])
        self.assertEqual(pointer.decode_pointer("/~01"),["~1"]); self.assertEqual(pointer.decode_pointer("/%2F"),["%2F"])

    def test_R1_case2(self):
        for p in [None,1,"#fragment","bad","/~","/~2"]:
            with self.assertRaises(ValueError): pointer.decode_pointer(p)

    def test_R2_case1(self):
        d={"a/b":{"~":[{"":1}]}}; self.assertEqual(pointer.get_value(d,"/a~1b/~0/0/"),1)
        out=pointer.get_value(d,""); out["a/b"]["~"].append(2); self.assertEqual(len(d["a/b"]["~"]),1)

    def test_R2_case2(self):
        for p in ["/a/01","/a/-","/a/1","/a/-1","/missing","/a/0/x"]:
            with self.assertRaises(ValueError): pointer.get_value({"a":[1]},p)
        self.assertEqual(pointer.get_value({"01":2},"/01"),2)

    def test_R3_case1(self):
        d={"a":[1,2]}; out=api.apply_basic(d,{"op":"add","path":"/a/1","value":{"x":[3]}})
        self.assertEqual(out,{"a":[1,{"x":[3]},2]}); self.assertEqual(d,{"a":[1,2]})
        self.assertEqual(api.apply_basic(d,{"op":"remove","path":""}),None)
        self.assertEqual(api.apply_basic(d,{"op":"replace","path":"","value":[9]}),[9])

    def test_R3_case2(self):
        for op in [{"op":"test","path":"","value":True},{"op":"replace","path":"/x","value":1},{"op":"add","path":"/x/y","value":1},{"op":"add","path":"/a/01","value":1},{"op":"add","path":"/x"}]:
            with self.assertRaises(ValueError): api.apply_basic(1 if op["op"]=="test" else {"a":[]},op)
        self.assertEqual(api.apply_basic(1,{"op":"test","path":"","value":1.0}),1)

    def test_R4_case1(self):
        self.assertEqual(api.apply_move_copy([0,1,2,3],{"op":"move","from":"/0","path":"/2"}),[1,2,0,3])
        self.assertEqual(api.apply_move_copy({"a":{"x":1}},{"op":"move","from":"/a","path":""}),{"x":1})
        d={"a":{"x":[]}}; out=api.apply_move_copy(d,{"op":"copy","from":"/a","path":"/a/copy"})
        out["a"]["copy"]["x"].append(1); self.assertEqual(out["a"]["x"],[]); self.assertEqual(d,{"a":{"x":[]}})

    def test_R4_case2(self):
        with self.assertRaises(ValueError): api.apply_move_copy({"a":{}},{"op":"move","from":"/a","path":"/a/x"})
        with self.assertRaises(ValueError): api.apply_move_copy({}, {"op":"move","from":"/missing","path":"/missing"})
        d={"a":[1]}; self.assertEqual(api.apply_move_copy(d,{"op":"move","from":"/a","path":"/a"}),d)

    def test_R5_case1(self):
        d={"a":[1,2,3]}; ops=[{"op":"move","from":"/a/0","path":"/a/2"},{"op":"copy","from":"/a","path":"/b"},{"op":"test","path":"/b/2","value":1}]
        before=copy.deepcopy(ops); out=api.apply_patch(d,ops)
        self.assertEqual(out,{"a":[2,3,1],"b":[2,3,1]}); self.assertEqual(d,{"a":[1,2,3]}); self.assertEqual(ops,before)

    def test_R5_case2(self):
        d={"a":[]}; ops=[{"op":"add","path":"/a/-","value":1},{"op":"remove","path":"/absent"}]
        with self.assertRaises(ValueError): api.apply_patch(d,ops)
        self.assertEqual(d,{"a":[]}); out=api.apply_patch(d,[]); out["a"].append(2); self.assertEqual(d,{"a":[]})

