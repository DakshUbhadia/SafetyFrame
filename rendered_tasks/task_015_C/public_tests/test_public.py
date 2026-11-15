import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.category_counts([{'x':'a'},{'x':'a'}],'x'),{'a':2})

    def test_example2(self):
        self.assertEqual(api.jensen_shannon([1,0],[0,1]),1)

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.drift_report([],[],'x',0)['divergence'],0)

