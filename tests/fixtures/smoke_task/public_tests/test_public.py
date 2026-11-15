import unittest
from solution import normalize_id, unique_ids, latest_event


class PublicTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_id(" run-1 "), "run-1")

    def test_unique(self):
        self.assertEqual(unique_ids(["b", "a", "b"]), ["b", "a"])

    def test_latest_unsorted(self):
        events = [{"id": "new", "timestamp": 5}, {"id": "old", "timestamp": 1}]
        self.assertEqual(latest_event(events), events[0])
