import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        rows=[{'id':'x','v':[]}]; out=api.index_rows(rows); out['x']['v'].append(1); self.assertEqual(rows,[{'id':'x','v':[]}]); self.assertEqual(api.index_rows([]),{})

    def test_R1_case2(self):
        with self.assertRaises(ValueError): api.index_rows([{'id':'x'},{'id':'x'}])

    def test_R2_case1(self):
        self.assertEqual(api.diff_reports([{'id':'z'},{'id':'a','x':1,'skip':1}],[{'id':'b'},{'id':'a','x':2,'skip':3}],['x']),{'added':['b'],'removed':['z'],'changed':[{'id':'a','fields':{'x':{'before':1,'after':2}}}]})

    def test_R2_case2(self):
        self.assertEqual(api.diff_reports([{'id':'a'}],[{'id':'a','x':None}],['x'])['changed'],[]); self.assertEqual(api.diff_reports([], [{'id':'z'},{'id':'a'}],[])['added'],['a','z'])

    def test_R3_case1(self):
        d={'added':['a','b'],'removed':['c'],'changed':[{'id':'x','fields':{'z':{},'a':{}}},{'id':'y','fields':{'a':{}}}]}; self.assertEqual(api.summarize_changes(d),{'added':2,'removed':1,'changed':2,'fields':{'a':2,'z':1}})

    def test_R3_case2(self):
        self.assertEqual(api.summarize_changes(dict(added=[],removed=[],changed=[])),dict(added=0,removed=0,changed=0,fields={}))

    def test_R4_case1(self):
        self.assertEqual(api.render_markdown([{'a':'x|y','b':'q'+chr(92)+'r'+chr(10)+'s'}],['a','b']), '| a | b |\n| --- | --- |\n| x\\|y | q\\\\r<br>s |')

    def test_R4_case2(self):
        self.assertEqual(api.render_markdown([{'a':None},{}],['a']),'| a |'+chr(10)+'| --- |'+chr(10)+'|  |'+chr(10)+'|  |'); self.assertEqual(api.render_markdown([],[]),'')

    def test_R5_case1(self):
        import reporting as report
        r=report.report_changes([{'id':'a','x':1,'y':0}],[{'id':'a','x':2,'y':1}],['y','x']); self.assertEqual(r['diff'],{'added':[],'removed':[],'changed':[{'id':'a','fields':{'x':dict(before=1,after=2),'y':dict(before=0,after=1)}}]}); self.assertEqual(r['summary'],dict(added=0,removed=0,changed=1,fields={'x':1,'y':1})); self.assertEqual(r['markdown'],'| id | fields |'+chr(10)+'| --- | --- |'+chr(10)+'| a | x, y |')

    def test_R5_case2(self):
        import reporting as report
        r=report.report_changes([],[],[]); self.assertEqual(r['diff'],dict(added=[],removed=[],changed=[])); self.assertEqual(r['markdown'],'| id | fields |'+chr(10)+'| --- | --- |')

