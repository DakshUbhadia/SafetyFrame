import copy
import json
import math
import unittest
import robustness_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.match_pairs({'x':1},{'x':3}),[('x',2)])

    def test_example2(self):
        self.assertEqual(api.trimmed_mean([1,2,3],0),2)

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.comparison_report({}, {},0,0)['ids'],[])

