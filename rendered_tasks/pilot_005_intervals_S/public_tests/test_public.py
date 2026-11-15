import copy
import json
import math
import unittest
import robustness_monitor as api
import reporting

def row(ident,group,start,end): return {"id":ident,"group":group,"start":start,"end":end}

class PublicTests(unittest.TestCase):
    def test_duration(self):
        self.assertEqual(api.parse_duration("2s"),2000)
    def test_coalesce(self):
        self.assertEqual(api.coalesce_intervals([(0,2),(1,3)]),[(0,3)])
    def test_summary(self):
        self.assertEqual(reporting.make_summary([row("a","g",0,10)],[(0,10)],1)["total_ms"],10)
