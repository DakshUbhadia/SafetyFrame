import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.rank_items({'b':1,'a':1}),['a','b'])

    def test_example2(self):
        self.assertEqual(api.discounted_gain({'x':1},['x'],1),1)

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.ranking_report({'a':1},{'a':2},1)['overlap'],1)

