"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def series_report(samples,width,origin,start,end,max_missing,window):
    reduced=api.reduce_buckets(api.bucket_samples(samples,width,origin)); buckets=list(range(start,end+1))
    values=[reduced.get(i) for i in buckets]; filled=api.fill_forward(values,max_missing)
    return {'buckets':buckets,'values':values,'filled':filled,'smoothed':api.moving_average(filled,window)}
