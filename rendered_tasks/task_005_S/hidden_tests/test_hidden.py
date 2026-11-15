import copy
import json
import math
import unittest
import robustness_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.rank_items({'b':-1,'a':-1,'z':0}),['z','a','b'])

    def test_R1_case2(self):
        d={'c':2,'a':3,'b':2}; self.assertEqual(api.rank_items(d),['a','b','c']); self.assertEqual(d,{'c':2,'a':3,'b':2}); self.assertEqual(api.rank_items({}),[])

    def test_R2_case1(self):
        self.assertAlmostEqual(api.discounted_gain({'a':2,'b':1},['a','b'],2),3+1/math.log2(3))

    def test_R2_case2(self):
        self.assertAlmostEqual(api.discounted_gain({'a':1,'b':1},['a','a','b'],3),1.5); self.assertEqual(api.discounted_gain({},['x'],1),0); self.assertEqual(api.discounted_gain({'x':2},['x'],-1),0)

    def test_R3_case1(self):
        self.assertEqual(api.pairwise_accuracy({'a':3,'b':2,'c':1},{'a':1,'b':1,'c':0}),5/6)

    def test_R3_case2(self):
        self.assertIsNone(api.pairwise_accuracy({'a':1,'b':1},{'a':0,'b':3})); self.assertEqual(api.pairwise_accuracy({'a':2,'b':1,'x':5},{'a':0,'b':1,'z':9}),0)

    def test_R4_case1(self):
        self.assertEqual(api.top_overlap(['a','a','b'],['a','c'],2),.5)

    def test_R4_case2(self):
        self.assertEqual(api.top_overlap([],[],3),1); self.assertEqual(api.top_overlap(['a'],['b'],0),1); self.assertEqual(api.top_overlap(['a'],['b'],1),0)

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.ranking_report({'a':1,'b':0},{'b':2,'a':1},1),{'order':['b','a'],'gain':0,'pairwise':0,'overlap':0})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.ranking_report({}, {}, 2),{'order':[],'gain':0,'pairwise':None,'overlap':1})

