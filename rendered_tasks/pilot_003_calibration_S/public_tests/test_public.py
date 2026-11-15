import copy
import json
import math
import unittest
import robustness_monitor as api
import reporting

def row(p,y,w=1): return {"probability":p,"label":y,"weight":w}

class PublicTests(unittest.TestCase):
    def test_brier(self):
        self.assertAlmostEqual(api.brier_score([row(0,0),row(1,1)]),0)
    def test_bins(self):
        self.assertEqual([g["count"] for g in api.calibration_bins([row(.1,0),row(.9,1)],2)],[1,1])
    def test_report(self):
        self.assertEqual(set(reporting.make_report([row(.1,0),row(.9,1)],2,[.5])),{"brier","bins","threshold","ece"})
