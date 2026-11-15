import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.bucket_samples([(0,1),(1,2)],1,0),{0:[1],1:[2]})

    def test_example2(self):
        self.assertEqual(api.fill_forward([1,None],1),[1,1])

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.series_report([],1,0,0,0,0,1)['values'],[None])

