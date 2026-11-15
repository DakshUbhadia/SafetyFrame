import copy
import json
import math
import unittest
import robustness_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.decide([.2,.5],.5),[0,1])

    def test_example2(self):
        self.assertEqual(api.confusion([1],[0])['fn'],1)

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.decision_report([],[],.5,{})['cost'],0)

