import copy
import json
import math
import unittest
import robustness_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.parse_path('run.id'),['run','id'])

    def test_example2(self):
        self.assertEqual(api.project({'x':0},{'v':'x'}),{'v':0})

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.project_table([{'x':2}],{'v':'x'})['rows'],[[2]])

