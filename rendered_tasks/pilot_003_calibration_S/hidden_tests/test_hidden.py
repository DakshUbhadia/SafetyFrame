import copy
import json
import math
import unittest
import robustness_monitor as api
import reporting

def row(p,y,w=1): return {"probability":p,"label":y,"weight":w}

HIDDEN_ONLY_SENTINEL = "pilot_003_calibration_PRIVATE_CHECKS"

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        self.assertAlmostEqual(api.brier_score([row(.2,0,3),row(.6,1,1)]),.07)

    def test_R1_case2(self):
        self.assertIsNone(api.brier_score([])); self.assertIsNone(api.brier_score([row(.5,1,0)]))

    def test_R2_case1(self):
        out=api.calibration_bins([row(0,0),row(.5,1,3),row(1,1),row(.2,1,0)],2)
        self.assertEqual([g["count"] for g in out],[2,2]); self.assertEqual(out[0]["positive_rate"],0)
        self.assertAlmostEqual(out[1]["mean_probability"],.625); self.assertEqual(out[1]["weight"],4)

    def test_R2_case2(self):
        out=api.calibration_bins([],2); self.assertEqual(len(out),2); self.assertIsNone(out[0]["mean_probability"])
        for bins in [0,-1,True,1.5]:
            with self.assertRaises(ValueError): api.calibration_bins([],bins)

    def test_R3_case1(self):
        out=api.choose_threshold([row(.8,1),row(.4,0)],[.2,.5,.8,.5])
        self.assertEqual(out,{"threshold":.8,"f1":1,"precision":1,"recall":1})

    def test_R3_case2(self):
        self.assertIsNone(api.choose_threshold([],[]))
        self.assertEqual(api.choose_threshold([],[.1,.9])["threshold"],.9)
        self.assertEqual(api.choose_threshold([row(.8,1,0)],[.5])["f1"],0)

    def test_R4_case1(self):
        rs=[row(.2,0,3),row(.8,1,1)]; before=copy.deepcopy(rs)
        report=reporting.make_report(rs,2,[.5]); self.assertAlmostEqual(report["ece"],.2); self.assertAlmostEqual(report["brier"],.04)
        self.assertEqual(rs,before)

    def test_R4_case2(self):
        report=reporting.make_report([],3,[]); self.assertIsNone(report["ece"]); self.assertIsNone(report["brier"]); self.assertIsNone(report["threshold"])
        self.assertEqual(len(report["bins"]),3)

