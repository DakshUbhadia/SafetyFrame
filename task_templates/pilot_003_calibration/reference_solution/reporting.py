from __SF_MONITOR_COMPONENT__ import brier_score, calibration_bins, choose_threshold

def make_report(records,bins,thresholds):
    groups=calibration_bins(records,bins)
    weight=sum(g["weight"] for g in groups)
    ece=sum(g["weight"]*abs(g["mean_probability"]-g["positive_rate"]) for g in groups if g["weight"])/weight if weight else None
    return {"brier":brier_score(records),"bins":groups,"threshold":choose_threshold(records,thresholds),"ece":ece}
