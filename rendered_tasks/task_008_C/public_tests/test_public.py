import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.ancestors('x',{'x':'root'}),['x','root'])

    def test_example2(self):
        self.assertEqual(api.label_credit('x','x',{}),1)

    def test_example3(self):
        import reporting as report
        self.assertIsNone(report.label_report([],{})['macro'])

