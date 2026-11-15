"""Final benchmark definitions: monitoring and reporting infrastructure."""

TASKS=[
dict(id='task_013',title='Consecutive-breach alert state machine',family='monitoring',functions=['classify','breach_streaks','alert_events','merge_episodes','alert_report'],requirements=[
"classify(values,low,high) returns low,ok,high labels using strict comparisons (<low or >high); None yields missing, boundary values are ok, and low>high raises ValueError.",
"breach_streaks(labels) returns consecutive identical low/high streak lengths at each position; ok or missing resets to zero and switching breach side starts at one.",
"alert_events(labels,min_streak,cooldown) requires positive integer min_streak and nonnegative integer cooldown excluding booleans or raises ValueError; emit index,side events when a low/high streak first reaches min_streak, and suppress candidates with index-last_emitted_index<=cooldown; a suppressed candidate is never delayed.",
"merge_episodes(indices,max_gap) requires nonnegative integer max_gap excluding booleans or raises ValueError; sort and deduplicate integer indices and merge adjacent indices when their difference<=max_gap, returning start,end,count dictionaries.",
"alert_report(values,low,high,min_streak,cooldown,max_gap) in reporting.py returns labels,streaks,events,episodes,missing, where episodes merge emitted event indices and missing counts None values."
],extra="Values are finite numbers or None. Valid labels are low,ok,high,missing. Event indices are zero-based. Episodes count distinct event indices, not the inclusive interval length. Do not use wall-clock time or persistent state.",core='''
def classify(values,low,high):
    if low>high: raise ValueError('thresholds')
    return ['missing' if v is None else 'low' if v<low else 'high' if v>high else 'ok' for v in values]
def breach_streaks(labels):
    out=[]; previous=None; length=0
    for label in labels:
        length=(length+1 if label==previous else 1) if label in ('low','high') else 0
        out.append(length); previous=label
    return out
def alert_events(labels,min_streak,cooldown):
    if type(min_streak) is not int or min_streak<=0 or type(cooldown) is not int or cooldown<0: raise ValueError('parameters')
    streaks=breach_streaks(labels); out=[]; last=None
    for i,(label,length) in enumerate(zip(labels,streaks)):
        if length==min_streak and (last is None or i-last>cooldown):
            out.append({'index':i,'side':label}); last=i
    return out
def merge_episodes(indices,max_gap):
    if type(max_gap) is not int or max_gap<0: raise ValueError('gap')
    out=[]
    for index in sorted(set(indices)):
        if out and index-out[-1]['end']<=max_gap: out[-1]['end']=index; out[-1]['count']+=1
        else: out.append(dict(start=index,end=index,count=1))
    return out
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def alert_report(values,low,high,min_streak,cooldown,max_gap):
    labels=api.classify(values,low,high); events=api.alert_events(labels,min_streak,cooldown)
    return {'labels':labels,'streaks':api.breach_streaks(labels),'events':events,'episodes':api.merge_episodes([e['index'] for e in events],max_gap),'missing':sum(v is None for v in values)}
''',public=["self.assertEqual(api.classify([0,1,2],0,1),['ok','ok','high'])","self.assertEqual(api.breach_streaks(['high','high','ok']),[1,2,0])","self.assertEqual(report.alert_report([],0,1,1,0,1)['events'],[])"],cases=[
["self.assertEqual(api.classify([-1,0,1,2,None],0,1),['low','ok','ok','high','missing'])","self.assertEqual(api.classify([1,None],1,1),['ok','missing'])\nwith self.assertRaises(ValueError): api.classify([],2,1)"],
["self.assertEqual(api.breach_streaks(['low','low','high','high','missing','high','ok','low']),[1,2,1,2,0,1,0,1])","self.assertEqual(api.breach_streaks([]),[]); self.assertEqual(api.breach_streaks(['ok','missing']),[0,0])"],
["labels=['high','high','high','ok','low','low','ok','high','high']; self.assertEqual(api.alert_events(labels,2,4),[dict(index=1,side='high'),dict(index=8,side='high')])","self.assertEqual(api.alert_events(['low','high','high'],1,0),[dict(index=0,side='low'),dict(index=1,side='high')])\nfor m,c in [(0,0),(1,-1),(True,0),(1,True)]:\n    with self.assertRaises(ValueError): api.alert_events([],m,c)"],
["self.assertEqual(api.merge_episodes([5,1,2,2,8],3),[dict(start=1,end=8,count=4)])","self.assertEqual(api.merge_episodes([2,1,1],0),[dict(start=1,end=1,count=1),dict(start=2,end=2,count=1)]); self.assertEqual(api.merge_episodes([],1),[])\nwith self.assertRaises(ValueError): api.merge_episodes([],-1)\nwith self.assertRaises(ValueError): api.merge_episodes([],True)"],
["self.assertEqual(report.alert_report([2,2,None,-1,-1],0,1,2,0,3),{'labels':['high','high','missing','low','low'],'streaks':[1,2,0,1,2],'events':[dict(index=1,side='high'),dict(index=4,side='low')],'episodes':[dict(start=1,end=4,count=2)],'missing':1})","self.assertEqual(report.alert_report([],0,1,1,0,1),{'labels':[],'streaks':[],'events':[],'episodes':[],'missing':0})"]]),
dict(id='task_014',title='Missing-aware time-series resampling',family='monitoring',functions=['bucket_samples','reduce_buckets','fill_forward','moving_average','series_report'],requirements=[
"bucket_samples(samples,width,origin) requires positive finite width or raises ValueError; group (time,value) pairs under integer floor((time-origin)/width), preserving input value order within each bucket and returning keys in ascending order.",
"reduce_buckets(buckets) returns each bucket's mean excluding None, or None when no numeric values remain; preserve the input key set.",
"fill_forward(values,max_missing) requires a nonnegative integer limit excluding booleans or raises ValueError; fill at most max_missing consecutive None entries after a known value, leaving leading missing values and longer-gap remainder as None; each observed value resets the gap.",
"moving_average(values,window) requires a positive integer window excluding booleans or raises ValueError; at each index average non-None values among the most recent window positions including current, returning None when all are missing.",
"series_report(samples,width,origin,start,end,max_missing,window) in reporting.py reduces buckets, builds values for every integer bucket start through end inclusive using None for absent buckets, forward-fills then smooths; return buckets,values,filled,smoothed and empty lists when start>end."
],extra="Times, origin, and numeric values are finite real numbers. Bucket boundaries are left-closed/right-open. Samples may be unsorted and repeated. start/end are integer bucket indices, not timestamps. All output arrays use chronological bucket order.",core='''
import math
def bucket_samples(samples,width,origin):
    if not math.isfinite(width) or width<=0: raise ValueError('width')
    result={}
    for time,value in samples: result.setdefault(math.floor((time-origin)/width),[]).append(value)
    return {k:result[k] for k in sorted(result)}
def reduce_buckets(buckets):
    out={}
    for key,values in buckets.items():
        kept=[v for v in values if v is not None]; out[key]=sum(kept)/len(kept) if kept else None
    return out
def fill_forward(values,max_missing):
    if type(max_missing) is not int or max_missing<0: raise ValueError('limit')
    out=[]; last=None; gap=0
    for value in values:
        if value is not None: last=value; gap=0; out.append(value)
        else: gap+=1; out.append(last if gap<=max_missing else None)
    return out
def moving_average(values,window):
    if type(window) is not int or window<=0: raise ValueError('window')
    out=[]
    for i in range(len(values)):
        kept=[v for v in values[max(0,i-window+1):i+1] if v is not None]
        out.append(sum(kept)/len(kept) if kept else None)
    return out
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def series_report(samples,width,origin,start,end,max_missing,window):
    reduced=api.reduce_buckets(api.bucket_samples(samples,width,origin)); buckets=list(range(start,end+1))
    values=[reduced.get(i) for i in buckets]; filled=api.fill_forward(values,max_missing)
    return {'buckets':buckets,'values':values,'filled':filled,'smoothed':api.moving_average(filled,window)}
''',public=["self.assertEqual(api.bucket_samples([(0,1),(1,2)],1,0),{0:[1],1:[2]})","self.assertEqual(api.fill_forward([1,None],1),[1,1])","self.assertEqual(report.series_report([],1,0,0,0,0,1)['values'],[None])"],cases=[
["self.assertEqual(api.bucket_samples([(2,4),(-.1,3),(0,1),(1.9,2)],2,0),{-1:[3],0:[1,2],1:[4]})","self.assertEqual(list(api.bucket_samples([(4,1),(0,2)],2,1)),[-1,1])\nfor w in [0,-1,float('inf'),float('nan')]:\n    with self.assertRaises(ValueError): api.bucket_samples([],w,0)"],
["self.assertEqual(api.reduce_buckets({0:[None,0,2],1:[None],2:[]}),{0:1,1:None,2:None})","b={1:[1,3]}; self.assertEqual(api.reduce_buckets(b),{1:2}); self.assertEqual(b,{1:[1,3]}); self.assertEqual(api.reduce_buckets({}),{})"],
["self.assertEqual(api.fill_forward([None,0,None,None,None,2,None],2),[None,0,0,0,None,2,2])","self.assertEqual(api.fill_forward([1,None],0),[1,None]); self.assertEqual(api.fill_forward([],0),[])\nfor n in [-1,True,1.5]:\n    with self.assertRaises(ValueError): api.fill_forward([],n)"],
["self.assertEqual(api.moving_average([None,2,None,4,None,None],2),[None,2,2,4,4,None])","self.assertEqual(api.moving_average([1,3,5],10),[1,2,3])\nfor w in [0,True,1.5]:\n    with self.assertRaises(ValueError): api.moving_average([],w)"],
["self.assertEqual(report.series_report([(0,2),(2,6)],1,0,0,3,1,2),{'buckets':[0,1,2,3],'values':[2,None,6,None],'filled':[2,2,6,6],'smoothed':[2,2,4,6]})","self.assertEqual(report.series_report([],1,0,2,1,0,1),dict(buckets=[],values=[],filled=[],smoothed=[]))"]]),
dict(id='task_015',title='Cohort distribution drift report',family='monitoring',functions=['category_counts','aligned_proportions','jensen_shannon','rank_changes','drift_report'],requirements=[
"category_counts(rows,key) counts string categories from key; missing keys and None are excluded and empty string remains a valid category.",
"aligned_proportions(left,right,alpha) returns categories,left,right lists aligned to the sorted union of count keys, adds nonnegative finite alpha to every category on each side and normalizes each side separately; zero total gives an all-zero vector, and invalid alpha raises ValueError.",
"jensen_shannon(left,right) requires equal-length finite nonnegative vectors or raises ValueError; normalize each to sum one when nonzero, then return base-2 Jensen-Shannon divergence, omitting zero logarithm terms; empty vectors give zero and zero vectors remain zero.",
"rank_changes(categories,left,right) requires equal lengths or raises ValueError; return category,delta rows for right-left, ordered by decreasing absolute delta then ascending category.",
"drift_report(reference,current,key,alpha) in reporting.py counts categories, aligns proportions, and returns categories,reference,current,divergence,changes; reference/current are normalized vectors and changes use those vectors."
],extra="Count mappings contain string keys and nonnegative integer counts, including explicit zero counts. Divergence is defined even when one vector is all zero: it contributes zero to its own KL sum. All calculations are offline deterministic summaries, not statistical significance claims.",core='''
import math
def category_counts(rows,key):
    counts={}
    for row in rows:
        value=row.get(key)
        if value is not None: counts[value]=counts.get(value,0)+1
    return counts
def aligned_proportions(left,right,alpha):
    if not math.isfinite(alpha) or alpha<0: raise ValueError('alpha')
    categories=sorted(left.keys()|right.keys()); vectors=[]
    for counts in (left,right):
        v=[counts.get(c,0)+alpha for c in categories]; total=sum(v)
        vectors.append([x/total if total else 0.0 for x in v])
    return {'categories':categories,'left':vectors[0],'right':vectors[1]}
def jensen_shannon(left,right):
    if len(left)!=len(right) or any(not math.isfinite(x) or x<0 for x in list(left)+list(right)): raise ValueError('vectors')
    def norm(values):
        total=sum(values)
        return [v/total if total else 0.0 for v in values]
    a=norm(left); b=norm(right); mid=[(x+y)/2 for x,y in zip(a,b)]
    return .5*sum(x*math.log2(x/m) for v in (a,b) for x,m in zip(v,mid) if x>0)
def rank_changes(categories,left,right):
    if len(categories)!=len(left) or len(left)!=len(right): raise ValueError('length')
    rows=[{'category':c,'delta':b-a} for c,a,b in zip(categories,left,right)]
    return sorted(rows,key=lambda r:(-abs(r['delta']),r['category']))
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def drift_report(reference,current,key,alpha):
    p=api.aligned_proportions(api.category_counts(reference,key),api.category_counts(current,key),alpha)
    return {'categories':p['categories'],'reference':p['left'],'current':p['right'],'divergence':api.jensen_shannon(p['left'],p['right']),'changes':api.rank_changes(p['categories'],p['left'],p['right'])}
''',public=["self.assertEqual(api.category_counts([{'x':'a'},{'x':'a'}],'x'),{'a':2})","self.assertEqual(api.jensen_shannon([1,0],[0,1]),1)","self.assertEqual(report.drift_report([],[],'x',0)['divergence'],0)"],cases=[
["self.assertEqual(api.category_counts([{'x':''},{'x':None},{},{'x':'a'},{'x':''}],'x'),{'':2,'a':1})","self.assertEqual(api.category_counts([],'x'),{}); rows=[{'x':'a'}]; api.category_counts(rows,'x'); self.assertEqual(rows,[{'x':'a'}])"],
["self.assertEqual(api.aligned_proportions({'b':2},{'a':2},1),{'categories':['a','b'],'left':[.25,.75],'right':[.75,.25]})","self.assertEqual(api.aligned_proportions({'a':0},{},0),{'categories':['a'],'left':[0],'right':[0]}); self.assertEqual(api.aligned_proportions({}, {},1),dict(categories=[],left=[],right=[]))\nfor a in [-1,float('inf'),float('nan')]:\n    with self.assertRaises(ValueError): api.aligned_proportions({}, {},a)"],
["self.assertEqual(api.jensen_shannon([2,0],[0,3]),1); self.assertEqual(api.jensen_shannon([2,4],[1,2]),0); self.assertEqual(api.jensen_shannon([0],[1]),.5); self.assertEqual(api.jensen_shannon([],[]),0)","for a,b in [([1],[]),([-1],[1]),([float('nan')],[1]),([1],[float('inf')])]:\n    with self.assertRaises(ValueError): api.jensen_shannon(a,b)"],
["self.assertEqual(api.rank_changes(['z','a','b'],[.5,.5,0],[0,0,1]),[dict(category='b',delta=1),dict(category='a',delta=-.5),dict(category='z',delta=-.5)])","self.assertEqual(api.rank_changes([],[],[]),[])\nwith self.assertRaises(ValueError): api.rank_changes(['x'],[],[])"],
["self.assertEqual(report.drift_report([{'g':'a'}],[{'g':'b'}],'g',0),{'categories':['a','b'],'reference':[1,0],'current':[0,1],'divergence':1,'changes':[dict(category='a',delta=-1),dict(category='b',delta=1)]})","self.assertEqual(report.drift_report([],[],'g',0),{'categories':[],'reference':[],'current':[],'divergence':0,'changes':[]})"]]),
dict(id='task_016',title='Structured report diff and rendering',family='monitoring',functions=['index_rows','diff_reports','summarize_changes','render_markdown','report_changes'],requirements=[
"index_rows(rows) returns deep-copied rows indexed by string id, rejecting duplicate IDs with ValueError; preserve input rows and nested values.",
"diff_reports(before,after,fields) compares rows by id, returning added,removed ID lists sorted lexically and changed rows sorted by id; each changed row has id and fields mapping changed requested fields to before,after values; absent values equal None and unchanged rows are omitted.",
"summarize_changes(diff) returns added,removed,changed counts plus fields counts across changed rows, with fields in sorted key order; counts are rows, not numeric magnitudes.",
"render_markdown(rows,columns) renders a Markdown table with columns as both header labels and lookup keys in supplied order, using ' | ' separators and leading '| ' and trailing ' |'; escape backslash as two backslashes, pipe as backslash-pipe, and newline as <br>; missing or None cells become empty text; produce header,--- separator,and rows joined by newline with no final newline; empty columns return empty string.",
"report_changes(before,after,fields) in reporting.py returns diff,summary,markdown, where markdown lists changed rows only with id and fields columns; fields cells join changed field names in sorted order with comma-space."
],extra="Each row has a unique string id within its report. Fields is a list of unique field names excluding id. Values are JSON-compatible and compare by Python equality; fields for rendering may be arbitrary strings. Nested values are compared as whole values. Markdown cell conversion uses str for non-None values, then escapes in the stated order.",core=r'''
import copy
def index_rows(rows):
    out={}
    for row in rows:
        if row['id'] in out: raise ValueError('duplicate')
        out[row['id']]=copy.deepcopy(row)
    return out
def diff_reports(before,after,fields):
    a=index_rows(before); b=index_rows(after); changed=[]
    for key in sorted(a.keys() & b.keys()):
        delta={f:{'before':copy.deepcopy(a[key].get(f)),'after':copy.deepcopy(b[key].get(f))} for f in fields if a[key].get(f)!=b[key].get(f)}
        if delta: changed.append({'id':key,'fields':delta})
    return {'added':sorted(b.keys()-a.keys()),'removed':sorted(a.keys()-b.keys()),'changed':changed}
def summarize_changes(diff):
    names=sorted({f for row in diff['changed'] for f in row['fields']})
    return {'added':len(diff['added']),'removed':len(diff['removed']),'changed':len(diff['changed']),'fields':{f:sum(f in row['fields'] for row in diff['changed']) for f in names}}
def render_markdown(rows,columns):
    if not columns: return ''
    def escape(value):
        if value is None: return ''
        return str(value).replace('\\','\\\\').replace('|','\\|').replace('\n','<br>')
    def line(values): return '| '+' | '.join(values)+' |'
    return '\n'.join([line([escape(c) for c in columns]),line(['---']*len(columns))]+[line([escape(r.get(c)) for c in columns]) for r in rows])
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def report_changes(before,after,fields):
    diff=api.diff_reports(before,after,fields)
    rows=[{'id':r['id'],'fields':', '.join(sorted(r['fields']))} for r in diff['changed']]
    return {'diff':diff,'summary':api.summarize_changes(diff),'markdown':api.render_markdown(rows,['id','fields'])}
''',public=["self.assertEqual(api.index_rows([{'id':'x'}]),{'x':{'id':'x'}})","self.assertEqual(api.diff_reports([],[],[])['changed'],[])","self.assertEqual(report.report_changes([],[],[])['summary']['changed'],0)"],cases=[
["rows=[{'id':'x','v':[]}]; out=api.index_rows(rows); out['x']['v'].append(1); self.assertEqual(rows,[{'id':'x','v':[]}]); self.assertEqual(api.index_rows([]),{})","with self.assertRaises(ValueError): api.index_rows([{'id':'x'},{'id':'x'}])"],
["self.assertEqual(api.diff_reports([{'id':'z'},{'id':'a','x':1,'skip':1}],[{'id':'b'},{'id':'a','x':2,'skip':3}],['x']),{'added':['b'],'removed':['z'],'changed':[{'id':'a','fields':{'x':{'before':1,'after':2}}}]})","self.assertEqual(api.diff_reports([{'id':'a'}],[{'id':'a','x':None}],['x'])['changed'],[]); self.assertEqual(api.diff_reports([], [{'id':'z'},{'id':'a'}],[])['added'],['a','z'])"],
["d={'added':['a','b'],'removed':['c'],'changed':[{'id':'x','fields':{'z':{},'a':{}}},{'id':'y','fields':{'a':{}}}]}; self.assertEqual(api.summarize_changes(d),{'added':2,'removed':1,'changed':2,'fields':{'a':2,'z':1}})","self.assertEqual(api.summarize_changes(dict(added=[],removed=[],changed=[])),dict(added=0,removed=0,changed=0,fields={}))"],
[r"self.assertEqual(api.render_markdown([{'a':'x|y','b':'q'+chr(92)+'r'+chr(10)+'s'}],['a','b']), '| a | b |\n| --- | --- |\n| x\\|y | q\\\\r<br>s |')","self.assertEqual(api.render_markdown([{'a':None},{}],['a']),'| a |'+chr(10)+'| --- |'+chr(10)+'|  |'+chr(10)+'|  |'); self.assertEqual(api.render_markdown([],[]),'')"],
["r=report.report_changes([{'id':'a','x':1,'y':0}],[{'id':'a','x':2,'y':1}],['y','x']); self.assertEqual(r['diff'],{'added':[],'removed':[],'changed':[{'id':'a','fields':{'x':dict(before=1,after=2),'y':dict(before=0,after=1)}}]}); self.assertEqual(r['summary'],dict(added=0,removed=0,changed=1,fields={'x':1,'y':1})); self.assertEqual(r['markdown'],'| id | fields |'+chr(10)+'| --- | --- |'+chr(10)+'| a | x, y |')","r=report.report_changes([],[],[]); self.assertEqual(r['diff'],dict(added=[],removed=[],changed=[])); self.assertEqual(r['markdown'],'| id | fields |'+chr(10)+'| --- | --- |')"]])
]
