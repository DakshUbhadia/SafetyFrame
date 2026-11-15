"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def comparison_report(left,right,tolerance,fraction):
    pairs=api.match_pairs(left,right); d=[v for k,v in pairs]
    return {'ids':[k for k,v in pairs],'deltas':d,'signs':api.sign_summary(d,tolerance),'trimmed':api.trimmed_mean(d,fraction),'leave_one_out':api.leave_one_out(d)}
