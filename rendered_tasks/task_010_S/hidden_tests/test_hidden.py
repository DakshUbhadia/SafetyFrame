import copy
import json
import math
import unittest
import robustness_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.deep_merge({'x':{'a':1,'b':2},'v':[1]},{'x':{'b':None},'v':[2]}),{'x':{'a':1,'b':None},'v':[2]})

    def test_R1_case2(self):
        b={'a':[1]}; o={'b':{'x':2}}; r=api.deep_merge(b,o); r['a'].append(3); r['b']['x']=4; self.assertEqual(b,{'a':[1]}); self.assertEqual(o,{'b':{'x':2}}); self.assertIsNone(api.deep_merge({'a':1},None))

    def test_R2_case1(self):
        self.assertEqual(api.expand_grid({'b':[2,1],'a':['x','x']}),[{'a':'x','b':2},{'a':'x','b':1},{'a':'x','b':2},{'a':'x','b':1}])

    def test_R2_case2(self):
        self.assertEqual(api.expand_grid({}),[{}]); self.assertEqual(api.expand_grid({'x':[],'y':[1]}),[])

    def test_R3_case1(self):
        items=[{'x':[]},1,2,3]; out=api.select_shard(items,0,2); self.assertEqual(out,[{'x':[]},2]); out[0]['x'].append(1); self.assertEqual(items[0],{'x':[]})

    def test_R3_case2(self):
        self.assertEqual(api.select_shard([],1,2),[])
        for i,c in [(0,0),(-1,2),(2,2),(True,2),(0,True),(0,1.5)]:
            with self.assertRaises(ValueError): api.select_shard([],i,c)

    def test_R4_case1(self):
        import hashlib
        expected=hashlib.sha256('{"a":1,"z":"é"}'.encode('utf-8')).hexdigest(); self.assertEqual(api.canonical_fingerprint({'z':'é','a':1}),expected)

    def test_R4_case2(self):
        self.assertEqual(api.canonical_fingerprint({'b':{'y':2,'x':1},'a':[]}),api.canonical_fingerprint({'a':[],'b':{'x':1,'y':2}})); self.assertNotEqual(api.canonical_fingerprint([1,2]),api.canonical_fingerprint([2,1]))
        with self.assertRaises(ValueError): api.canonical_fingerprint({'x':float('nan')})

    def test_R5_case1(self):
        import reporting as report
        import hashlib
        r=report.configuration_report({'nested':{'x':1}}, {'v':[1,2,3]},1,2); self.assertEqual(r,{'configurations':[{'nested':{'x':1},'v':2}],'total':3,'fingerprints':[hashlib.sha256(b'{"nested":{"x":1},"v":2}').hexdigest()]})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.configuration_report({}, {'x':[]},0,1),{'configurations':[],'fingerprints':[],'total':0})

