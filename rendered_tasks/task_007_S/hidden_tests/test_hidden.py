import copy
import json
import math
import unittest
import robustness_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.match_pairs({'z':5,'a':2,'x':8},{'a':1,'z':7,'q':0}),[('a',-1),('z',2)])

    def test_R1_case2(self):
        self.assertEqual(api.match_pairs({'x':0},{'y':1}),[]); d={'x':1}; api.match_pairs(d,{'x':3}); self.assertEqual(d,{'x':1})

    def test_R2_case1(self):
        self.assertEqual(api.sign_summary([-2,-1,0,1,2],1),dict(positive=1,negative=1,ties=3))

    def test_R2_case2(self):
        self.assertEqual(api.sign_summary([],0),dict(positive=0,negative=0,ties=0))
        with self.assertRaises(ValueError): api.sign_summary([],-.1)

    def test_R3_case1(self):
        v=[100,2,1,3,0]; self.assertEqual(api.trimmed_mean(v,.2),2); self.assertEqual(v,[100,2,1,3,0])

    def test_R3_case2(self):
        self.assertIsNone(api.trimmed_mean([],0)); self.assertEqual(api.trimmed_mean([1,9,2],.3),4)
        for f in [-.1,.5,1]:
            with self.assertRaises(ValueError): api.trimmed_mean([1],f)

    def test_R4_case1(self):
        self.assertEqual(api.leave_one_out([1,2,6]),[4,3.5,1.5])

    def test_R4_case2(self):
        self.assertEqual(api.leave_one_out([2,2]),[2,2]); self.assertEqual(api.leave_one_out([]),[]); self.assertEqual(api.leave_one_out([4]),[])

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.comparison_report({'a':1,'b':2},{'b':0,'a':3},0,0),{'ids':['a','b'],'deltas':[2,-2],'signs':dict(positive=1,negative=1,ties=0),'trimmed':0,'leave_one_out':[-2,2]})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.comparison_report({}, {},0,0),{'ids':[],'deltas':[],'signs':dict(positive=0,negative=0,ties=0),'trimmed':None,'leave_one_out':[]})

