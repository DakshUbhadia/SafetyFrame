"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def report_changes(before,after,fields):
    diff=api.diff_reports(before,after,fields)
    rows=[{'id':r['id'],'fields':', '.join(sorted(r['fields']))} for r in diff['changed']]
    return {'diff':diff,'summary':api.summarize_changes(diff),'markdown':api.render_markdown(rows,['id','fields'])}
