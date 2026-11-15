"""Utilities for AI safety research safety_eval_run processing."""
import copy

def _impl_index_rows(rows):
    out = {}
    for row in rows:
        if row['id'] in out:
            raise ValueError('duplicate')
        out[row['id']] = copy.deepcopy(row)
    return out

def _impl_diff_reports(before, after, fields):
    a = _impl_index_rows(before)
    b = _impl_index_rows(after)
    changed = []
    for key in sorted(a.keys() & b.keys()):
        delta = {f: {'before': copy.deepcopy(a[key].get(f)), 'after': copy.deepcopy(b[key].get(f))} for f in fields if a[key].get(f) != b[key].get(f)}
        if delta:
            changed.append({'id': key, 'fields': delta})
    return {'added': sorted(b.keys() - a.keys()), 'removed': sorted(a.keys() - b.keys()), 'changed': changed}

def _impl_summarize_changes(diff):
    names = sorted({f for row in diff['changed'] for f in row['fields']})
    return {'added': len(diff['added']), 'removed': len(diff['removed']), 'changed': len(diff['changed']), 'fields': {f: sum((f in row['fields'] for row in diff['changed'])) for f in names}}

def _impl_render_markdown(rows, columns):
    if not columns:
        return ''

    def escape(value):
        if value is None:
            return ''
        return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('\n', '<br>')

    def line(values):
        return '| ' + ' | '.join(values) + ' |'
    return '\n'.join([line([escape(c) for c in columns]), line(['---'] * len(columns))] + [line([escape(r.get(c)) for c in columns]) for r in rows])

def index_rows(rows):
    return _impl_index_rows(rows)

def diff_reports(before, after, fields):
    return _impl_diff_reports(before, after, fields)

def summarize_changes(diff):
    return _impl_summarize_changes(diff)

def render_markdown(rows, columns):
    return _impl_render_markdown(rows, columns)
