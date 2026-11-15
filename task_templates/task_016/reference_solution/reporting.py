"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def report_changes(before,after,fields):
    diff=api.diff_reports(before,after,fields)
    rows=[{'id':r['id'],'fields':', '.join(sorted(r['fields']))} for r in diff['changed']]
    return {'diff':diff,'summary':api.summarize_changes(diff),'markdown':api.render_markdown(rows,['id','fields'])}
