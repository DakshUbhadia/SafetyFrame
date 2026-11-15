"""Fresh final-task definitions: evaluation ingestion. No pilot definitions reused."""

TASKS=[
dict(id='task_001',title='Escaped record-path projection',family='ingestion',functions=['parse_path','lookup','project','expand_columns','project_table'],
requirements=[
"parse_path(text) splits dot-separated paths, using backslash to escape a dot or backslash; reject empty segments, empty input, non-string input, invalid escapes, and a trailing backslash with ValueError.",
"lookup(record,segments,default=None) traverses dictionary keys and canonical list indices (0 or a nonzero digit followed by digits); return a deep copy or the supplied default for a missing key, invalid index, or scalar traversal; empty segments select the whole record.",
"project(record,columns) resolves output-name to path-string mappings, returns values in sorted output-name order, and uses None for missing fields while preserving False and zero values.",
"expand_columns(columns,prefix) prepends prefix plus a dot to each path when prefix is nonempty, preserves paths when prefix is empty, returns a new dictionary, and rejects invalid resulting paths with ValueError.",
"project_table(records,columns) in reporting.py projects every record, returning columns as sorted output names, rows as lists of values in that order, and missing_counts per output column counting only None values."
],extra="Paths use ASCII canonical list indices with no signs or leading zeros. Dictionary keys remain literal even when numeric. Inputs are JSON-compatible. Do not mutate any input.",
core=r'''
import copy
import re
def parse_path(text):
    if not isinstance(text,str) or not text: raise ValueError('invalid path')
    result=[]; part=''; escaped=False
    for char in text:
        if escaped:
            if char not in '.\\': raise ValueError('invalid escape')
            part+=char; escaped=False
        elif char=='\\': escaped=True
        elif char=='.':
            if not part: raise ValueError('empty segment')
            result.append(part); part=''
        else: part+=char
    if escaped or not part: raise ValueError('invalid ending')
    return result+[part]
def lookup(record,segments,default=None):
    node=record
    for segment in segments:
        if isinstance(node,dict) and segment in node: node=node[segment]
        elif isinstance(node,list) and re.fullmatch(r'0|[1-9][0-9]*',segment) and int(segment)<len(node): node=node[int(segment)]
        else: return default
    return copy.deepcopy(node)
def project(record,columns):
    return {name:lookup(record,parse_path(columns[name])) for name in sorted(columns)}
def expand_columns(columns,prefix):
    out={name:(prefix+'.'+path if prefix else path) for name,path in columns.items()}
    for path in out.values(): parse_path(path)
    return out
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def project_table(records,columns):
    names=sorted(columns); projected=[api.project(r,columns) for r in records]
    return {'columns':names,'rows':[[r[n] for n in names] for r in projected],
            'missing_counts':{n:sum(r[n] is None for r in projected) for n in names}}
''',public=["self.assertEqual(api.parse_path('run.id'),['run','id'])","self.assertEqual(api.project({'x':0},{'v':'x'}),{'v':0})","self.assertEqual(report.project_table([{'x':2}],{'v':'x'})['rows'],[[2]])"],cases=[
[r"self.assertEqual(api.parse_path(r'a\.b.c'),['a.b','c']); self.assertEqual(api.parse_path(r'a\\b'),['a\\b'])", "for p in ['', 'a..b', 'a.', 'a'+chr(92), 'a'+chr(92)+'q', None]:\n    with self.assertRaises(ValueError): api.parse_path(p)"],
["self.assertEqual(api.lookup({'x':[{'v':False}]},['x','0','v']),False); self.assertEqual(api.lookup({'01':2},['01']),2)","self.assertEqual(api.lookup({'x':[1]},['x','01'],9),9); d={'x':[]}; out=api.lookup(d,[]); out['x'].append(1); self.assertEqual(d,{'x':[]})"],
[r"out=api.project({'a.b':3,'x':False},{'z':'missing','a':r'a\.b','b':'x'}); self.assertEqual(out,{'a':3,'b':False,'z':None}); self.assertEqual(list(out),['a','b','z'])","r={'x':[1]}; out=api.project(r,{'v':'x'}); out['v'].append(2); self.assertEqual(r,{'x':[1]})"],
["self.assertEqual(api.expand_columns({'a':'x'},'run'),{'a':'run.x'}); self.assertEqual(api.expand_columns({'a':'x'},''),{'a':'x'})","with self.assertRaises(ValueError): api.expand_columns({'a':'.x'},'run')"],
["self.assertEqual(report.project_table([{'x':0},{'x':False},{}],{'v':'x'}),{'columns':['v'],'rows':[[0],[False],[None]],'missing_counts':{'v':1}})","self.assertEqual(report.project_table([],{'b':'x','a':'y'}),{'columns':['a','b'],'rows':[],'missing_counts':{'a':0,'b':0}})"]]),
dict(id='task_002',title='Typed CSV result ingestion',family='ingestion',functions=['parse_header','convert_value','read_table','validate_rows','ingest'],
requirements=[
"parse_header(names) strips whitespace, rejects empty or duplicate stripped column names with ValueError, and returns the stripped names in original order.",
"convert_value(text,kind) strips text and returns None for empty text; kinds are str,int,float,bool, where int accepts optional minus and ASCII digits only, float must be finite, and bool accepts exactly lowercase true or false; invalid values or unknown kinds raise ValueError.",
"read_table(text) parses CSV with its first row as header, skips completely empty rows, rejects ragged rows with ValueError, and returns string-valued dictionaries using normalized header names; empty input returns an empty list.",
"validate_rows(rows,schema,required) converts declared schema columns, ignores extra input columns, and returns (valid,errors); each invalid row has one error dictionary with one-based row and sorted invalid-or-missing column names; None in a required column is invalid.",
"ingest(text,schema,required) in reporting.py combines reading and validation into valid_rows,errors,total_rows; malformed CSV row widths or headers propagate ValueError rather than becoming row conversion errors."
],extra="CSV quoting follows Python's csv reader. Empty input has no header. Required is a subset of schema keys. Schema kinds must be recognized even for empty strings. No input mutation.",core=r'''
import csv
import io
import math
import re
def parse_header(names):
    result=[n.strip() for n in names]
    if any(not n for n in result) or len(set(result))!=len(result): raise ValueError('bad header')
    return result
def convert_value(text,kind):
    if kind not in {'str','int','float','bool'}: raise ValueError('bad kind')
    text=text.strip()
    if not text: return None
    try:
        if kind=='str': return text
        if kind=='int':
            if not re.fullmatch(r'-?[0-9]+',text): raise ValueError('bad integer')
            return int(text)
        if kind=='float':
            value=float(text)
            if not math.isfinite(value): raise ValueError('nonfinite')
            return value
        if text not in {'true','false'}: raise ValueError('bad boolean')
        return text=='true'
    except (TypeError,OverflowError): raise ValueError('bad value')
def read_table(text):
    reader=csv.reader(io.StringIO(text))
    try: names=parse_header(next(reader))
    except StopIteration: return []
    result=[]
    for row in reader:
        if not row: continue
        if len(row)!=len(names): raise ValueError('ragged row')
        result.append(dict(zip(names,row)))
    return result
def validate_rows(rows,schema,required):
    valid=[]; errors=[]
    for index,row in enumerate(rows,1):
        converted={}; invalid=[]
        for name,kind in schema.items():
            try:
                converted[name]=convert_value(row.get(name,''),kind)
                if name in required and converted[name] is None: invalid.append(name)
            except ValueError: invalid.append(name)
        if invalid: errors.append({'row':index,'columns':sorted(invalid)})
        else: valid.append(converted)
    return valid,errors
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def ingest(text,schema,required):
    rows=api.read_table(text); valid,errors=api.validate_rows(rows,schema,required)
    return {'valid_rows':valid,'errors':errors,'total_rows':len(rows)}
''',public=["self.assertEqual(api.parse_header([' a ','b']),['a','b'])","self.assertEqual(api.convert_value(' 2 ','int'),2)","self.assertEqual(report.ingest('x\\n2\\n',{'x':'int'},['x'])['valid_rows'],[{'x':2}])"],cases=[
["self.assertEqual(api.parse_header([' a ','b']),['a','b'])","for names in [['a',' a '],['']]:\n    with self.assertRaises(ValueError): api.parse_header(names)"],
["self.assertEqual(api.convert_value('-02','int'),-2); self.assertIs(api.convert_value('false','bool'),False); self.assertIs(api.convert_value('true','bool'),True); self.assertIsNone(api.convert_value(' ','str')); self.assertEqual(api.convert_value(' 2.5e1 ','float'),25); self.assertEqual(api.convert_value(' text ','str'),'text')","for value,kind in [('True','bool'),('1.0','int'),('nan','float'),('','unknown')]:\n    with self.assertRaises(ValueError): api.convert_value(value,kind)"],
["self.assertEqual(api.read_table(' a,b\\n\"x,y\",2\\n\\n'),[{'a':'x,y','b':'2'}])","self.assertEqual(api.read_table(''),[]);\nwith self.assertRaises(ValueError): api.read_table('a,b\\n1\\n')"],
["v,e=api.validate_rows([{'x':'2','y':'true'},{'x':'bad','y':'TRUE'}],{'y':'bool','x':'int'},['x']); self.assertEqual(v,[{'x':2,'y':True}]); self.assertEqual(e,[{'row':2,'columns':['x','y']}])","v,e=api.validate_rows([{}, {'x':'0','extra':'x'}],{'x':'int'},['x']); self.assertEqual(v,[{'x':0}]); self.assertEqual(e,[{'row':1,'columns':['x']}])"],
["self.assertEqual(report.ingest('x\\n1\\nbad\\n',{'x':'int'},['x']),{'valid_rows':[{'x':1}],'errors':[{'row':2,'columns':['x']}],'total_rows':2})","with self.assertRaises(ValueError): report.ingest('x,x\\n1,2',{'x':'int'},[])\nself.assertEqual(report.ingest('',{'x':'int'},[]),dict(valid_rows=[],errors=[],total_rows=0))"]]),
dict(id='task_003',title='Record columnar round-trip',family='ingestion',functions=['flatten_record','unflatten_record','to_columns','from_columns','roundtrip_report'],
requirements=[
"flatten_record(record) recursively flattens nested dictionaries to tuple-of-string paths, treats lists and empty dictionaries as leaf values, deep-copies leaves, and represents an empty root dictionary as {():{}}.",
"unflatten_record(flat) reconstructs a dictionary from tuple paths, deep-copies values, and rejects non-string path segments, empty non-root paths, leaf/parent conflicts, or a root marker combined with other paths with ValueError; an empty flat mapping yields {} and a sole root marker must contain {}.",
"to_columns(records) returns a path-sorted dictionary of flattened leaf columns, each a list with None for absent paths; an empty input returns {}, and every record contributes one slot to each column.",
"from_columns(columns) requires equal column lengths, rejects mismatches with ValueError, and reconstructs one record per position using non-None cells; empty columns returns [], and entirely None rows become {}.",
"roundtrip_report(records) in reporting.py returns columns,row_count,missing_cells; row_count is the original number of records, and missing_cells counts None cells across the produced columns."
],extra="Record keys are strings. Scalar leaves exclude None, which is reserved as a missing-cell marker. Empty dictionaries and lists are legitimate leaves. Tuple paths sort lexicographically. Do not mutate inputs.",core='''
import copy
def flatten_record(record):
    result={}
    def visit(node,path):
        if isinstance(node,dict) and node:
            for key,value in node.items(): visit(value,path+(key,))
        else: result[path]=copy.deepcopy(node)
    visit(record,())
    return result
def unflatten_record(flat):
    if not flat: return {}
    if () in flat:
        if len(flat)!=1 or flat[()]!={}: raise ValueError('bad root')
        return {}
    out={}; leaves=set()
    for path,value in sorted(flat.items(),key=lambda item:len(item[0])):
        if not isinstance(path,tuple) or not path or any(not isinstance(k,str) for k in path): raise ValueError('bad path')
        node=out
        for depth,key in enumerate(path[:-1],1):
            if path[:depth] in leaves: raise ValueError('parent conflict')
            node=node.setdefault(key,{})
        if path[-1] in node: raise ValueError('leaf conflict')
        node[path[-1]]=copy.deepcopy(value); leaves.add(path)
    return out
def to_columns(records):
    rows=[flatten_record(r) for r in records]; paths=sorted(set().union(*(r.keys() for r in rows))) if rows else []
    return {path:[copy.deepcopy(row.get(path)) for row in rows] for path in paths}
def from_columns(columns):
    lengths={len(values) for values in columns.values()}
    if len(lengths)>1: raise ValueError('unequal lengths')
    if not lengths: return []
    return [unflatten_record({path:values[i] for path,values in columns.items() if values[i] is not None}) for i in range(next(iter(lengths)))]
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def roundtrip_report(records):
    columns=api.to_columns(records)
    return {'columns':columns,'row_count':len(records),'missing_cells':sum(v is None for values in columns.values() for v in values)}
''',public=["self.assertEqual(api.flatten_record({'x':{'y':2}}),{('x','y'):2})","self.assertEqual(api.unflatten_record({('x',):2}),{'x':2})","self.assertEqual(report.roundtrip_report([{'x':1}])['row_count'],1)"],cases=[
["self.assertEqual(api.flatten_record({'a':{},'b':[1]}),{('a',):{},('b',):[1]}); self.assertEqual(api.flatten_record({}),{():{}})","r={'x':[1]}; o=api.flatten_record(r); o[('x',)].append(2); self.assertEqual(r,{'x':[1]})"],
["self.assertEqual(api.unflatten_record({('a','b'):1,('a','c'):[]}),{'a':{'b':1,'c':[]}})","for f in [{():{},('x',):1},{('a',):{},('a','b'):2},{(1,):2},{():1}]:\n    with self.assertRaises(ValueError): api.unflatten_record(f)"],
["self.assertEqual(api.to_columns([{'x':1},{'y':2}]),{('x',):[1,None],('y',):[None,2]})","self.assertEqual(api.to_columns([]),{}); self.assertEqual(api.to_columns([{},{}]),{():[{},{}]})"],
["self.assertEqual(api.from_columns({('x',):[1,None]}),[{'x':1},{}])","with self.assertRaises(ValueError): api.from_columns({('x',):[1],('y',):[]})\nself.assertEqual(api.from_columns({}),[])"],
["self.assertEqual(report.roundtrip_report([{'a':1},{'b':2}]),{'columns':{('a',):[1,None],('b',):[None,2]},'row_count':2,'missing_cells':2})","self.assertEqual(report.roundtrip_report([]),{'columns':{},'row_count':0,'missing_cells':0})"]]),
dict(id='task_004',title='Versioned score-table migration',family='ingestion',functions=['convert_score','rename_fields','migrate_row','migrate_table','migration_report'],
requirements=[
"convert_score(value,unit) accepts finite non-bool numbers, converts unit fraction unchanged and percent by dividing by 100, then requires the result in [0,1]; invalid units or values raise ValueError.",
"rename_fields(row,mapping) performs simultaneous key renaming on a deep copy, preserving unmapped keys, and raises ValueError if two existing source keys would collide at one destination; mappings for absent keys are ignored.",
"migrate_row(row) accepts version 1 rows with run_id and percent score, or version 2 rows with id and __SF_PRIMARY_SCORE__; outputs version=2,id stripped nonempty string,__SF_PRIMARY_SCORE__ as fraction, and metadata as a deep copy defaulting to {}; unsupported versions or invalid IDs/scores raise ValueError.",
"migrate_table(rows) returns (valid,errors), migrating independently and recording one-based input indices of ValueError failures while preserving successful order and not mutating inputs.",
"migration_report(rows) in reporting.py returns migrated,errors,duplicate_ids; duplicate_ids is a sorted list of IDs occurring more than once among successful migrations, each listed once."
],extra="For migrate_row, required version-1 fields are version,run_id,score; version-2 fields are version,id,__SF_PRIMARY_SCORE__. Missing required fields raise ValueError. Extra top-level fields are omitted from migrated rows; metadata is JSON-compatible. Version must be int excluding bool.",core='''
import copy
import math
def convert_score(value,unit):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or unit not in {'fraction','percent'}: raise ValueError('bad score')
    result=value/100 if unit=='percent' else value
    if not 0<=result<=1: raise ValueError('score range')
    return result
def rename_fields(row,mapping):
    out={}
    for key,value in row.items():
        target=mapping.get(key,key)
        if target in out: raise ValueError('rename collision')
        out[target]=copy.deepcopy(value)
    return out
def migrate_row(row):
    if type(row.get('version')) is not int or row['version'] not in (1,2): raise ValueError('bad version')
    old=row['version']==1; id_key='run_id' if old else 'id'; score_key='score' if old else '__SF_PRIMARY_SCORE__'
    if id_key not in row or score_key not in row or not isinstance(row[id_key],str) or not row[id_key].strip(): raise ValueError('bad row')
    return {'version':2,'id':row[id_key].strip(),'__SF_PRIMARY_SCORE__':convert_score(row[score_key],'percent' if old else 'fraction'),'metadata':copy.deepcopy(row.get('metadata',{}))}
def migrate_table(rows):
    valid=[]; errors=[]
    for index,row in enumerate(rows,1):
        try: valid.append(migrate_row(row))
        except ValueError: errors.append(index)
    return valid,errors
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def migration_report(rows):
    valid,errors=api.migrate_table(rows); counts={}
    for row in valid: counts[row['id']]=counts.get(row['id'],0)+1
    return {'migrated':valid,'errors':errors,'duplicate_ids':sorted(k for k,v in counts.items() if v>1)}
''',public=["self.assertEqual(api.convert_score(50,'percent'),.5)","self.assertEqual(api.rename_fields({'a':1},{'a':'b'}),{'b':1})","self.assertEqual(report.migration_report([])['duplicate_ids'],[])"],cases=[
["self.assertEqual(api.convert_score(1,'fraction'),1); self.assertEqual(api.convert_score(0,'percent'),0)","for value,unit in [(True,'fraction'),(101,'percent'),(float('inf'),'fraction'),(.5,'other')]:\n    with self.assertRaises(ValueError): api.convert_score(value,unit)"],
["self.assertEqual(api.rename_fields({'a':1,'b':2},{'a':'b','b':'a'}),{'b':1,'a':2})","with self.assertRaises(ValueError): api.rename_fields({'a':1,'b':2},{'a':'b'})\nr={'a':[]}; o=api.rename_fields(r,{}); o['a'].append(1); self.assertEqual(r,{'a':[]})"],
["self.assertEqual(api.migrate_row({'version':1,'run_id':' x ','score':25}),{'version':2,'id':'x','__SF_PRIMARY_SCORE__':.25,'metadata':{}}); row={'version':2,'id':' y ','__SF_PRIMARY_SCORE__':.7,'metadata':{'x':[]},'extra':1}; out=api.migrate_row(row); self.assertEqual(out,{'version':2,'id':'y','__SF_PRIMARY_SCORE__':.7,'metadata':{'x':[]}}); out['metadata']['x'].append(1); self.assertEqual(row['metadata'],{'x':[]})","for row in [{'version':True,'run_id':'x','score':2},{'version':2,'id':'x'},{'version':2,'id':' ','__SF_PRIMARY_SCORE__':.5}]:\n    with self.assertRaises(ValueError): api.migrate_row(row)"],
["v,e=api.migrate_table([{'version':1,'run_id':'a','score':50},{'version':9},{'version':2,'id':'b','__SF_PRIMARY_SCORE__':0}]); self.assertEqual([r['id'] for r in v],['a','b']); self.assertEqual(e,[2])","self.assertEqual(api.migrate_table([]),([],[]))"],
["rows=[{'version':1,'run_id':'x','score':50},{'version':2,'id':'x','__SF_PRIMARY_SCORE__':1}]; self.assertEqual(report.migration_report(rows),{'migrated':[{'version':2,'id':'x','__SF_PRIMARY_SCORE__':.5,'metadata':{}},{'version':2,'id':'x','__SF_PRIMARY_SCORE__':1,'metadata':{}}],'errors':[],'duplicate_ids':['x']})","self.assertEqual(report.migration_report([{'version':8}]),dict(migrated=[],errors=[1],duplicate_ids=[]))"]])
]
