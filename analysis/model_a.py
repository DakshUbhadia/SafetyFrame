"""Model-A phase analysis, only after every frozen A run is terminal."""
import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
import io
from pathlib import Path
import re
import sys

from harness.artifacts import confined,digest,read_json,tree_hash,write_json
from harness.bootstrap import complete_contrast,paired_bootstrap
from harness.freeze import planned_rows,verify_freeze
from harness.preflight import ROOT,nonnegative_number
from harness.scoring import aggregate_assessments,assess

CONDITIONS=('C','S','CD','SD')
PUBLIC_FIELDS=('run_id','task_id','task_family','model_id','returned_model_id','provider',
    'condition','status','phase','block_id','within_block_order','format_success_turn1',
    'format_success_turn2','artifact_tcs_turn1','artifact_tcs_turn2','tcs_turn1','tcs_turn2',
    'repair_gain','requirements_passed_turn1','requirements_passed_turn2','requirements_total',
    'provider_failure_type','retry_count','primary_analysis_included','end_to_end_utility_score',
    'input_tokens','output_tokens','reported_cost','estimated_cost','cost_accounting_complete',
    'latency_seconds','timestamp_turn1','timestamp_turn2','prompt_hash','repo_hash','test_hash')


def attempt_usage(outcome):
    usage=outcome.get('result',{}).get('summary',{}).get('usage')
    if not usage and isinstance(outcome.get('raw'),dict):
        usage=outcome['raw'].get('usage')
    return usage if isinstance(usage,dict) else {}


def audit_attempts(raw_dir,model,execution,expected_context):
    """Check persisted request/outcome pairs against the frozen retry policy."""
    requests={p.name.removesuffix('-request.json'):p for p in raw_dir.glob('*-request.json')}
    outcomes={p.name.removesuffix('-outcome.json'):p for p in raw_dir.glob('*-outcome.json')}
    if not requests or requests.keys()!=outcomes.keys():
        raise ValueError('Unreconciled request/outcome pair')
    turns={1:[],2:[]}
    entries=[]
    for prefix,path in sorted(outcomes.items()):
        match=re.fullmatch(r'turn([12])-attempt([0-9]+)',prefix)
        if not match: raise ValueError('Unknown attempt filename')
        turn,index=map(int,match.groups())
        request=read_json(requests[prefix]); outcome=read_json(path)
        if (request['turn']!=turn or request['attempt']!=index or outcome['turn']!=turn
                or outcome['attempt']!=index or request['model_id']!=model['model_id']
                or request['generation']!=model['generation']
                or request['context']!=expected_context or outcome['context']!=expected_context):
            raise ValueError('Request/outcome differs from frozen run identity')
        turns[turn].append((index,outcome))
        entries.append((path,outcome,digest(request)))
    for turn,attempts in turns.items():
        if not attempts: continue
        indices=[i for i,outcome in attempts]
        if indices!=list(range(len(indices))) or indices[-1]>execution['maximum_retries_per_turn']:
            raise ValueError('Attempt sequence exceeds frozen retry policy')
        for _,previous in attempts[:-1]:
            if ('result' in previous or not previous.get('retryable')
                    or previous.get('failure') not in execution['retryable']):
                raise ValueError('Nonretryable response was rerun')
    if not turns[1] or (turns[2] and 'result' not in turns[1][-1][1]):
        raise ValueError('Turn 2 precedes a successful Turn 1 response')
    return entries


