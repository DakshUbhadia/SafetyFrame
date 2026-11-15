import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        e=[dict(job='a',sequence=2,status='failed'),dict(job='a',sequence=1,status='complete'),dict(job='a',sequence=2,status='complete')]; self.assertEqual(api.latest_checkpoints(e),{'a':e[2]})

    def test_R1_case2(self):
        e=[dict(job='b',sequence=0,data=[])]; out=api.latest_checkpoints(e); out['b']['data'].append(1); self.assertEqual(e[0]['data'],[]); self.assertEqual(api.latest_checkpoints([]),{})

    def test_R2_case1(self):
        self.assertEqual(api.resume_jobs(['c','a','a','b'],{'a':{'status':'complete'},'b':{'status':'running'},'x':{'status':'failed'}}),['b','c'])

    def test_R2_case2(self):
        self.assertEqual(api.resume_jobs([],{'x':{'status':'failed'}}),[]); self.assertEqual(api.resume_jobs(['a'],{'a':{'status':'failed'}}),['a'])

    def test_R3_case1(self):
        self.assertEqual(api.reconcile_artifacts({'a':'1','b':'2','c':'3'},{'b':'x','c':'3','d':'4'}),{'missing':['a'],'changed':['b'],'unexpected':['d']})

    def test_R3_case2(self):
        self.assertEqual(api.reconcile_artifacts({},{}),dict(missing=[],changed=[],unexpected=[])); self.assertEqual(api.reconcile_artifacts({'b':'2','a':'1'}, {})['missing'],['a','b'])

    def test_R4_case1(self):
        c={'a':{'status':'failed','attempts':2},'b':{'status':'pending','attempts':1},'c':{'status':'running'},'d':{'status':'complete'}}; self.assertEqual(api.plan_retries(['e','a','b','c','d','e'],c,2),['b','e'])

    def test_R4_case2(self):
        for limit in [0,-1,True,1.5]:
            with self.assertRaises(ValueError): api.plan_retries([],{},limit)
        self.assertEqual(api.plan_retries([],{},1),[])

    def test_R5_case1(self):
        import reporting as report
        e=[dict(job='a',sequence=1,status='failed',attempts=1)]; r=report.recovery_report(['a','b'],e,{'x':'1'},{'x':'2'},2); self.assertEqual(r['latest'],{'a':e[0]}); self.assertEqual(r['resume'],['a','b']); self.assertEqual(r['retry'],['a','b']); self.assertEqual(r['artifacts']['changed'],['x'])

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.recovery_report([],[],{},{},1),{'latest':{},'resume':[],'retry':[],'artifacts':dict(missing=[],changed=[],unexpected=[])})

