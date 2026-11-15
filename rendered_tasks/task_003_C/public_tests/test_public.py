import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.flatten_record({'x':{'y':2}}),{('x','y'):2})

    def test_example2(self):
        self.assertEqual(api.unflatten_record({('x',):2}),{'x':2})

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.roundtrip_report([{'x':1}])['row_count'],1)

