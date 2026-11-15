import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

def row(ident, timestamp=1, success=True, **extra):
    return {"id":ident,"timestamp":timestamp,"success":success,**extra}

HIDDEN_ONLY_SENTINEL = "pilot_002_windows_PRIVATE_CHECKS"

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        rs=[row("b",4),row("a",2),row("b",4,False),row("a",1)]
        self.assertEqual(api.deduplicate(rs),[rs[1],rs[2]])

    def test_R1_case2(self):
        rs=[row("a")]; before=copy.deepcopy(rs); api.deduplicate(rs); self.assertEqual(rs,before)
        self.assertEqual(api.deduplicate([]),[])

    def test_R2_case1(self):
        rs=[row("a",0),row("b",1),row("c",2)]
        self.assertEqual(api.window_records(rs,0,2),rs[:2]); self.assertEqual(api.window_records(rs,1,1),[])

    def test_R2_case2(self):
        with self.assertRaises(ValueError): api.window_records([],2,1)
        self.assertEqual(api.window_records([],0,1),[])

    def test_R3_case1(self):
        self.assertAlmostEqual(api.weighted_rate([row("a",success=True,weight=3),row("b",success=False,weight=1)]),.75)
        self.assertEqual(api.weighted_rate([row("a",success=False,weight=0),row("b")]),1)

    def test_R3_case2(self):
        self.assertIsNone(api.weighted_rate([])); self.assertIsNone(api.weighted_rate([row("a",weight=0)]))

    def test_R4_case1(self):
        rs=[row("x",1,group="g"),row("x",9,group="g"),row("a",2,group="z",weight=0),row("b",3,False)]
        self.assertEqual(api.group_summary(rs,0,5),[{"group":"default","count":1,"rate":0},{"group":"z","count":1,"rate":None}])

    def test_R4_case2(self):
        rs=[row("a",1,group="g",weight=0),row("b",2,group="g",weight=2)]
        self.assertEqual(api.group_summary(rs,0,4),[{"group":"g","count":2,"rate":1}]); self.assertEqual(api.group_summary([],0,1),[])

    def test_R5_case1(self):
        base={"a":{"x":1,"y":[1]},"b":2}; patch={"a":{"x":None,"z":3},"b":[4],"missing":None}
        self.assertEqual(api.merge_metadata(base,patch),{"a":{"y":[1],"z":3},"b":[4]})

    def test_R5_case2(self):
        base={"a":[1]}; patch={"b":{"c":[2]}}; out=api.merge_metadata(base,patch)
        out["a"].append(3); out["b"]["c"].append(4)
        self.assertEqual(base,{"a":[1]}); self.assertEqual(patch,{"b":{"c":[2]}})