def load_phase(output=ROOT/'data/main'):
    """Validate all terminal identities and workspaces before releasing summaries."""
    manifest=verify_freeze()
    rows=[r for r in planned_rows() if r['role']=='A']
    missing=[r['run_id'] for r in rows if not (output/'scored'/f"{r['run_id']}.json").exists()]
    if missing: raise ValueError(f'Model A is incomplete: {len(missing)} planned runs lack terminal records')
    release=[]
    model=read_json(ROOT/'config/study.json')['models']['A']
    execution=read_json(ROOT/'config/execution.json')
    for planned in rows:
        run=planned['run_id']
        record_path=output/'scored'/f'{run}.json'
        record=read_json(record_path); row=record['trajectory']
        state=read_json(output/'runs'/run/'state.json')
        identity=read_json(output/'runs'/run/'identity.json')
        if (state.get('result_hash')!=digest(record) or row['status'] not in ('completed','provider_failed')
                or row['run_id']!=run or row['task_id']!=planned['task_id']
                or row['model_id']!=planned['model_id'] or row['condition']!=planned['condition']
                or row['block_id']!=planned['block_id'] or row['phase']!='final'
                or int(row['within_block_order'])!=int(planned['within_block_order'])
                or identity['role']!='A' or identity['configuration_hash']!=manifest['configuration_hash']
                or identity['condition']!=planned['condition']):
            raise ValueError('Terminal identity/checksum mismatch: '+run)
        public_turns=[]
        for number,turn in enumerate(record['turns'],1):
            workspace=Path(turn['workspace_path'])
            raw=Path(turn['raw_path'])
            if (workspace.resolve()!=(output/('turn1_snapshots' if number==1 else 'final_snapshots')/run).resolve()
                    or not raw.resolve().is_relative_to((output/'raw'/run).resolve())
                    or tree_hash(workspace)!=turn['workspace_hash']
                    or digest(read_json(raw)['result'])!=turn['response_hash']
                    or turn['executor']['image_id']!=manifest['executor']['image_id']):
                raise ValueError('Raw response/workspace checksum mismatch: '+run)
            if set(turn['requirements'])!={f'R{i}' for i in range(1,6)}:
                raise ValueError('Requirement IDs differ: '+run)
            artifact=sum(turn['requirements'].values())/5
            if (turn['artifact_tcs']!=artifact or turn['tcs']!=(artifact if turn['format_success'] else 0)
                    or turn['assessment']!=assess(turn['requirements'],turn['claims'])
                    or row[f'tcs_turn{number}']!=turn['tcs']):
                raise ValueError('Stored score/claim counts disagree with frozen scoring: '+run)
            public_turns.append({k:turn[k] for k in
                ('requirements','claims','claim_issues','format_success','artifact_tcs','tcs','assessment',
                 'requirements_passed','workspace_hash','response_hash')})
        if row['status']=='completed' and len(public_turns)!=2: raise ValueError('Completed run needs both turns')
        attempts=[]
        context={key:planned[key] for key in ('run_id','task_id','condition','provider','block_id','role')}
        context['within_block_order']=int(planned['within_block_order'])
        for path,outcome,request_hash in audit_attempts(output/'raw'/run,model,execution,context):
            usage=attempt_usage(outcome)
            estimated=None
            if all(nonnegative_number(usage.get(key)) for key in ('input_tokens','output_tokens')):
                rates=model['pricing']
                estimated=(usage['input_tokens']*rates['input_credits_per_million']+usage['output_tokens']*rates['output_credits_per_million'])/1e6
            attempts.append(dict(file=path.relative_to(ROOT).as_posix(),outcome_hash=digest(outcome),request_hash=request_hash,
                failure=outcome.get('failure'),attempt=outcome['attempt'],
                reported_cost=usage.get('cost') if nonnegative_number(usage.get('cost')) else None,
                estimated_cost=estimated,input_tokens=usage.get('input_tokens'),output_tokens=usage.get('output_tokens')))
        release.append(dict(trajectory={key:row.get(key) for key in PUBLIC_FIELDS},turns=public_turns,
                            attempts=attempts,record_hash=digest(record),identity_hash=digest(identity)))
    return dict(schema_version=1,role='A',freeze_hash=digest(manifest),source_checkpoint=manifest['git_commit'],
                analysis_config_hash=digest(read_json(ROOT/'config/analysis.json')),records=release)


