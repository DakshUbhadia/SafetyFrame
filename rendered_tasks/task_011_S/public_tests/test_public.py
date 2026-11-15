import copy
import json
import math
import unittest
import robustness_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.latest_checkpoints([]),{})

    def test_example2(self):
        self.assertEqual(api.resume_jobs(['a'],{}),['a'])

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.recovery_report([],[],{},{},1)['retry'],[])

