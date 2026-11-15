import copy
import unittest
from performance_monitor import (
    normalize_capability_run_id,
    unique_capability_runs,
    latest_capability_run,
    mean_capability_score,
)

HIDDEN_ONLY_SENTINEL = "STAGE3_HIDDEN_TEST_MATERIAL_58d09c"


class Requirements(unittest.TestCase):
    def test_R1_strip(self):
        self.assertEqual(normalize_capability_run_id(" x "), "x")
        self.assertEqual(normalize_capability_run_id("a-b"), "a-b")

    def test_R1_invalid(self):
        for value in (None, 2, "", "  "):
            with self.assertRaises(ValueError):
                normalize_capability_run_id(value)

    def test_R2_first_order(self):
        records = [{"id": "b", "timestamp": 1, "capability_score": 2},
                   {"id": "a", "timestamp": 2, "capability_score": 4},
                   {"id": "b", "timestamp": 3, "capability_score": 9}]
        self.assertEqual(unique_capability_runs(records), records[:2])

    def test_R2_empty_unchanged(self):
        self.assertEqual(unique_capability_runs([]), [])
        records = [{"id": "b", "timestamp": 1, "capability_score": 2}]
        before = copy.deepcopy(records)
        unique_capability_runs(records)
        self.assertEqual(records, before)

    def test_R3_timestamp(self):
        records = [{"id": "a", "timestamp": 7, "capability_score": 2},
                   {"id": "b", "timestamp": 1, "capability_score": 4}]
        self.assertEqual(latest_capability_run(records), records[0])

    def test_R3_ties_empty(self):
        records = [{"id": "z", "timestamp": 7, "capability_score": 2},
                   {"id": "a", "timestamp": 7, "capability_score": 4}]
        self.assertEqual(latest_capability_run(records), records[1])
        self.assertIsNone(latest_capability_run([]))

    def test_R4_mean(self):
        records = [{"id": "a", "timestamp": 1, "capability_score": 1.5},
                   {"id": "b", "timestamp": 2, "capability_score": 4.5}]
        self.assertAlmostEqual(mean_capability_score(records), 3)

    def test_R4_empty(self):
        self.assertEqual(mean_capability_score([]), 0)
