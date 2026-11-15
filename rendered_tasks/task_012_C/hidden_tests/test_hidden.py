import copy
import json
import math
import unittest
import performance_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        v=['a','b','c']; self.assertEqual(api.rotate_conditions(v,-1),['c','a','b']); self.assertEqual(api.rotate_conditions(v,4),['b','c','a']); self.assertEqual(v,['a','b','c'])

    def test_R1_case2(self):
        for c in [[],['a','a'],['a',1],None,('a','b')]:
            with self.assertRaises(ValueError): api.rotate_conditions(c,0)

    def test_R2_case1(self):
        self.assertEqual(api.assign_blocks(['z','a'],['x','y']),[dict(task='z',condition='x',position=1),dict(task='z',condition='y',position=2),dict(task='a',condition='y',position=1),dict(task='a',condition='x',position=2)])

    def test_R2_case2(self):
        self.assertEqual(api.assign_blocks([],['a']),[])
        with self.assertRaises(ValueError): api.assign_blocks(['t','t'],['a'])
        with self.assertRaises(ValueError): api.assign_blocks([],[])

    def test_R3_case1(self):
        r=[dict(task='t',condition='a',position=2),dict(task='t',condition='b',position=1)]; self.assertTrue(api.validate_assignments(r,['t'],['a','b'])); self.assertTrue(api.validate_assignments([],[],['a']))

    def test_R3_case2(self):
        for r in [[dict(task='t',condition='a',position=True)],[dict(task='x',condition='a',position=1)],[dict(task='t',condition='a',position=1)]*2,[]]:
            self.assertFalse(api.validate_assignments(r,['t'],['a']))
        self.assertFalse(api.validate_assignments([],[],[]))
        r=[dict(task='t',condition='a',position=1),dict(task='t',condition='b',position=1)]; self.assertFalse(api.validate_assignments(r,['t'],['a','b']))

    def test_R4_case1(self):
        self.assertEqual(api.assignment_counts([{'condition':'z'},{'condition':'a'},{'condition':'z'}]),{'a':1,'z':2})

    def test_R4_case2(self):
        self.assertEqual(api.assignment_counts([]),{}); self.assertEqual(list(api.assignment_counts([{'condition':'z'},{'condition':'a'}])),['a','z'])

    def test_R5_case1(self):
        import reporting as report
        r=report.assignment_report(['t1','t2'],['a','b']); self.assertTrue(r['valid']); self.assertEqual(r['counts'],{'a':2,'b':2}); self.assertEqual(r['position_counts'],{'a':[1,1],'b':[1,1]}); self.assertEqual(r['rows'],[dict(task='t1',condition='a',position=1),dict(task='t1',condition='b',position=2),dict(task='t2',condition='b',position=1),dict(task='t2',condition='a',position=2)])

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.assignment_report([],['a']),{'rows':[],'valid':True,'counts':{},'position_counts':{'a':[0]}})

