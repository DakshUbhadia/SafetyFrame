import copy
import json
import math
import unittest
import robustness_monitor as api

def event(eid,ident,action): return {"event_id":eid,"id":ident,"action":action}
def record(ident="a",state="queued",attempts=0): return {"id":ident,"state":state,"attempts":attempts}

HIDDEN_ONLY_SENTINEL = "pilot_004_registry_PRIVATE_CHECKS"

class Requirements(unittest.TestCase):
    def test_R1_case1(self):
        a=api.new_registry(); b=api.new_registry(); a["runs"]["x"]={}; self.assertEqual(b,{"version":0,"runs":{},"seen":{}})

    def test_R1_case2(self):
        self.assertEqual(api.new_registry()["version"],0); self.assertEqual(set(api.new_registry()),{"version","runs","seen"})

    def test_R2_case1(self):
        self.assertEqual(api.resolve_config({"x":{"a":1,"b":2},"y":[1]},{"x":{"a":None,"c":3},"y":[2],"z":None}),{"x":{"b":2,"c":3},"y":[2]})

    def test_R2_case2(self):
        base={"x":[1]}; patch={"y":{"z":[2]}}; out=api.resolve_config(base,patch); out["x"].append(3); out["y"]["z"].append(4)
        self.assertEqual(base,{"x":[1]}); self.assertEqual(patch,{"y":{"z":[2]}})

    def test_R3_case1(self):
        r={**record(state="failed",attempts=2),"metadata":{"tags":[1]}}; out=api.transition(r,"retry")
        self.assertEqual((out["state"],out["attempts"]),("queued",3)); out["metadata"]["tags"].append(2); self.assertEqual(r["metadata"]["tags"],[1])

    def test_R3_case2(self):
        for state,action in [("queued","complete"),("completed","retry"),("running","start")]:
            with self.assertRaises(ValueError): api.transition(record(state=state),action)

    def test_R4_case1(self):
        r={"version":0,"runs":{},"seen":{}}; es=[event("e1","a","register"),event("e2","a","start"),event("e3","a","fail"),event("e4","a","retry")]
        out=api.apply_batch(r,es,0); self.assertEqual(out["version"],1); self.assertEqual(out["runs"]["a"],record(attempts=1)); self.assertEqual(api.apply_batch(out,es,1),out)
        self.assertEqual(r,{"version":0,"runs":{},"seen":{}})

    def test_R4_case2(self):
        r={"version":0,"runs":{},"seen":{}}; before=copy.deepcopy(r)
        with self.assertRaises(ValueError): api.apply_batch(r,[event("x","a","register"),event("x","b","register")],0)
        self.assertEqual(r,before)
        with self.assertRaises(ValueError): api.apply_batch(r,[],1)
        with self.assertRaises(ValueError): api.apply_batch(r,[event("x","a","register"),event("y","a","complete")],0)
        self.assertEqual(r,before)

    def test_R5_case1(self):
        r={"version":2,"runs":{"b":record("b","completed",2),"a":record("a","completed",1),"c":record("c","queued")},"seen":{}}
        self.assertEqual(api.summarize_registry(r),{"counts":{"queued":1,"running":0,"completed":2,"failed":0},"completed_ids":["a","b"],"total_retries":3})

    def test_R5_case2(self):
        r={"version":0,"runs":{},"seen":{}}; out=api.summarize_registry(r)
        self.assertEqual(sum(out["counts"].values()),0); self.assertEqual(out["completed_ids"],[]); self.assertEqual(out["total_retries"],0)