def mean(values):
    return sum(values)/len(values) if values else None


def summarize(dataset,config):
    records=dataset['records']
    if len(records)!=64: raise ValueError('Model-A analysis requires all 64 planned terminal records')
    identities=[(r['trajectory']['task_id'],r['trajectory']['condition']) for r in records]
    tasks=sorted({task for task,condition in identities})
    if len(tasks)!=16 or len(set(identities))!=64 or set(identities)!={(t,c) for t in tasks for c in CONDITIONS}:
        raise ValueError('Expected the complete sixteen-task factorial plan')
    rows=[r['trajectory'] for r in records]
    if any(r['status'] not in ('completed','provider_failed') for r in rows): raise ValueError('Nonterminal data')
    settings=config['bootstrap']
    completed={c:{r['task_id']:r['tcs_turn2'] for r in rows if r['condition']==c and r['status']=='completed'} for c in CONDITIONS}
    task_rows={task:{} for task in tasks}
    utility={task:{} for task in tasks}; valid_format={task:{} for task in tasks}
    for row in rows:
        t=row['task_id']; c=row['condition']
        task_rows[t][c]=row['tcs_turn2'] if row['status']=='completed' else None
        utility[t][c]=row['end_to_end_utility_score']
        valid_format[t][c]=row['tcs_turn2'] if row['status']=='completed' and row['format_success_turn2'] else None
    conditions={}
    for c in CONDITIONS:
        selected=[r for r in rows if r['condition']==c]; done=[r for r in selected if r['status']=='completed']
        conditions[c]={**paired_bootstrap(completed[c],settings),'planned':16,'completed':len(done),
            'provider_failed':sum(r['status']=='provider_failed' for r in selected),
            'failures_by_type':dict(Counter(r['provider_failure_type'] for r in selected if r['status']=='provider_failed')),
            'turn1_mean':mean([r['tcs_turn1'] for r in selected if r['tcs_turn1'] is not None]),
            'artifact_turn2_mean':mean([r['artifact_tcs_turn2'] for r in done]),
            'repair_gain_mean':mean([r['repair_gain'] for r in done]),
            'turn2_format_failures':sum(r['format_success_turn2'] is False for r in done),
            'turn2_format_evaluable':len(done)}
    contrasts={}
    specs={**config['contrasts'],**config['secondary_contrasts']}
    for name,spec in specs.items():
        if spec['role']!='A': continue
        weights=spec['weights']; values=complete_contrast(task_rows,weights)
        contrasts[name]={**paired_bootstrap(values,settings),'task_values':values,
            'matched_condition_means':{c:mean([task_rows[t][c] for t in values]) for c in weights},
            'utility_sensitivity':paired_bootstrap(complete_contrast(utility,weights),settings),
            'valid_format_sensitivity':paired_bootstrap(complete_contrast(valid_format,weights),settings)}
    assessments={}
    for c in ('CD','SD'):
        assessments[c]={}
        for number in (1,2):
            turns=[r['turns'][number-1] for r in records if r['trajectory']['condition']==c and len(r['turns'])>=number]
            values=[assess(t['requirements'],t['claims']) for t in turns]
            assessments[c][str(number)]={'metrics':aggregate_assessments(values),'evaluable_trajectories':len(turns),
                'claim_issues':sum(bool(t['claim_issues']) for t in turns),
                'counts':{name:sum(v[name] or 0 for v in values) for name in
                    ('actual_failed_requirements','claimed_implemented','claimed_unmet','claimed_uncertain','claimed_missing',
                     'failed_claimed_implemented','failed_acknowledged','failed_acknowledged_lenient')}}
    attempts=[a for r in records for a in r.get('attempts',[])]
    costs={'known_reported_cost':sum(a['reported_cost'] for a in attempts if a['reported_cost'] is not None),
           'known_token_estimated_cost':sum(a['estimated_cost'] for a in attempts if a['estimated_cost'] is not None),
           'outcomes_with_unknown_usage':sum(a['estimated_cost'] is None for a in attempts),
           'attempts':len(attempts),'retries':sum(r['retry_count'] or 0 for r in rows)}
    return dict(schema_version=1,role='A',planned=64,terminal=64,task_count=16,
        freeze_hash=dataset['freeze_hash'],dataset_hash=digest(dataset),analysis_config_hash=digest(config),conditions=conditions,
        contrasts=contrasts,self_assessment=assessments,costs=costs,task_outcomes=task_rows,
        no_model_b_results=True)


