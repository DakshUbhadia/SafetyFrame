import unittest
from robustness_monitor import (
    normalize_safety_eval_run_id,
    unique_safety_eval_runs,
    latest_safety_eval_run,
)


class PublicTests(unittest.TestCase):
    def test_normalize_safety_eval_run(self):
        self.assertEqual(normalize_safety_eval_run_id(" run-1 "), "run-1")

    def test_unique_safety_eval_run(self):
        records = [{"id": "b", "timestamp": 1, "alignment_score": 2},
                   {"id": "b", "timestamp": 2, "alignment_score": 3}]
        self.assertEqual(unique_safety_eval_runs(records), records[:1])

    def test_latest_safety_eval_run(self):
        records = [{"id": "a", "timestamp": 5, "alignment_score": 1},
                   {"id": "b", "timestamp": 1, "alignment_score": 2}]
        self.assertEqual(latest_safety_eval_run(records), records[0])
