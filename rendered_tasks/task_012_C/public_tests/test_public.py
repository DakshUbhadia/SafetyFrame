import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.rotate_conditions(['a','b'],1),['b','a'])

    def test_example2(self):
        self.assertEqual(api.assign_blocks(['t'],['c']),[dict(task='t',condition='c',position=1)])

    def test_example3(self):
        import reporting as report
        self.assertTrue(report.assignment_report(['t'],['a','b'])['valid'])

