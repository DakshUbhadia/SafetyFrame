"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def alert_report(values,low,high,min_streak,cooldown,max_gap):
    labels=api.classify(values,low,high); events=api.alert_events(labels,min_streak,cooldown)
    return {'labels':labels,'streaks':api.breach_streaks(labels),'events':events,'episodes':api.merge_episodes([e['index'] for e in events],max_gap),'missing':sum(v is None for v in values)}
