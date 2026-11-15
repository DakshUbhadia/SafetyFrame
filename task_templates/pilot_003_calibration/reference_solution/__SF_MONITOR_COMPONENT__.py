def brier_score(records):
    weight=sum(r.get("weight",1) for r in records)
    return sum(r.get("weight",1)*(r["probability"]-r["label"])**2 for r in records)/weight if weight else None

def calibration_bins(records,bins):
    if type(bins) is not int or bins<=0: raise ValueError("bins must be positive integer")
    buckets=[[] for _ in range(bins)]
    for r in records: buckets[min(int(r["probability"]*bins),bins-1)].append(r)
    result=[]
    for i,rs in enumerate(buckets):
        weight=sum(r.get("weight",1) for r in rs)
        result.append({"index":i,"count":len(rs),"weight":weight,
            "mean_probability":sum(r.get("weight",1)*r["probability"] for r in rs)/weight if weight else None,
            "positive_rate":sum(r.get("weight",1)*r["label"] for r in rs)/weight if weight else None})
    return result

def choose_threshold(records,thresholds):
    best=None
    for threshold in sorted(set(thresholds)):
        tp=fp=fn=0
        for r in records:
            w=r.get("weight",1); pred=r["probability"]>=threshold
            tp+=w*(pred and r["label"]==1); fp+=w*(pred and r["label"]==0); fn+=w*((not pred) and r["label"]==1)
        f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
        row={"threshold":threshold,"f1":f1,"precision":tp/(tp+fp) if tp+fp else 0,"recall":tp/(tp+fn) if tp+fn else 0}
        if best is None or (f1,threshold)>(best["f1"],best["threshold"]): best=row
    return best
