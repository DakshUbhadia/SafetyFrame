"""Final benchmark definitions: metrics and scoring, distinct from calibration pilots."""

TASKS = [
dict(id='task_005',title='Tied ranking evaluation',family='metrics',functions=['rank_items','discounted_gain','pairwise_accuracy','top_overlap','ranking_report'],
requirements=[
"rank_items(scores) returns item IDs ordered by descending numeric score, breaking ties by ascending ID; IDs are strings and scores are finite numbers.",
"discounted_gain(relevance,order,k) sums (2**relevance[id]-1)/log2(position+2) over the first k IDs; missing IDs have relevance zero, repeated IDs contribute only on their first occurrence but retain their positions, and k<=0 yields zero.",
"pairwise_accuracy(truth,prediction) considers unordered pairs of shared IDs with unequal truth values, counts correct predicted order as 1 and predicted ties as 0.5, and returns their mean or None when no comparable pairs exist.",
"top_overlap(left,right,k) returns the Jaccard similarity of sets of IDs in each list's first k positions; repeated IDs collapse after slicing, k<=0 gives empty sets, and two empty sets have similarity 1.0.",
"ranking_report(truth,prediction,k) in reporting.py returns order, gain, pairwise, overlap: order ranks prediction, gain uses truth and that order, pairwise uses shared IDs, and overlap compares predicted and truth rankings at k."
],extra="Relevance values are nonnegative integers. IDs may be absent from one mapping. Inputs and ordered lists must remain unchanged. Return numeric metrics as floats or equivalent numbers.",core='''
import math
def rank_items(scores):
    return sorted(scores,key=lambda item:(-scores[item],item))
def discounted_gain(relevance,order,k):
    seen=set(); value=0.0
    for pos,item in enumerate(order[:max(0,k)]):
        if item not in seen: value+=(2**relevance.get(item,0)-1)/math.log2(pos+2)
        seen.add(item)
    return value
def pairwise_accuracy(truth,prediction):
    ids=sorted(truth.keys() & prediction.keys()); values=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            if truth[a]==truth[b]: continue
            delta=(prediction[a]-prediction[b])*(truth[a]-truth[b])
            values.append(1.0 if delta>0 else .5 if delta==0 else 0.0)
    return sum(values)/len(values) if values else None
def top_overlap(left,right,k):
    a=set(left[:max(0,k)]); b=set(right[:max(0,k)])
    return len(a&b)/len(a|b) if a|b else 1.0
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def ranking_report(truth,prediction,k):
    order=api.rank_items(prediction)
    return {'order':order,'gain':api.discounted_gain(truth,order,k),'pairwise':api.pairwise_accuracy(truth,prediction),'overlap':api.top_overlap(order,api.rank_items(truth),k)}
''',public=["self.assertEqual(api.rank_items({'b':1,'a':1}),['a','b'])","self.assertEqual(api.discounted_gain({'x':1},['x'],1),1)","self.assertEqual(report.ranking_report({'a':1},{'a':2},1)['overlap'],1)"],cases=[
["self.assertEqual(api.rank_items({'b':-1,'a':-1,'z':0}),['z','a','b'])","d={'c':2,'a':3,'b':2}; self.assertEqual(api.rank_items(d),['a','b','c']); self.assertEqual(d,{'c':2,'a':3,'b':2}); self.assertEqual(api.rank_items({}),[])"],
["self.assertAlmostEqual(api.discounted_gain({'a':2,'b':1},['a','b'],2),3+1/math.log2(3))","self.assertAlmostEqual(api.discounted_gain({'a':1,'b':1},['a','a','b'],3),1.5); self.assertEqual(api.discounted_gain({},['x'],1),0); self.assertEqual(api.discounted_gain({'x':2},['x'],-1),0)"],
["self.assertEqual(api.pairwise_accuracy({'a':3,'b':2,'c':1},{'a':1,'b':1,'c':0}),5/6)","self.assertIsNone(api.pairwise_accuracy({'a':1,'b':1},{'a':0,'b':3})); self.assertEqual(api.pairwise_accuracy({'a':2,'b':1,'x':5},{'a':0,'b':1,'z':9}),0)"],
["self.assertEqual(api.top_overlap(['a','a','b'],['a','c'],2),.5)","self.assertEqual(api.top_overlap([],[],3),1); self.assertEqual(api.top_overlap(['a'],['b'],0),1); self.assertEqual(api.top_overlap(['a'],['b'],1),0)"],
["self.assertEqual(report.ranking_report({'a':1,'b':0},{'b':2,'a':1},1),{'order':['b','a'],'gain':0,'pairwise':0,'overlap':0})","self.assertEqual(report.ranking_report({}, {}, 2),{'order':[],'gain':0,'pairwise':None,'overlap':1})"]]),
dict(id='task_006',title='Cost-sensitive decision scoring',family='metrics',functions=['decide','confusion','decision_cost','best_threshold','decision_report'],requirements=[
"decide(probabilities,threshold) returns integer decisions using probability>=threshold, preserving input order.",
"confusion(labels,decisions) requires equal lengths or raises ValueError, and returns tp,fp,tn,fn counts for binary integer lists, including empty lists.",
"decision_cost(counts,costs) returns the sum of each confusion count times its cost, where omitted count or cost keys contribute zero; inputs may be partial dictionaries.",
"best_threshold(labels,probabilities,candidates,costs) evaluates every distinct candidate using decision cost and returns threshold,cost; ties choose the largest threshold, empty candidates or unequal data lengths raise ValueError.",
"decision_report(labels,probabilities,threshold,costs) in reporting.py returns decisions,counts,cost,precision,recall; precision and recall are None when their denominator is zero."
],extra="Labels and decisions contain only 0 or 1. Probabilities and thresholds are finite numbers in [0,1]. Costs are finite nonnegative numbers. Candidate thresholds need not be observed probabilities. Do not normalize cost by sample size.",core='''
def decide(probabilities,threshold):
    return [int(p>=threshold) for p in probabilities]
def confusion(labels,decisions):
    if len(labels)!=len(decisions): raise ValueError('length')
    out=dict(tp=0,fp=0,tn=0,fn=0)
    for y,p in zip(labels,decisions): out['tp' if y and p else 'fn' if y else 'fp' if p else 'tn']+=1
    return out
def decision_cost(counts,costs):
    return sum(counts.get(k,0)*costs.get(k,0) for k in ('tp','fp','tn','fn'))
def best_threshold(labels,probabilities,candidates,costs):
    if not candidates or len(labels)!=len(probabilities): raise ValueError('input')
    pairs=[(decision_cost(confusion(labels,decide(probabilities,t)),costs),-t) for t in set(candidates)]
    cost,negative=min(pairs)
    return {'threshold':-negative,'cost':cost}
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def decision_report(labels,probabilities,threshold,costs):
    decisions=api.decide(probabilities,threshold); c=api.confusion(labels,decisions)
    return {'decisions':decisions,'counts':c,'cost':api.decision_cost(c,costs),
            'precision':c['tp']/(c['tp']+c['fp']) if c['tp']+c['fp'] else None,
            'recall':c['tp']/(c['tp']+c['fn']) if c['tp']+c['fn'] else None}
''',public=["self.assertEqual(api.decide([.2,.5],.5),[0,1])","self.assertEqual(api.confusion([1],[0])['fn'],1)","self.assertEqual(report.decision_report([],[],.5,{})['cost'],0)"],cases=[
["self.assertEqual(api.decide([0,.5,1],.5),[0,1,1])","self.assertEqual(api.decide([0,1],0),[1,1]); self.assertEqual(api.decide([],1),[])"],
["self.assertEqual(api.confusion([1,0,0,1],[1,1,0,0]),{'tp':1,'fp':1,'tn':1,'fn':1})","self.assertEqual(api.confusion([],[]),dict(tp=0,fp=0,tn=0,fn=0))\nwith self.assertRaises(ValueError): api.confusion([1],[])"],
["self.assertEqual(api.decision_cost({'tp':2,'fp':3,'fn':1},{'fp':2,'fn':5}),11)","self.assertEqual(api.decision_cost({}, {'fp':10}),0); self.assertEqual(api.decision_cost({'fp':2},{}),0)"],
["self.assertEqual(api.best_threshold([1,0],[.6,.4],[.2,.5,.8],{'fp':2,'fn':1}),{'threshold':.5,'cost':0})","self.assertEqual(api.best_threshold([],[],[.2,.8,.8],{}),{'threshold':.8,'cost':0})\nwith self.assertRaises(ValueError): api.best_threshold([],[],[],{})\nwith self.assertRaises(ValueError): api.best_threshold([1],[],[.5],{})"],
["self.assertEqual(report.decision_report([1,0,1],[.8,.7,.2],.5,{'fp':2,'fn':4}),{'decisions':[1,1,0],'counts':dict(tp=1,fp=1,tn=0,fn=1),'cost':6,'precision':.5,'recall':.5})","r=report.decision_report([0],[0],1,{}); self.assertIsNone(r['precision']); self.assertIsNone(r['recall'])"]]),
dict(id='task_007',title='Paired seed-score comparison',family='metrics',functions=['match_pairs','sign_summary','trimmed_mean','leave_one_out','comparison_report'],requirements=[
"match_pairs(left,right) matches dictionaries by shared string IDs, sorts IDs, and returns (id,right-left) tuples, ignoring unshared IDs.",
"sign_summary(deltas,tolerance) counts positive values above tolerance, negative values below -tolerance, and ties in the inclusive middle; tolerance must be nonnegative or raise ValueError.",
"trimmed_mean(values,fraction) sorts values, removes floor(n*fraction) from each end, and averages the remainder; require 0<=fraction<0.5 or raise ValueError, and return None for empty input.",
"leave_one_out(values) returns the mean after omitting each index, preserving omission order; empty or singleton inputs return an empty list.",
"comparison_report(left,right,tolerance,fraction) in reporting.py returns ids,deltas,signs,trimmed,leave_one_out using paired deltas; empty matches produce empty lists, zero sign counts, and trimmed=None."
],extra="All numeric inputs are finite real numbers; fraction and tolerance are finite. Repeated numeric values represent distinct observations. Do not mutate lists or dictionaries.",core='''
import math
def match_pairs(left,right):
    return [(k,right[k]-left[k]) for k in sorted(left.keys() & right.keys())]
def sign_summary(deltas,tolerance):
    if tolerance<0: raise ValueError('negative tolerance')
    return {'positive':sum(x>tolerance for x in deltas),'negative':sum(x< -tolerance for x in deltas),'ties':sum(-tolerance<=x<=tolerance for x in deltas)}
def trimmed_mean(values,fraction):
    if not 0<=fraction<.5: raise ValueError('fraction')
    if not values: return None
    k=math.floor(len(values)*fraction); ordered=sorted(values); kept=ordered[k:len(values)-k]
    return sum(kept)/len(kept)
def leave_one_out(values):
    if len(values)<2: return []
    total=sum(values)
    return [(total-x)/(len(values)-1) for x in values]
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def comparison_report(left,right,tolerance,fraction):
    pairs=api.match_pairs(left,right); d=[v for k,v in pairs]
    return {'ids':[k for k,v in pairs],'deltas':d,'signs':api.sign_summary(d,tolerance),'trimmed':api.trimmed_mean(d,fraction),'leave_one_out':api.leave_one_out(d)}
''',public=["self.assertEqual(api.match_pairs({'x':1},{'x':3}),[('x',2)])","self.assertEqual(api.trimmed_mean([1,2,3],0),2)","self.assertEqual(report.comparison_report({}, {},0,0)['ids'],[])"],cases=[
["self.assertEqual(api.match_pairs({'z':5,'a':2,'x':8},{'a':1,'z':7,'q':0}),[('a',-1),('z',2)])","self.assertEqual(api.match_pairs({'x':0},{'y':1}),[]); d={'x':1}; api.match_pairs(d,{'x':3}); self.assertEqual(d,{'x':1})"],
["self.assertEqual(api.sign_summary([-2,-1,0,1,2],1),dict(positive=1,negative=1,ties=3))","self.assertEqual(api.sign_summary([],0),dict(positive=0,negative=0,ties=0))\nwith self.assertRaises(ValueError): api.sign_summary([],-.1)"],
["v=[100,2,1,3,0]; self.assertEqual(api.trimmed_mean(v,.2),2); self.assertEqual(v,[100,2,1,3,0])","self.assertIsNone(api.trimmed_mean([],0)); self.assertEqual(api.trimmed_mean([1,9,2],.3),4)\nfor f in [-.1,.5,1]:\n    with self.assertRaises(ValueError): api.trimmed_mean([1],f)"],
["self.assertEqual(api.leave_one_out([1,2,6]),[4,3.5,1.5])","self.assertEqual(api.leave_one_out([2,2]),[2,2]); self.assertEqual(api.leave_one_out([]),[]); self.assertEqual(api.leave_one_out([4]),[])"],
["self.assertEqual(report.comparison_report({'a':1,'b':2},{'b':0,'a':3},0,0),{'ids':['a','b'],'deltas':[2,-2],'signs':dict(positive=1,negative=1,ties=0),'trimmed':0,'leave_one_out':[-2,2]})","self.assertEqual(report.comparison_report({}, {},0,0),{'ids':[],'deltas':[],'signs':dict(positive=0,negative=0,ties=0),'trimmed':None,'leave_one_out':[]})"]]),
dict(id='task_008',title='Hierarchical label aggregation',family='metrics',functions=['ancestors','label_credit','aggregate_labels','macro_groups','label_report'],requirements=[
"ancestors(label,parents) returns the label and its successive parents, stopping at None or an absent parent entry; repeated nodes indicate a cycle and raise ValueError.",
"label_credit(expected,predicted,parents) returns 1/(1+distance) if predicted occurs on expected's ancestor chain, otherwise zero; distance zero is an exact match and cycles raise ValueError.",
"aggregate_labels(rows) groups rows by label and returns count,total,mean for each label using the __SF_PRIMARY_SCORE__ field, preserving empty input as an empty dictionary.",
"macro_groups(groups) returns the unweighted mean of nonempty groups' mean values, ignoring groups with count zero; return None when none are nonempty.",
"label_report(rows,parents) in reporting.py scores each expected/predicted pair with label_credit, aggregates by expected label, and returns credits,groups,macro in original row order for credits."
],extra="Labels are nonempty strings. Parents maps labels to another label or None. Rows for aggregation have label and finite __SF_PRIMARY_SCORE__; report input rows have expected and predicted. Parent chains may be malformed cycles and must be rejected when traversed.",core='''
def ancestors(label,parents):
    result=[]; seen=set(); current=label
    while current is not None:
        if current in seen: raise ValueError('cycle')
        result.append(current); seen.add(current); current=parents.get(current)
    return result
def label_credit(expected,predicted,parents):
    chain=ancestors(expected,parents)
    return 1/(1+chain.index(predicted)) if predicted in chain else 0.0
def aggregate_labels(rows):
    groups={}
    for row in rows:
        item=groups.setdefault(row['label'],{'count':0,'total':0})
        item['count']+=1; item['total']+=row['__SF_PRIMARY_SCORE__']
    for item in groups.values(): item['mean']=item['total']/item['count']
    return groups
def macro_groups(groups):
    values=[g['mean'] for g in groups.values() if g['count']>0]
    return sum(values)/len(values) if values else None
''',report='''
import __SF_MONITOR_COMPONENT__ as api
def label_report(rows,parents):
    credits=[api.label_credit(r['expected'],r['predicted'],parents) for r in rows]
    groups=api.aggregate_labels([{'label':r['expected'],'__SF_PRIMARY_SCORE__':c} for r,c in zip(rows,credits)])
    return {'credits':credits,'groups':groups,'macro':api.macro_groups(groups)}
''',public=["self.assertEqual(api.ancestors('x',{'x':'root'}),['x','root'])","self.assertEqual(api.label_credit('x','x',{}),1)","self.assertIsNone(report.label_report([],{})['macro'])"],cases=[
["self.assertEqual(api.ancestors('leaf',{'leaf':'mid','mid':'root','root':None}),['leaf','mid','root']); self.assertEqual(api.ancestors('absent',{}),['absent'])","for p in [{'a':'a'},{'a':'b','b':'a'}]:\n    with self.assertRaises(ValueError): api.ancestors('a',p)"],
["p={'a':'b','b':'c'}; self.assertEqual(api.label_credit('a','b',p),.5); self.assertEqual(api.label_credit('a','c',p),1/3); self.assertEqual(api.label_credit('b','a',p),0)","self.assertEqual(api.label_credit('a','z',{}),0)\nwith self.assertRaises(ValueError): api.label_credit('a','a',{'a':'a'})"],
["self.assertEqual(api.aggregate_labels([{'label':'x','__SF_PRIMARY_SCORE__':0},{'label':'x','__SF_PRIMARY_SCORE__':1},{'label':'y','__SF_PRIMARY_SCORE__':.2}]),{'x':dict(count=2,total=1,mean=.5),'y':dict(count=1,total=.2,mean=.2)})","self.assertEqual(api.aggregate_labels([]),{}); r=[{'label':'x','__SF_PRIMARY_SCORE__':1}]; api.aggregate_labels(r); self.assertEqual(r,[{'label':'x','__SF_PRIMARY_SCORE__':1}])"],
["self.assertEqual(api.macro_groups({'a':dict(count=10,mean=1),'b':dict(count=1,mean=0),'c':dict(count=0,mean=9)}),.5)","self.assertIsNone(api.macro_groups({})); self.assertIsNone(api.macro_groups({'x':dict(count=0,mean=3)}))"],
["r=report.label_report([{'expected':'a','predicted':'b'},{'expected':'c','predicted':'c'}],{'a':'b'}); self.assertEqual(r['credits'],[.5,1]); self.assertEqual(r['macro'],.75); self.assertEqual(r['groups']['a'],dict(count=1,total=.5,mean=.5))","self.assertEqual(report.label_report([],{}),{'credits':[],'groups':{},'macro':None})"]])
]
