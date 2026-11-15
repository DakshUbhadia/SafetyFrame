import copy
import json
import math
import unittest
import robustness_monitor as api

def row(ident, timestamp=1, score=.5, **extra):
    return {"id": ident, "timestamp": timestamp, "alignment_score": score, **extra}

HIDDEN_ONLY_SENTINEL = "pilot_001_ingestion_PRIVATE_CHECKS"

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertEqual(api.normalize_record(row(" a ", note="keep")), row("a", note="keep"))
        original = row(" a "); api.normalize_record(original); self.assertEqual(original["id"], " a ")

    def test_R1_case2(self):
        for bad in [None, {}, row(" "), row("a", timestamp=True), row("a", timestamp=-1), row("a", score=True), row("a", score=float("nan")), row("a", score=2)]:
            with self.assertRaises(ValueError): api.normalize_record(bad)

    def test_R2_case1(self):
        text = "\n" + json.dumps(row(" a ")) + "\n[]\n{broken\n" + json.dumps(row("b"))
        good, bad = api.read_records(text)
        self.assertEqual([r["id"] for r in good], ["a", "b"]); self.assertEqual(bad, [3,4])

    def test_R2_case2(self):
        self.assertEqual(api.read_records(" \n\n"), ([], []))
        self.assertEqual(api.read_records(json.dumps(row("a", score=-1)))[1], [1])

    def test_R3_case1(self):
        records = [row("b",3), row("a",4), row("b",1), row("a",4,score=.8)]
        before = copy.deepcopy(records)
        self.assertEqual(api.latest_records(records), [records[3],records[0]])
        self.assertEqual(records,before)

    def test_R3_case2(self):
        self.assertEqual(api.latest_records([]), [])
        r=row("x"); out=api.latest_records([r]); out[0]["id"]="changed"; self.assertEqual(r["id"],"x")

    def test_R4_case1(self):
        records=[row("a",score=.25,group="g"),row("b",score=.75,group="g"),row("c",score=1)]
        self.assertEqual(api.group_means(records),{"g":.5,"default":1})

    def test_R4_case2(self):
        self.assertEqual(api.group_means([]), {})
        records=[row("a",score=.1),row("b",score=.3)]
        self.assertAlmostEqual(api.group_means(records)["default"],.2)

