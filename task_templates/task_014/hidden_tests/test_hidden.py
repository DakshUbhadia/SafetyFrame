import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.bucket_samples([(2,4),(-.1,3),(0,1),(1.9,2)],2,0),{-1:[3],0:[1,2],1:[4]})

    def test_R1_case2(self):
        self.assertEqual(list(api.bucket_samples([(4,1),(0,2)],2,1)),[-1,1])
        for w in [0,-1,float('inf'),float('nan')]:
            with self.assertRaises(ValueError): api.bucket_samples([],w,0)

    def test_R2_case1(self):
        self.assertEqual(api.reduce_buckets({0:[None,0,2],1:[None],2:[]}),{0:1,1:None,2:None})

    def test_R2_case2(self):
        b={1:[1,3]}; self.assertEqual(api.reduce_buckets(b),{1:2}); self.assertEqual(b,{1:[1,3]}); self.assertEqual(api.reduce_buckets({}),{})

    def test_R3_case1(self):
        self.assertEqual(api.fill_forward([None,0,None,None,None,2,None],2),[None,0,0,0,None,2,2])

    def test_R3_case2(self):
        self.assertEqual(api.fill_forward([1,None],0),[1,None]); self.assertEqual(api.fill_forward([],0),[])
        for n in [-1,True,1.5]:
            with self.assertRaises(ValueError): api.fill_forward([],n)

    def test_R4_case1(self):
        self.assertEqual(api.moving_average([None,2,None,4,None,None],2),[None,2,2,4,4,None])

    def test_R4_case2(self):
        self.assertEqual(api.moving_average([1,3,5],10),[1,2,3])
        for w in [0,True,1.5]:
            with self.assertRaises(ValueError): api.moving_average([],w)

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.series_report([(0,2),(2,6)],1,0,0,3,1,2),{'buckets':[0,1,2,3],'values':[2,None,6,None],'filled':[2,2,6,6],'smoothed':[2,2,4,6]})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.series_report([],1,0,2,1,0,1),dict(buckets=[],values=[],filled=[],smoothed=[]))

