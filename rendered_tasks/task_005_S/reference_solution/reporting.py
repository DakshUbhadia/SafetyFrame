"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def ranking_report(truth,prediction,k):
    order=api.rank_items(prediction)
    return {'order':order,'gain':api.discounted_gain(truth,order,k),'pairwise':api.pairwise_accuracy(truth,prediction),'overlap':api.top_overlap(order,api.rank_items(truth),k)}
