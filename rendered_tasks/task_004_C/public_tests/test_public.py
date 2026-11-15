import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.convert_score(50,'percent'),.5)

    def test_example2(self):
        self.assertEqual(api.rename_fields({'a':1},{'a':'b'}),{'b':1})

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.migration_report([])['duplicate_ids'],[])

