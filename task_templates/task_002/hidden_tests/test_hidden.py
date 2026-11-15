import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.parse_header([' a ','b']),['a','b'])

    def test_R1_case2(self):
        for names in [['a',' a '],['']]:
            with self.assertRaises(ValueError): api.parse_header(names)

    def test_R2_case1(self):
        self.assertEqual(api.convert_value('-02','int'),-2); self.assertIs(api.convert_value('false','bool'),False); self.assertIs(api.convert_value('true','bool'),True); self.assertIsNone(api.convert_value(' ','str')); self.assertEqual(api.convert_value(' 2.5e1 ','float'),25); self.assertEqual(api.convert_value(' text ','str'),'text')

    def test_R2_case2(self):
        for value,kind in [('True','bool'),('1.0','int'),('nan','float'),('','unknown')]:
            with self.assertRaises(ValueError): api.convert_value(value,kind)

    def test_R3_case1(self):
        self.assertEqual(api.read_table(' a,b\n"x,y",2\n\n'),[{'a':'x,y','b':'2'}])

    def test_R3_case2(self):
        self.assertEqual(api.read_table(''),[]);
        with self.assertRaises(ValueError): api.read_table('a,b\n1\n')

    def test_R4_case1(self):
        v,e=api.validate_rows([{'x':'2','y':'true'},{'x':'bad','y':'TRUE'}],{'y':'bool','x':'int'},['x']); self.assertEqual(v,[{'x':2,'y':True}]); self.assertEqual(e,[{'row':2,'columns':['x','y']}])

    def test_R4_case2(self):
        v,e=api.validate_rows([{}, {'x':'0','extra':'x'}],{'x':'int'},['x']); self.assertEqual(v,[{'x':0}]); self.assertEqual(e,[{'row':1,'columns':['x']}])

    def test_R5_case1(self):
        import reporting as report
        self.assertEqual(report.ingest('x\n1\nbad\n',{'x':'int'},['x']),{'valid_rows':[{'x':1}],'errors':[{'row':2,'columns':['x']}],'total_rows':2})

    def test_R5_case2(self):
        import reporting as report
        with self.assertRaises(ValueError): report.ingest('x,x\n1,2',{'x':'int'},[])
        self.assertEqual(report.ingest('',{'x':'int'},[]),dict(valid_rows=[],errors=[],total_rows=0))

