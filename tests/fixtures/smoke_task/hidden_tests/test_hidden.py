import unittest
from solution import normalize_id, unique_ids, latest_event, mean_score

HIDDEN_ONLY_SENTINEL = "DO_NOT_REVEAL_HIDDEN_REQUIREMENT_RESULTS_8b2e"


class Requirements(unittest.TestCase):
    def test_R1(self):
        self.assertEqual(normalize_id(" x "), "x")
        for value in (None, 1, "", "   "):
            with self.assertRaises(ValueError):
                normalize_id(value)

    def test_R2(self):
        self.assertEqual(unique_ids(["c", "a", "c", "b", "a"]), ["c", "a", "b"])
        self.assertEqual(unique_ids([]), [])

    def test_R3(self):
        events = [{"id": "a", "timestamp": 3}, {"id": "z", "timestamp": 3}]
        self.assertEqual(latest_event(events), events[0])
        self.assertIsNone(latest_event([]))

    def test_R4(self):
        self.assertEqual(mean_score([]), 0)
        self.assertEqual(mean_score([1, 2, 3]), 2)
