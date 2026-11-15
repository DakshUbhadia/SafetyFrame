import copy
import json
import math
import unittest
import performance_monitor as api

def row(ident, timestamp=1, success=True, **extra):
    return {"id":ident,"timestamp":timestamp,"success":success,**extra}

class PublicTests(unittest.TestCase):
    def test_window(self):
        self.assertEqual(len(api.window_records([row("a",1),row("b",5)],0,3)),1)
    def test_rate(self):
        self.assertEqual(api.weighted_rate([row("a",success=True),row("b",success=False)]),.5)
    def test_metadata(self):
        self.assertEqual(api.merge_metadata({"x":1},{"y":2}),{"x":1,"y":2})
