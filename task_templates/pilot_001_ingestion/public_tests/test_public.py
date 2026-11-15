import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

def row(ident, timestamp=1, score=.5, **extra):
    return {"id": ident, "timestamp": timestamp, "__SF_PRIMARY_SCORE__": score, **extra}

class PublicTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(api.normalize_record(row(" a "))["id"], "a")
    def test_lines(self):
        good, bad = api.read_records(json.dumps(row("a")) + "\nnot-json")
        self.assertEqual(([r["id"] for r in good], bad), (["a"], [2]))
    def test_means(self):
        self.assertEqual(api.group_means([row("a", score=0), row("b", score=1)]), {"default": .5})