def write_csv(path,columns,rows):
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows); path.write_text(stream.getvalue(),encoding='utf-8',newline='\n')


def tables(dataset,summary,output):
    write_csv(output/'model_a_trajectories.csv',PUBLIC_FIELDS,[r['trajectory'] for r in dataset['records']])
    write_csv(output/'model_a_conditions.csv',
        ['condition','planned','completed','provider_failed','mean_tcs_turn2','lower','upper','mean_tcs_turn1','repair_gain','format_failures'],
        [dict(condition=c,planned=v['planned'],completed=v['completed'],provider_failed=v['provider_failed'],
              mean_tcs_turn2=v['estimate'],lower=v['lower'],upper=v['upper'],mean_tcs_turn1=v['turn1_mean'],
              repair_gain=v['repair_gain_mean'],format_failures=v['turn2_format_failures']) for c,v in summary['conditions'].items()])
    write_csv(output/'model_a_contrasts.csv',['contrast','paired_tasks','estimate','lower','upper','utility_estimate','valid_format_estimate'],
        [dict(contrast=name,paired_tasks=v['tasks'],estimate=v['estimate'],lower=v['lower'],upper=v['upper'],
              utility_estimate=v['utility_sensitivity']['estimate'],valid_format_estimate=v['valid_format_sensitivity']['estimate'])
         for name,v in summary['contrasts'].items()])
    write_csv(output/'model_a_self_assessment.csv',
        ['condition','turn','metric','numerator','denominator','micro','macro','defined_tasks','tasks'],
        [dict(condition=c,turn=turn,metric=metric,**values)
         for c,turns in summary['self_assessment'].items() for turn,assessment in turns.items()
         for metric,values in assessment['metrics'].items()])
    write_csv(output/'model_a_task_differences.csv',['task_id','C','S','CD','SD','C_minus_S','CD_minus_C','SD_minus_S','interaction'],
        [dict(task_id=t,**v,C_minus_S=summary['contrasts']['BaselineSafetyGap_A']['task_values'].get(t),
              CD_minus_C=summary['contrasts']['DisclosureEffect_C_A']['task_values'].get(t),
              SD_minus_S=summary['contrasts']['DisclosureEffect_S_A']['task_values'].get(t),
              interaction=summary['contrasts']['DisclosureFramingInteraction_A']['task_values'].get(t))
         for t,v in summary['task_outcomes'].items()])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,help='Reproduce from the released text-free scored dataset')
    parser.add_argument('--output',type=Path,default=ROOT/'report/model_a')
    args=parser.parse_args()
    dataset=read_json(args.dataset) if args.dataset else load_phase()
    manifest=verify_freeze()
    config=read_json(ROOT/'config/analysis.json')
    if dataset['freeze_hash']!=digest(manifest) or dataset['analysis_config_hash']!=digest(config):
        raise ValueError('Dataset belongs to a different freeze or analysis policy')
    result=summarize(dataset,config)
    args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/'scored_dataset.json',dataset)
    write_json(args.output/'summary.json',result)
    tables(dataset,result,args.output)
    from .model_a_figures import figures,report_text
    figures(result,args.output)
    (args.output/'results.md').write_text(report_text(result),encoding='utf-8',newline='\n')
    print(f'Model A: 64 terminal records validated; analysis, tables, and figures saved to {args.output}')


if __name__=='__main__':
    main()
