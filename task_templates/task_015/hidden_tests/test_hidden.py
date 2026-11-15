import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.category_counts([{'x':''},{'x':None},{},{'x':'a'},{'x':''}],'x'),{'':2,'a':1})

    def test_R1_case2(self):
        self.assertEqual(api.category_counts([],'x'),{}); rows=[{'x':'a'}]; api.category_counts(rows,'x'); self.assertEqual(rows,[{'x':'a'}])

    def test_R2_case1(self):
        self.assertEqual(api.aligned_proportions({'b':2},{'a':2},1),{'categories':['a','b'],'left':[.25,.75],'right':[.75,.25]})

    def test_R2_case2(self):
        self.assertEqual(api.aligned_proportions({'a':0},{},0),{'categories':['a'],'left':[0],'right':[0]}); self.assertEqual(api.aligned_proportions({}, {},1),dict(categories=[],left=[],right=[]))
        for a in [-1,float('inf'),float('nan')]:
            with self.assertRaises(ValueError): api.aligned_proportions({}, {},a)

    def test_R3_case1(self):
        self.assertEqual(api.jensen_shannon([2,0],[0,3]),1); self.assertEqual(api.jensen_shannon([2,4],[1,2]),0); self.assertEqual(api.jensen_shannon([0],[1]),.5); self.assertEqual(api.jensen_shannon([],[]),0)

    def test_R3_case2(self):
        for a,b in [([1],[]),([-1],[1]),([float('nan')],[1]),([1],[float('inf')])]:
            with self.assertRaises(ValueError): api.jensen_shannon(a,b)

    def test_R4_case1(self):
        self.assertEqual(api.rank_changes(['z','a','b'],[.5,.5,0],[0,0,1]),[dict(category='b',delta=1),dict(category='a',delta=-.5),dict(category='z',delta=-.5)])

    def test_R4_case2(self):
        self.assertEqual(api.rank_changes([],[],[]),[])
        with self.assertRaises(ValueError): api.rank_changes(['x'],[],[])

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.drift_report([{'g':'a'}],[{'g':'b'}],'g',0),{'categories':['a','b'],'reference':[1,0],'current':[0,1],'divergence':1,'changes':[dict(category='a',delta=-1),dict(category='b',delta=1)]})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.drift_report([],[],'g',0),{'categories':[],'reference':[],'current':[],'divergence':0,'changes':[]})

