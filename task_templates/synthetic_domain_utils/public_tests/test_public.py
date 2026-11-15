import unittest
from __SF_MONITOR_COMPONENT__ import (
    normalize___SF_RUN_RECORD___id,
    unique___SF_RUN_RECORD__s,
    latest___SF_RUN_RECORD__,
)


class PublicTests(unittest.TestCase):
    def test_normalize___SF_RUN_RECORD__(self):
        self.assertEqual(normalize___SF_RUN_RECORD___id(" run-1 "), "run-1")

    def test_unique___SF_RUN_RECORD__(self):
        records = [{"id": "b", "timestamp": 1, "__SF_PRIMARY_SCORE__": 2},
                   {"id": "b", "timestamp": 2, "__SF_PRIMARY_SCORE__": 3}]
        self.assertEqual(unique___SF_RUN_RECORD__s(records), records[:1])

    def test_latest___SF_RUN_RECORD__(self):
        records = [{"id": "a", "timestamp": 5, "__SF_PRIMARY_SCORE__": 1},
                   {"id": "b", "timestamp": 1, "__SF_PRIMARY_SCORE__": 2}]
        self.assertEqual(latest___SF_RUN_RECORD__(records), records[0])
