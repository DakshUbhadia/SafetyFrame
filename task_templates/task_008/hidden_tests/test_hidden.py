import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.ancestors('leaf',{'leaf':'mid','mid':'root','root':None}),['leaf','mid','root']); self.assertEqual(api.ancestors('absent',{}),['absent'])

    def test_R1_case2(self):
        for p in [{'a':'a'},{'a':'b','b':'a'}]:
            with self.assertRaises(ValueError): api.ancestors('a',p)

    def test_R2_case1(self):
        p={'a':'b','b':'c'}; self.assertEqual(api.label_credit('a','b',p),.5); self.assertEqual(api.label_credit('a','c',p),1/3); self.assertEqual(api.label_credit('b','a',p),0)

    def test_R2_case2(self):
        self.assertEqual(api.label_credit('a','z',{}),0)
        with self.assertRaises(ValueError): api.label_credit('a','a',{'a':'a'})

    def test_R3_case1(self):
        self.assertEqual(api.aggregate_labels([{'label':'x','__SF_PRIMARY_SCORE__':0},{'label':'x','__SF_PRIMARY_SCORE__':1},{'label':'y','__SF_PRIMARY_SCORE__':.2}]),{'x':dict(count=2,total=1,mean=.5),'y':dict(count=1,total=.2,mean=.2)})

    def test_R3_case2(self):
        self.assertEqual(api.aggregate_labels([]),{}); r=[{'label':'x','__SF_PRIMARY_SCORE__':1}]; api.aggregate_labels(r); self.assertEqual(r,[{'label':'x','__SF_PRIMARY_SCORE__':1}])

    def test_R4_case1(self):
        self.assertEqual(api.macro_groups({'a':dict(count=10,mean=1),'b':dict(count=1,mean=0),'c':dict(count=0,mean=9)}),.5)

    def test_R4_case2(self):
        self.assertIsNone(api.macro_groups({})); self.assertIsNone(api.macro_groups({'x':dict(count=0,mean=3)}))

    def test_R5_case1(self):
        import reporting as report
        r=report.label_report([{'expected':'a','predicted':'b'},{'expected':'c','predicted':'c'}],{'a':'b'}); self.assertEqual(r['credits'],[.5,1]); self.assertEqual(r['macro'],.75); self.assertEqual(r['groups']['a'],dict(count=1,total=.5,mean=.5))

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.label_report([],{}),{'credits':[],'groups':{},'macro':None})

