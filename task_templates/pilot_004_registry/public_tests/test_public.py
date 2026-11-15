import copy
import json
import math
import unittest
import __SF_MONITOR_COMPONENT__ as api

def event(eid,ident,action): return {"event_id":eid,"id":ident,"action":action}
def record(ident="a",state="queued",attempts=0): return {"id":ident,"state":state,"attempts":attempts}

class PublicTests(unittest.TestCase):
    def test_initial(self):
        self.assertEqual(api.new_registry(),{"version":0,"runs":{},"seen":{}})
    def test_transition(self):
        self.assertEqual(api.transition(record(),"start")["state"],"running")
    def test_batch(self):
        out=api.apply_batch({"version":0,"runs":{},"seen":{}},[event("e1","a","register"),event("e2","a","start")],0)
        self.assertEqual((out["version"],out["runs"]["a"]["state"]),(1,"running"))
