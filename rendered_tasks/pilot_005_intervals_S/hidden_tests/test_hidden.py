import copy
import json
import math
import unittest
import robustness_monitor as api
import reporting

def row(ident,group,start,end): return {"id":ident,"group":group,"start":start,"end":end}

HIDDEN_ONLY_SENTINEL = "pilot_005_intervals_PRIVATE_CHECKS"

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        for value,expected in [(" 1.001s ",1001),("0.025m",1500),("3ms",3),(7,7),("000.001s",1)]: self.assertEqual(api.parse_duration(value),expected)

    def test_R1_case2(self):
        for value in [True,-1,".5s","1e3ms","1.01ms","1 S","1S","1.0001s"]:
            with self.assertRaises(ValueError): api.parse_duration(value)

    def test_R2_case1(self):
        rs=[(5,7),(0,2),(2,5),(1,1),(-2,-1)]
        self.assertEqual(api.coalesce_intervals(rs),[(-2,-1),(0,7)]); self.assertEqual(rs[0],(5,7))

    def test_R2_case2(self):
        self.assertEqual(api.coalesce_intervals([]),[])
        for pair in [(2,1),(True,2),(1,),[1,2,3]]:
            with self.assertRaises(ValueError): api.coalesce_intervals([pair])

    def test_R3_case1(self):
        self.assertEqual(api.subtract_intervals([(0,10),(8,15)],[(3,5),(5,7),(12,20)]),[(0,3),(7,12)])

    def test_R3_case2(self):
        self.assertEqual(api.subtract_intervals([(0,4)],[(4,5)]),[(0,4)])
        self.assertEqual(api.subtract_intervals([(0,4)],[(-1,5)]),[]); self.assertEqual(api.subtract_intervals([],[]),[])

    def test_R4_case1(self):
        rs=[row("x","old",0,10),row("x","a",20,30),row("y","a",25,40),row("z","b",0,5)]
        self.assertEqual(api.coverage_by_group(rs,[(0,3),(2,10),(20,35)]),{"a":15,"b":5})

    def test_R4_case2(self):
        self.assertEqual(api.coverage_by_group([row("a","g",0,5)],[(7,9)]),{"g":0})
        self.assertEqual(api.coverage_by_group([],[]),{})

    def test_R5_case1(self):
        rs=[row("1","b",0,5),row("2","a",0,5),row("3","c",8,8)]
        self.assertEqual(reporting.make_summary(rs,[(0,10)],1),{"total_ms":10,"active_groups":2,"groups":[{"group":"a","coverage_ms":5}]})

    def test_R5_case2(self):
        self.assertEqual(reporting.make_summary([],[],0),{"total_ms":0,"active_groups":0,"groups":[]})
        for value in [True,-1,1.5]:
            with self.assertRaises(ValueError): reporting.make_summary([],[],value)

