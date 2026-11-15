import copy
import json
import math
import unittest
import robustness_monitor as api
import pointer



class PublicTests(unittest.TestCase):
    def test_pointer(self):
        self.assertEqual(pointer.decode_pointer("/runs/0"),["runs","0"])
    def test_add(self):
        self.assertEqual(api.apply_basic({"runs":[]},{"op":"add","path":"/runs/-","value":1}),{"runs":[1]})
    def test_patch(self):
        self.assertEqual(api.apply_patch({"x":1},[{"op":"replace","path":"/x","value":2}]),{"x":2})
