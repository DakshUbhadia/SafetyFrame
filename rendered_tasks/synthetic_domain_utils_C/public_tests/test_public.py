import unittest
from performance_monitor import (
    normalize_capability_run_id,
    unique_capability_runs,
    latest_capability_run,
)


class PublicTests(unittest.TestCase):
    def test_normalize_capability_run(self):
        self.assertEqual(normalize_capability_run_id(" run-1 "), "run-1")

    def test_unique_capability_run(self):
        records = [{"id": "b", "timestamp": 1, "capability_score": 2},
                   {"id": "b", "timestamp": 2, "capability_score": 3}]
        self.assertEqual(unique_capability_runs(records), records[:1])

    def test_latest_capability_run(self):
        records = [{"id": "a", "timestamp": 5, "capability_score": 1},
                   {"id": "b", "timestamp": 1, "capability_score": 2}]
        self.assertEqual(latest_capability_run(records), records[0])
