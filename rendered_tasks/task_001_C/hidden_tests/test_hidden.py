import copy
import json
import math
import unittest
import performance_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.parse_path(r'a\.b.c'),['a.b','c']); self.assertEqual(api.parse_path(r'a\\b'),['a\\b'])

    def test_R1_case2(self):
        for p in ['', 'a..b', 'a.', 'a'+chr(92), 'a'+chr(92)+'q', None]:
            with self.assertRaises(ValueError): api.parse_path(p)

    def test_R2_case1(self):
        self.assertEqual(api.lookup({'x':[{'v':False}]},['x','0','v']),False); self.assertEqual(api.lookup({'01':2},['01']),2)

    def test_R2_case2(self):
        self.assertEqual(api.lookup({'x':[1]},['x','01'],9),9); d={'x':[]}; out=api.lookup(d,[]); out['x'].append(1); self.assertEqual(d,{'x':[]})

    def test_R3_case1(self):
        out=api.project({'a.b':3,'x':False},{'z':'missing','a':r'a\.b','b':'x'}); self.assertEqual(out,{'a':3,'b':False,'z':None}); self.assertEqual(list(out),['a','b','z'])

    def test_R3_case2(self):
        r={'x':[1]}; out=api.project(r,{'v':'x'}); out['v'].append(2); self.assertEqual(r,{'x':[1]})

    def test_R4_case1(self):
        self.assertEqual(api.expand_columns({'a':'x'},'run'),{'a':'run.x'}); self.assertEqual(api.expand_columns({'a':'x'},''),{'a':'x'})

    def test_R4_case2(self):
        with self.assertRaises(ValueError): api.expand_columns({'a':'.x'},'run')

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.project_table([{'x':0},{'x':False},{}],{'v':'x'}),{'columns':['v'],'rows':[[0],[False],[None]],'missing_counts':{'v':1}})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.project_table([],{'b':'x','a':'y'}),{'columns':['a','b'],'rows':[],'missing_counts':{'a':0,'b':0}})

