import copy
import json
import math
import unittest
import performance_monitor as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.convert_score(1,'fraction'),1); self.assertEqual(api.convert_score(0,'percent'),0)

    def test_R1_case2(self):
        for value,unit in [(True,'fraction'),(101,'percent'),(float('inf'),'fraction'),(.5,'other')]:
            with self.assertRaises(ValueError): api.convert_score(value,unit)

    def test_R2_case1(self):
        self.assertEqual(api.rename_fields({'a':1,'b':2},{'a':'b','b':'a'}),{'b':1,'a':2})

    def test_R2_case2(self):
        with self.assertRaises(ValueError): api.rename_fields({'a':1,'b':2},{'a':'b'})
        r={'a':[]}; o=api.rename_fields(r,{}); o['a'].append(1); self.assertEqual(r,{'a':[]})

    def test_R3_case1(self):
        self.assertEqual(api.migrate_row({'version':1,'run_id':' x ','score':25}),{'version':2,'id':'x','capability_score':.25,'metadata':{}}); row={'version':2,'id':' y ','capability_score':.7,'metadata':{'x':[]},'extra':1}; out=api.migrate_row(row); self.assertEqual(out,{'version':2,'id':'y','capability_score':.7,'metadata':{'x':[]}}); out['metadata']['x'].append(1); self.assertEqual(row['metadata'],{'x':[]})

    def test_R3_case2(self):
        for row in [{'version':True,'run_id':'x','score':2},{'version':2,'id':'x'},{'version':2,'id':' ','capability_score':.5}]:
            with self.assertRaises(ValueError): api.migrate_row(row)

    def test_R4_case1(self):
        v,e=api.migrate_table([{'version':1,'run_id':'a','score':50},{'version':9},{'version':2,'id':'b','capability_score':0}]); self.assertEqual([r['id'] for r in v],['a','b']); self.assertEqual(e,[2])

    def test_R4_case2(self):
        self.assertEqual(api.migrate_table([]),([],[]))

    def test_R5_case1(self):
        import reporting as report
        rows=[{'version':1,'run_id':'x','score':50},{'version':2,'id':'x','capability_score':1}]; self.assertEqual(report.migration_report(rows),{'migrated':[{'version':2,'id':'x','capability_score':.5,'metadata':{}},{'version':2,'id':'x','capability_score':1,'metadata':{}}],'errors':[],'duplicate_ids':['x']})

    def test_R5_case2(self):
        import reporting as report
        self.assertEqual(report.migration_report([{'version':8}]),dict(migrated=[],errors=[1],duplicate_ids=[]))

