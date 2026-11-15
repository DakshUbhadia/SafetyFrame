"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def ranking_report(truth,prediction,k):
    order=api.rank_items(prediction)
    return {'order':order,'gain':api.discounted_gain(truth,order,k),'pairwise':api.pairwise_accuracy(truth,prediction),'overlap':api.top_overlap(order,api.rank_items(truth),k)}
