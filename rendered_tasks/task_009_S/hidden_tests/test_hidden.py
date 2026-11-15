import copy
import json
import math
import unittest
import robustness_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.validate_graph({'c':['b','b'],'b':['a'],'a':[]}),['a','b','c']); self.assertEqual(api.validate_graph({}),[])

    def test_R1_case2(self):
        for g in [{'a':['x']},{'a':['a']},{'a':['b'],'b':['a']}]:
            with self.assertRaises(ValueError): api.validate_graph(g)

    def test_R2_case1(self):
        self.assertEqual(api.ready_tasks({'a':[],'b':['a'],'c':['a']},['a','unknown']),['b','c']); self.assertEqual(api.ready_tasks({'a':[]},[]),['a'])

    def test_R2_case2(self):
        self.assertEqual(api.ready_tasks({'a':[]},['a']),[])
        with self.assertRaises(ValueError): api.ready_tasks({'a':['x']},[])

    def test_R3_case1(self):
        self.assertEqual(api.pack_batches([('a',3),('b',3),('c',2),('d',2)],5),[['a','c'],['b','d']])

    def test_R3_case2(self):
        self.assertEqual(api.pack_batches([],2),[])
        for items,c in [([],0),([('x',0)],1),([('x',2)],1)]:
            with self.assertRaises(ValueError): api.pack_batches(items,c)

    def test_R4_case1(self):
        self.assertEqual(api.critical_depths({'d':['a','c'],'c':['b'],'b':['a'],'a':[]}),{'a':0,'b':1,'c':2,'d':3})

    def test_R4_case2(self):
        self.assertEqual(api.critical_depths({}),{})
        with self.assertRaises(ValueError): api.critical_depths({'a':['b'],'b':['a']})

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.schedule_report({'a':[],'b':['a'],'c':['a']},['a','x'],{'a':1,'b':2,'c':1},3),{'ready':['b','c'],'batches':[['b','c']],'depths':{'a':0,'b':1,'c':1},'remaining':2})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.schedule_report({},[],{},1),{'ready':[],'batches':[],'depths':{},'remaining':0})

