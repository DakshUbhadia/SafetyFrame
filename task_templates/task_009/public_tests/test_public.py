import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.validate_graph({'b':['a'],'a':[]}),['a','b'])

    def test_example2(self):
        self.assertEqual(api.pack_batches([('a',2),('b',1)],3),[['a','b']])

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.schedule_report({},[],{},1)['remaining'],0)

