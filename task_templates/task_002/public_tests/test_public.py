import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.parse_header([' a ','b']),['a','b'])

    def test_example2(self):
        self.assertEqual(api.convert_value(' 2 ','int'),2)

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.ingest('x\n2\n',{'x':'int'},['x'])['valid_rows'],[{'x':2}])

