import copy
import json
import math
import unittest
import performance_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.classify([-1,0,1,2,None],0,1),['low','ok','ok','high','missing'])

    def test_R1_case2(self):
        self.assertEqual(api.classify([1,None],1,1),['ok','missing'])
        with self.assertRaises(ValueError): api.classify([],2,1)

    def test_R2_case1(self):
        self.assertEqual(api.breach_streaks(['low','low','high','high','missing','high','ok','low']),[1,2,1,2,0,1,0,1])

    def test_R2_case2(self):
        self.assertEqual(api.breach_streaks([]),[]); self.assertEqual(api.breach_streaks(['ok','missing']),[0,0])

    def test_R3_case1(self):
        labels=['high','high','high','ok','low','low','ok','high','high']; self.assertEqual(api.alert_events(labels,2,4),[dict(index=1,side='high'),dict(index=8,side='high')])

    def test_R3_case2(self):
        self.assertEqual(api.alert_events(['low','high','high'],1,0),[dict(index=0,side='low'),dict(index=1,side='high')])
        for m,c in [(0,0),(1,-1),(True,0),(1,True)]:
            with self.assertRaises(ValueError): api.alert_events([],m,c)

    def test_R4_case1(self):
        self.assertEqual(api.merge_episodes([5,1,2,2,8],3),[dict(start=1,end=8,count=4)])

    def test_R4_case2(self):
        self.assertEqual(api.merge_episodes([2,1,1],0),[dict(start=1,end=1,count=1),dict(start=2,end=2,count=1)]); self.assertEqual(api.merge_episodes([],1),[])
        with self.assertRaises(ValueError): api.merge_episodes([],-1)
        with self.assertRaises(ValueError): api.merge_episodes([],True)

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.alert_report([2,2,None,-1,-1],0,1,2,0,3),{'labels':['high','high','missing','low','low'],'streaks':[1,2,0,1,2],'events':[dict(index=1,side='high'),dict(index=4,side='low')],'episodes':[dict(start=1,end=4,count=2)],'missing':1})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.alert_report([],0,1,1,0,1),{'labels':[],'streaks':[],'events':[],'episodes':[],'missing':0})

