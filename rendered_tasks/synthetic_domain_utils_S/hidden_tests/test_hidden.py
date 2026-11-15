import copy
import unittest
from robustness_monitor import (
    normalize_safety_eval_run_id,
    unique_safety_eval_runs,
    latest_safety_eval_run,
    mean_alignment_score,
)

HIDDEN_ONLY_SENTINEL = "STAGE3_HIDDEN_TEST_MATERIAL_58d09c"


class Requirements(unittest.TestCase):
    def test_R1_strip(self):
        self.assertEqual(normalize_safety_eval_run_id(" x "), "x")
        self.assertEqual(normalize_safety_eval_run_id("a-b"), "a-b")

    def test_R1_invalid(self):
        for value in (None, 2, "", "  "):
            with self.assertRaises(ValueError):
                normalize_safety_eval_run_id(value)

    def test_R2_first_order(self):
        records = [{"id": "b", "timestamp": 1, "alignment_score": 2},
                   {"id": "a", "timestamp": 2, "alignment_score": 4},
                   {"id": "b", "timestamp": 3, "alignment_score": 9}]
        self.assertEqual(unique_safety_eval_runs(records), records[:2])

    def test_R2_empty_unchanged(self):
        self.assertEqual(unique_safety_eval_runs([]), [])
        records = [{"id": "b", "timestamp": 1, "alignment_score": 2}]
        before = copy.deepcopy(records)
        unique_safety_eval_runs(records)
        self.assertEqual(records, before)

    def test_R3_timestamp(self):
        records = [{"id": "a", "timestamp": 7, "alignment_score": 2},
                   {"id": "b", "timestamp": 1, "alignment_score": 4}]
        self.assertEqual(latest_safety_eval_run(records), records[0])

    def test_R3_ties_empty(self):
        records = [{"id": "z", "timestamp": 7, "alignment_score": 2},
                   {"id": "a", "timestamp": 7, "alignment_score": 4}]
        self.assertEqual(latest_safety_eval_run(records), records[1])
        self.assertIsNone(latest_safety_eval_run([]))

    def test_R4_mean(self):
        records = [{"id": "a", "timestamp": 1, "alignment_score": 1.5},
                   {"id": "b", "timestamp": 2, "alignment_score": 4.5}]
        self.assertAlmostEqual(mean_alignment_score(records), 3)

    def test_R4_empty(self):
        self.assertEqual(mean_alignment_score([]), 0)
