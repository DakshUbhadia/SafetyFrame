import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.flatten_record({'a':{},'b':[1]}),{('a',):{},('b',):[1]}); self.assertEqual(api.flatten_record({}),{():{}})

    def test_R1_case2(self):
        r={'x':[1]}; o=api.flatten_record(r); o[('x',)].append(2); self.assertEqual(r,{'x':[1]})

    def test_R2_case1(self):
        self.assertEqual(api.unflatten_record({('a','b'):1,('a','c'):[]}),{'a':{'b':1,'c':[]}})

    def test_R2_case2(self):
        for f in [{():{},('x',):1},{('a',):{},('a','b'):2},{(1,):2},{():1}]:
            with self.assertRaises(ValueError): api.unflatten_record(f)

    def test_R3_case1(self):
        self.assertEqual(api.to_columns([{'x':1},{'y':2}]),{('x',):[1,None],('y',):[None,2]})

    def test_R3_case2(self):
        self.assertEqual(api.to_columns([]),{}); self.assertEqual(api.to_columns([{},{}]),{():[{},{}]})

    def test_R4_case1(self):
        self.assertEqual(api.from_columns({('x',):[1,None]}),[{'x':1},{}])

    def test_R4_case2(self):
        with self.assertRaises(ValueError): api.from_columns({('x',):[1],('y',):[]})
        self.assertEqual(api.from_columns({}),[])

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.roundtrip_report([{'a':1},{'b':2}]),{'columns':{('a',):[1,None],('b',):[None,2]},'row_count':2,'missing_cells':2})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.roundtrip_report([]),{'columns':{},'row_count':0,'missing_cells':0})

