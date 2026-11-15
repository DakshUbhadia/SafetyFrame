"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def recovery_report(jobs,events,expected,observed,max_attempts):
    latest=api.latest_checkpoints(events)
    return {'latest':latest,'resume':api.resume_jobs(jobs,latest),'artifacts':api.reconcile_artifacts(expected,observed),'retry':api.plan_retries(jobs,latest,max_attempts)}
