import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.classify([0,1,2],0,1),['ok','ok','high'])

    def test_example2(self):
        self.assertEqual(api.breach_streaks(['high','high','ok']),[1,2,0])

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.alert_report([],0,1,1,0,1)['events'],[])

