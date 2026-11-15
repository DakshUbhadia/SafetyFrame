import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.deep_merge({'a':1},{'b':2}),{'a':1,'b':2})

    def test_example2(self):
        self.assertEqual(api.expand_grid({}),[{}])

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.configuration_report({}, {},0,1)['total'],1)

