import copy

def new_registry():
    return {"version":0,"runs":{},"seen":{}}

def resolve_config(base,patch):
    out=copy.deepcopy(base)
    for k,v in patch.items():
        if v is None: out.pop(k,None)
        elif isinstance(v,dict): out[k]=resolve_config(out.get(k,{}) if isinstance(out.get(k),dict) else {},v)
        else: out[k]=copy.deepcopy(v)
    return out

def transition(record,action):
    mapping={( "queued","start"):"running",("running","complete"):"completed",("running","fail"):"failed",("failed","retry"):"queued"}
    key=(record["state"],action)
    if key not in mapping: raise ValueError("invalid transition")
    out=copy.deepcopy(record); out["state"]=mapping[key]
    if action=="retry": out["attempts"]+=1
    return out

def apply_batch(registry,events,expected_version):
    if registry["version"]!=expected_version: raise ValueError("stale version")
    out=copy.deepcopy(registry); changed=False
    for event in events:
        eid,ident,action=event["event_id"],event["id"],event["action"]
        if eid in out["seen"]:
            if out["seen"][eid]!=event: raise ValueError("conflicting replay")
            continue
        if action=="register":
            if ident in out["runs"]: raise ValueError("existing run")
            out["runs"][ident]={"id":ident,"state":"queued","attempts":0}
        else:
            if ident not in out["runs"]: raise ValueError("missing run")
            out["runs"][ident]=transition(out["runs"][ident],action)
        out["seen"][eid]=copy.deepcopy(event); changed=True
    if changed: out["version"]+=1
    return out

def summarize_registry(registry):
    counts={state:0 for state in ["queued","running","completed","failed"]}
    for record in registry["runs"].values(): counts[record["state"]]+=1
    return {"counts":counts,"completed_ids":sorted(r["id"] for r in registry["runs"].values() if r["state"]=="completed"),"total_retries":sum(r["attempts"] for r in registry["runs"].values())}
