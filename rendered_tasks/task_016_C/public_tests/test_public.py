import copy
import json
import math
import unittest
import performance_monitor as api

class PublicTests(unittest.TestCase):
    def test_example1(self):
        self.assertEqual(api.index_rows([{'id':'x'}]),{'x':{'id':'x'}})

    def test_example2(self):
        self.assertEqual(api.diff_reports([],[],[])['changed'],[])

    def test_example3(self):
        import reporting as report
        self.assertEqual(report.report_changes([],[],[])['summary']['changed'],0)

