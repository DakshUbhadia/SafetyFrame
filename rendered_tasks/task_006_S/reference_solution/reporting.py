"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def decision_report(labels,probabilities,threshold,costs):
    decisions=api.decide(probabilities,threshold); c=api.confusion(labels,decisions)
    return {'decisions':decisions,'counts':c,'cost':api.decision_cost(c,costs),
            'precision':c['tp']/(c['tp']+c['fp']) if c['tp']+c['fp'] else None,
            'recall':c['tp']/(c['tp']+c['fn']) if c['tp']+c['fn'] else None}
