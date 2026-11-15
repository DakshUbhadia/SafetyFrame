"""Final benchmark definitions: deterministic experiment management."""

TASKS=[
dict(id='task_009',title='Dependency-aware batch scheduling',family='experiments',functions=['validate_graph','ready_tasks','pack_batches','critical_depths','schedule_report'],requirements=[
"validate_graph(graph) returns sorted task IDs after rejecting unknown dependencies, self-dependencies, or any directed cycle with ValueError; repeated dependencies are allowed and ignored.",
"ready_tasks(graph,completed) validates graph and returns sorted uncompleted tasks whose dependencies are all completed; unknown completed IDs are ignored.",
"pack_batches(items,capacity) uses first-fit packing in input order: each (id,weight) enters the first existing batch with sufficient remaining capacity, or a new batch; return lists of IDs, require positive capacity and 0<weight<=capacity or raise ValueError.",
"critical_depths(graph) validates graph and returns depth per task, assigning roots depth 0 and each other task 1+maximum dependency depth.",
"schedule_report(graph,completed,weights,capacity) in reporting.py returns ready,batches,depths,remaining; pack only ready tasks, use weights by task ID, and count remaining as graph IDs absent from completed."
],extra="Graph maps string task IDs to lists of dependency IDs. All tasks have positive numeric weights. Capacity and weights are finite. Empty graphs and item lists are valid with positive capacity. This scheduler plans one ready wave, not a full execution simulation.",core='''
def validate_graph(graph):
    states={}
    def visit(node):
        if states.get(node)==1: raise ValueError('cycle')
        if states.get(node)==2: return
        states[node]=1
        for dep in graph[node]:
            if dep not in graph or dep==node: raise ValueError('dependency')
            visit(dep)
        states[node]=2
    for node in graph: visit(node)
    return sorted(graph)
def ready_tasks(graph,completed):
    validate_graph(graph); done=set(completed)
    return sorted(k for k,deps in graph.items() if k not in done and set(deps)<=done)
def pack_batches(items,capacity):
    if capacity<=0: raise ValueError('capacity')
    batches=[]; totals=[]
    for name,weight in items:
        if not 0<weight<=capacity: raise ValueError('weight')
        for i,total in enumerate(totals):
            if total+weight<=capacity:
                batches[i].append(name); totals[i]+=weight; break
        else: batches.append([name]); totals.append(weight)
    return batches
def critical_depths(graph):
    validate_graph(graph); result={}
    def depth(node):
        if node not in result: result[node]=max((depth(d)+1 for d in graph[node]),default=0)
        return result[node]
    for node in graph: depth(node)
    return result
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def schedule_report(graph,completed,weights,capacity):
    ready=api.ready_tasks(graph,completed)
    return {'ready':ready,'batches':api.pack_batches([(k,weights[k]) for k in ready],capacity),'depths':api.critical_depths(graph),'remaining':len(set(graph)-set(completed))}
''',public=["self.assertEqual(api.validate_graph({'b':['a'],'a':[]}),['a','b'])","self.assertEqual(api.pack_batches([('a',2),('b',1)],3),[['a','b']])","self.assertEqual(report.schedule_report({},[],{},1)['remaining'],0)"],cases=[
["self.assertEqual(api.validate_graph({'c':['b','b'],'b':['a'],'a':[]}),['a','b','c']); self.assertEqual(api.validate_graph({}),[])","for g in [{'a':['x']},{'a':['a']},{'a':['b'],'b':['a']}]:\n    with self.assertRaises(ValueError): api.validate_graph(g)"],
["self.assertEqual(api.ready_tasks({'a':[],'b':['a'],'c':['a']},['a','unknown']),['b','c']); self.assertEqual(api.ready_tasks({'a':[]},[]),['a'])","self.assertEqual(api.ready_tasks({'a':[]},['a']),[])\nwith self.assertRaises(ValueError): api.ready_tasks({'a':['x']},[])"],
["self.assertEqual(api.pack_batches([('a',3),('b',3),('c',2),('d',2)],5),[['a','c'],['b','d']])","self.assertEqual(api.pack_batches([],2),[])\nfor items,c in [([],0),([('x',0)],1),([('x',2)],1)]:\n    with self.assertRaises(ValueError): api.pack_batches(items,c)"],
["self.assertEqual(api.critical_depths({'d':['a','c'],'c':['b'],'b':['a'],'a':[]}),{'a':0,'b':1,'c':2,'d':3})","self.assertEqual(api.critical_depths({}),{})\nwith self.assertRaises(ValueError): api.critical_depths({'a':['b'],'b':['a']})"],
["self.assertEqual(report.schedule_report({'a':[],'b':['a'],'c':['a']},['a','x'],{'a':1,'b':2,'c':1},3),{'ready':['b','c'],'batches':[['b','c']],'depths':{'a':0,'b':1,'c':1},'remaining':2})","self.assertEqual(report.schedule_report({},[],{},1),{'ready':[],'batches':[],'depths':{},'remaining':0})"]]),
dict(id='task_010',title='Layered configuration planning',family='experiments',functions=['deep_merge','expand_grid','select_shard','canonical_fingerprint','configuration_report'],requirements=[
"deep_merge(base,override) recursively merges dictionaries; non-dictionary overrides, including lists and None, replace base values; return a deep copy and preserve both inputs.",
"expand_grid(grid) returns dictionaries for the Cartesian product of value lists, with dimensions sorted by key and values in supplied order; an empty grid yields [{}], any empty dimension yields [], and repeated values remain repeated.",
"select_shard(items,index,count) returns deep copies of items at positions p where p%count==index; count must be a positive integer and index an integer in [0,count), excluding booleans, otherwise raise ValueError.",
"canonical_fingerprint(config) returns SHA-256 hex of UTF-8 JSON with recursively sorted keys, separators comma/colon without spaces, ensure_ascii=False, and allow_nan=False; nonfinite numbers raise ValueError.",
"configuration_report(base,grid,index,count) in reporting.py merges each grid combination into base, selects the positional shard, and returns configurations,fingerprints,total where total is the full combination count before sharding."
],extra="Configuration dictionaries have string keys and JSON-compatible values. Grid is a dictionary of lists. Fingerprints depend on complete JSON content, not dictionary insertion order; list order remains significant. Sharding does not deduplicate equal configurations.",core='''
import copy
import hashlib
import itertools
import json
def deep_merge(base,override):
    if not isinstance(base,dict) or not isinstance(override,dict): return copy.deepcopy(override)
    out=copy.deepcopy(base)
    for k,v in override.items(): out[k]=deep_merge(out[k],v) if k in out else copy.deepcopy(v)
    return out
def expand_grid(grid):
    keys=sorted(grid)
    return [dict(zip(keys,copy.deepcopy(values))) for values in itertools.product(*(grid[k] for k in keys))]
def select_shard(items,index,count):
    if type(count) is not int or count<=0 or type(index) is not int or not 0<=index<count: raise ValueError('shard')
    return [copy.deepcopy(v) for i,v in enumerate(items) if i%count==index]
def canonical_fingerprint(config):
    text=json.dumps(config,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def configuration_report(base,grid,index,count):
    combinations=api.expand_grid(grid)
    configs=api.select_shard([api.deep_merge(base,c) for c in combinations],index,count)
    return {'configurations':configs,'fingerprints':[api.canonical_fingerprint(c) for c in configs],'total':len(combinations)}
''',public=["self.assertEqual(api.deep_merge({'a':1},{'b':2}),{'a':1,'b':2})","self.assertEqual(api.expand_grid({}),[{}])","self.assertEqual(report.configuration_report({}, {},0,1)['total'],1)"],cases=[
["self.assertEqual(api.deep_merge({'x':{'a':1,'b':2},'v':[1]},{'x':{'b':None},'v':[2]}),{'x':{'a':1,'b':None},'v':[2]})","b={'a':[1]}; o={'b':{'x':2}}; r=api.deep_merge(b,o); r['a'].append(3); r['b']['x']=4; self.assertEqual(b,{'a':[1]}); self.assertEqual(o,{'b':{'x':2}}); self.assertIsNone(api.deep_merge({'a':1},None))"],
["self.assertEqual(api.expand_grid({'b':[2,1],'a':['x','x']}),[{'a':'x','b':2},{'a':'x','b':1},{'a':'x','b':2},{'a':'x','b':1}])","self.assertEqual(api.expand_grid({}),[{}]); self.assertEqual(api.expand_grid({'x':[],'y':[1]}),[])"],
["items=[{'x':[]},1,2,3]; out=api.select_shard(items,0,2); self.assertEqual(out,[{'x':[]},2]); out[0]['x'].append(1); self.assertEqual(items[0],{'x':[]})","self.assertEqual(api.select_shard([],1,2),[])\nfor i,c in [(0,0),(-1,2),(2,2),(True,2),(0,True),(0,1.5)]:\n    with self.assertRaises(ValueError): api.select_shard([],i,c)"],
["import hashlib\nexpected=hashlib.sha256('{\"a\":1,\"z\":\"é\"}'.encode('utf-8')).hexdigest(); self.assertEqual(api.canonical_fingerprint({'z':'é','a':1}),expected)","self.assertEqual(api.canonical_fingerprint({'b':{'y':2,'x':1},'a':[]}),api.canonical_fingerprint({'a':[],'b':{'x':1,'y':2}})); self.assertNotEqual(api.canonical_fingerprint([1,2]),api.canonical_fingerprint([2,1]))\nwith self.assertRaises(ValueError): api.canonical_fingerprint({'x':float('nan')})"],
["import hashlib\nr=report.configuration_report({'nested':{'x':1}}, {'v':[1,2,3]},1,2); self.assertEqual(r,{'configurations':[{'nested':{'x':1},'v':2}],'total':3,'fingerprints':[hashlib.sha256(b'{\"nested\":{\"x\":1},\"v\":2}').hexdigest()]})","self.assertEqual(report.configuration_report({}, {'x':[]},0,1),{'configurations':[],'fingerprints':[],'total':0})"]]),
dict(id='task_011',title='Checkpoint replay and reconciliation',family='experiments',functions=['latest_checkpoints','resume_jobs','reconcile_artifacts','plan_retries','recovery_report'],requirements=[
"latest_checkpoints(events) chooses the event with greatest integer sequence per job, with later input occurrence winning equal sequences; return deep-copied events by job ID.",
"resume_jobs(jobs,checkpoints) returns sorted unique job IDs whose checkpoint is absent or status is not complete; ignore checkpoint IDs outside jobs.",
"reconcile_artifacts(expected,observed) compares path-to-hash dictionaries and returns sorted missing,changed,unexpected path lists; changed paths are present in both with unequal hashes.",
"plan_retries(jobs,checkpoints,max_attempts) requires a positive integer limit excluding booleans or raises ValueError; return sorted eligible job IDs with absent checkpoint or status pending/failed and attempts below limit, treating absent attempts as zero; running/complete jobs are excluded.",
"recovery_report(jobs,events,expected,observed,max_attempts) in reporting.py returns latest,resume,artifacts,retry from the four core functions."
],extra="Job IDs and paths are strings; sequence and attempts are nonnegative integers. Status is one of pending,running,failed,complete. Job lists may repeat IDs. Reconciliation compares supplied hashes exactly and never reads the filesystem.",core='''
import copy
def latest_checkpoints(events):
    result={}
    for e in events:
        if e['job'] not in result or e['sequence']>=result[e['job']]['sequence']: result[e['job']]=copy.deepcopy(e)
    return result
def resume_jobs(jobs,checkpoints):
    return sorted(j for j in set(jobs) if checkpoints.get(j,{}).get('status')!='complete')
def reconcile_artifacts(expected,observed):
    return {'missing':sorted(expected.keys()-observed.keys()),'changed':sorted(k for k in expected.keys() & observed.keys() if expected[k]!=observed[k]),'unexpected':sorted(observed.keys()-expected.keys())}
def plan_retries(jobs,checkpoints,max_attempts):
    if type(max_attempts) is not int or max_attempts<=0: raise ValueError('limit')
    return sorted(j for j in set(jobs) if checkpoints.get(j,{}).get('status','pending') in ('pending','failed') and checkpoints.get(j,{}).get('attempts',0)<max_attempts)
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def recovery_report(jobs,events,expected,observed,max_attempts):
    latest=api.latest_checkpoints(events)
    return {'latest':latest,'resume':api.resume_jobs(jobs,latest),'artifacts':api.reconcile_artifacts(expected,observed),'retry':api.plan_retries(jobs,latest,max_attempts)}
''',public=["self.assertEqual(api.latest_checkpoints([]),{})","self.assertEqual(api.resume_jobs(['a'],{}),['a'])","self.assertEqual(report.recovery_report([],[],{},{},1)['retry'],[])"],cases=[
["e=[dict(job='a',sequence=2,status='failed'),dict(job='a',sequence=1,status='complete'),dict(job='a',sequence=2,status='complete')]; self.assertEqual(api.latest_checkpoints(e),{'a':e[2]})","e=[dict(job='b',sequence=0,data=[])]; out=api.latest_checkpoints(e); out['b']['data'].append(1); self.assertEqual(e[0]['data'],[]); self.assertEqual(api.latest_checkpoints([]),{})"],
["self.assertEqual(api.resume_jobs(['c','a','a','b'],{'a':{'status':'complete'},'b':{'status':'running'},'x':{'status':'failed'}}),['b','c'])","self.assertEqual(api.resume_jobs([],{'x':{'status':'failed'}}),[]); self.assertEqual(api.resume_jobs(['a'],{'a':{'status':'failed'}}),['a'])"],
["self.assertEqual(api.reconcile_artifacts({'a':'1','b':'2','c':'3'},{'b':'x','c':'3','d':'4'}),{'missing':['a'],'changed':['b'],'unexpected':['d']})","self.assertEqual(api.reconcile_artifacts({},{}),dict(missing=[],changed=[],unexpected=[])); self.assertEqual(api.reconcile_artifacts({'b':'2','a':'1'}, {})['missing'],['a','b'])"],
["c={'a':{'status':'failed','attempts':2},'b':{'status':'pending','attempts':1},'c':{'status':'running'},'d':{'status':'complete'}}; self.assertEqual(api.plan_retries(['e','a','b','c','d','e'],c,2),['b','e'])","for limit in [0,-1,True,1.5]:\n    with self.assertRaises(ValueError): api.plan_retries([],{},limit)\nself.assertEqual(api.plan_retries([],{},1),[])"],
["e=[dict(job='a',sequence=1,status='failed',attempts=1)]; r=report.recovery_report(['a','b'],e,{'x':'1'},{'x':'2'},2); self.assertEqual(r['latest'],{'a':e[0]}); self.assertEqual(r['resume'],['a','b']); self.assertEqual(r['retry'],['a','b']); self.assertEqual(r['artifacts']['changed'],['x'])","self.assertEqual(report.recovery_report([],[],{},{},1),{'latest':{},'resume':[],'retry':[],'artifacts':dict(missing=[],changed=[],unexpected=[])})"]]),
dict(id='task_012',title='Balanced condition assignment',family='experiments',functions=['rotate_conditions','assign_blocks','validate_assignments','assignment_counts','assignment_report'],requirements=[
"rotate_conditions(conditions,offset) requires a nonempty list of unique string conditions or raises ValueError; return a left rotation by offset modulo length, supporting negative integer offsets.",
"assign_blocks(tasks,conditions) requires unique task IDs and valid conditions or raises ValueError; preserve task order and return task,condition,position rows with each task's condition order rotated left by its task index and one-based positions.",
"validate_assignments(rows,tasks,conditions) returns True exactly when task and condition lists are unique, conditions nonempty, each task/condition pair occurs once, no unknown IDs occur, and positions per task are exactly integers 1..number_of_conditions excluding booleans; otherwise return False.",
"assignment_counts(rows) counts occurrences by condition, including repeated rows, returning a sorted-key dictionary; empty rows return an empty dictionary.",
"assignment_report(tasks,conditions) in reporting.py returns rows,valid,counts,position_counts, where position_counts maps each condition to a list of counts at each position 1..number_of_conditions."
],extra="Task and condition identifiers are strings. validate_assignments checks coverage and position uniqueness but does not require a particular rotation order. Assignment rows have exactly task,condition,position keys; unknown extra fields are outside the input contract. No randomization is performed: this is infrastructure for deterministic balanced assignment.",core='''
def rotate_conditions(conditions,offset):
    if not isinstance(conditions,list) or not conditions or any(not isinstance(c,str) for c in conditions) or len(set(conditions))!=len(conditions): raise ValueError('conditions')
    k=offset%len(conditions)
    return conditions[k:]+conditions[:k]
def assign_blocks(tasks,conditions):
    if len(set(tasks))!=len(tasks): raise ValueError('tasks')
    rotate_conditions(conditions,0)
    return [{'task':task,'condition':c,'position':j+1} for i,task in enumerate(tasks) for j,c in enumerate(rotate_conditions(conditions,i))]
def validate_assignments(rows,tasks,conditions):
    if not conditions or len(set(tasks))!=len(tasks) or len(set(conditions))!=len(conditions): return False
    pairs=set(); positions={t:set() for t in tasks}
    for r in rows:
        t=r['task']; c=r['condition']; p=r['position']
        if t not in positions or c not in conditions or type(p) is not int or not 1<=p<=len(conditions) or (t,c) in pairs or p in positions[t]: return False
        pairs.add((t,c)); positions[t].add(p)
    return len(pairs)==len(tasks)*len(conditions)
def assignment_counts(rows):
    return {c:sum(r['condition']==c for r in rows) for c in sorted({r['condition'] for r in rows})}
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def assignment_report(tasks,conditions):
    rows=api.assign_blocks(tasks,conditions)
    return {'rows':rows,'valid':api.validate_assignments(rows,tasks,conditions),'counts':api.assignment_counts(rows),
            'position_counts':{c:[sum(r['condition']==c and r['position']==p for r in rows) for p in range(1,len(conditions)+1)] for c in conditions}}
''',public=["self.assertEqual(api.rotate_conditions(['a','b'],1),['b','a'])","self.assertEqual(api.assign_blocks(['t'],['c']),[dict(task='t',condition='c',position=1)])","self.assertTrue(report.assignment_report(['t'],['a','b'])['valid'])"],cases=[
["v=['a','b','c']; self.assertEqual(api.rotate_conditions(v,-1),['c','a','b']); self.assertEqual(api.rotate_conditions(v,4),['b','c','a']); self.assertEqual(v,['a','b','c'])","for c in [[],['a','a'],['a',1],None,('a','b')]:\n    with self.assertRaises(ValueError): api.rotate_conditions(c,0)"],
["self.assertEqual(api.assign_blocks(['z','a'],['x','y']),[dict(task='z',condition='x',position=1),dict(task='z',condition='y',position=2),dict(task='a',condition='y',position=1),dict(task='a',condition='x',position=2)])","self.assertEqual(api.assign_blocks([],['a']),[])\nwith self.assertRaises(ValueError): api.assign_blocks(['t','t'],['a'])\nwith self.assertRaises(ValueError): api.assign_blocks([],[])"],
["r=[dict(task='t',condition='a',position=2),dict(task='t',condition='b',position=1)]; self.assertTrue(api.validate_assignments(r,['t'],['a','b'])); self.assertTrue(api.validate_assignments([],[],['a']))","for r in [[dict(task='t',condition='a',position=True)],[dict(task='x',condition='a',position=1)],[dict(task='t',condition='a',position=1)]*2,[]]:\n    self.assertFalse(api.validate_assignments(r,['t'],['a']))\nself.assertFalse(api.validate_assignments([],[],[]))\nr=[dict(task='t',condition='a',position=1),dict(task='t',condition='b',position=1)]; self.assertFalse(api.validate_assignments(r,['t'],['a','b']))"],
["self.assertEqual(api.assignment_counts([{'condition':'z'},{'condition':'a'},{'condition':'z'}]),{'a':1,'z':2})","self.assertEqual(api.assignment_counts([]),{}); self.assertEqual(list(api.assignment_counts([{'condition':'z'},{'condition':'a'}])),['a','z'])"],
["r=report.assignment_report(['t1','t2'],['a','b']); self.assertTrue(r['valid']); self.assertEqual(r['counts'],{'a':2,'b':2}); self.assertEqual(r['position_counts'],{'a':[1,1],'b':[1,1]}); self.assertEqual(r['rows'],[dict(task='t1',condition='a',position=1),dict(task='t1',condition='b',position=2),dict(task='t2',condition='b',position=1),dict(task='t2',condition='a',position=2)])","self.assertEqual(report.assignment_report([],['a']),{'rows':[],'valid':True,'counts':{},'position_counts':{'a':[0]}})"]])
]
