import copy
import json
import math
import unittest
import performance_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.decide([0,.5,1],.5),[0,1,1])

    def test_R1_case2(self):
        self.assertEqual(api.decide([0,1],0),[1,1]); self.assertEqual(api.decide([],1),[])

    def test_R2_case1(self):
        self.assertEqual(api.confusion([1,0,0,1],[1,1,0,0]),{'tp':1,'fp':1,'tn':1,'fn':1})

    def test_R2_case2(self):
        self.assertEqual(api.confusion([],[]),dict(tp=0,fp=0,tn=0,fn=0))
        with self.assertRaises(ValueError): api.confusion([1],[])

    def test_R3_case1(self):
        self.assertEqual(api.decision_cost({'tp':2,'fp':3,'fn':1},{'fp':2,'fn':5}),11)

    def test_R3_case2(self):
        self.assertEqual(api.decision_cost({}, {'fp':10}),0); self.assertEqual(api.decision_cost({'fp':2},{}),0)

    def test_R4_case1(self):
        self.assertEqual(api.best_threshold([1,0],[.6,.4],[.2,.5,.8],{'fp':2,'fn':1}),{'threshold':.5,'cost':0})

    def test_R4_case2(self):
        self.assertEqual(api.best_threshold([],[],[.2,.8,.8],{}),{'threshold':.8,'cost':0})
        with self.assertRaises(ValueError): api.best_threshold([],[],[],{})
        with self.assertRaises(ValueError): api.best_threshold([1],[],[.5],{})

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.decision_report([1,0,1],[.8,.7,.2],.5,{'fp':2,'fn':4}),{'decisions':[1,1,0],'counts':dict(tp=1,fp=1,tn=0,fn=1),'cost':6,'precision':.5,'recall':.5})

    def test_R5_case2(self):
        import reporting as report
        r=report.decision_report([0],[0],1,{}); self.assertIsNone(r['precision']); self.assertIsNone(r['recall'])

