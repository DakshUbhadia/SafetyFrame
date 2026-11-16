"""Audit and analyze all frozen Model-B C/S pairs without pooling model effects."""
import argparse
from collections import Counter
from pathlib import Path

from .model_a import PUBLIC_FIELDS,load_phase,mean,write_csv
from harness.artifacts import digest,read_json,write_json
from harness.bootstrap import complete_contrast,paired_bootstrap
from harness.freeze import verify_freeze
from harness.preflight import ROOT

CONDITIONS=('C','S')


def summarize(dataset,config):
    if dataset.get('role')!='B': raise ValueError('Model B requires its own phase dataset')
    records=dataset['records']
    identities=[(r['trajectory']['task_id'],r['trajectory']['condition']) for r in records]
    tasks=sorted({t for t,c in identities})
    if (len(records)!=32 or len(tasks)!=16 or len(set(identities))!=32
            or set(identities)!={(t,c) for t in tasks for c in CONDITIONS}):
        raise ValueError('Model B requires all 32 planned C/S terminal records')
    rows=[r['trajectory'] for r in records]
    if any(r['status'] not in ('completed','provider_failed') for r in rows): raise ValueError('Nonterminal Model B data')
    if any(t['claims'] is not None for r in records for t in r['turns']):
        raise ValueError('Model B C/S has no prompted self-assessment outcome')
    task_rows={t:{} for t in tasks}; utility={t:{} for t in tasks}; valid={t:{} for t in tasks}
    for row in rows:
        task,c=row['task_id'],row['condition']
        task_rows[task][c]=row['tcs_turn2'] if row['status']=='completed' else None
        utility[task][c]=row['end_to_end_utility_score']
        valid[task][c]=row['tcs_turn2'] if row['status']=='completed' and row['format_success_turn2'] else None
    conditions={}
    for c in CONDITIONS:
        selected=[r for r in rows if r['condition']==c]; done=[r for r in selected if r['status']=='completed']
        values={r['task_id']:r['tcs_turn2'] for r in done}
        conditions[c]={**paired_bootstrap(values,config['bootstrap']),'planned':16,'completed':len(done),
            'provider_failed':sum(r['status']=='provider_failed' for r in selected),
            'failures_by_type':dict(Counter(r['provider_failure_type'] for r in selected if r['status']=='provider_failed')),
            'turn1_mean':mean([r['tcs_turn1'] for r in selected if r['tcs_turn1'] is not None]),
            'turn1_evaluable':sum(r['tcs_turn1'] is not None for r in selected),
            'artifact_turn2_mean':mean([r['artifact_tcs_turn2'] for r in done]),
            'repair_gain_mean':mean([r['repair_gain'] for r in done]),
            'turn2_format_failures':sum(r['format_success_turn2'] is False for r in done),
            'turn2_format_evaluable':len(done)}
    spec=config['contrasts']['BaselineSafetyGap_B']
    if spec['role']!='B' or set(spec['weights'])!={'C','S'}: raise ValueError('Invalid frozen Model B contrast')
    values=complete_contrast(task_rows,spec['weights'])
    gap={**paired_bootstrap(values,config['bootstrap']),'task_values':values,
         'matched_condition_means':{c:mean([task_rows[t][c] for t in values]) for c in spec['weights']},
         'utility_sensitivity':paired_bootstrap(complete_contrast(utility,spec['weights']),config['bootstrap']),
         'valid_format_sensitivity':paired_bootstrap(complete_contrast(valid,spec['weights']),config['bootstrap'])}
    attempts=[a for r in records for a in r.get('attempts',[])]
    costs=dict(known_reported_cost=sum(a['reported_cost'] for a in attempts if a['reported_cost'] is not None),
        known_token_estimated_cost=sum(a['estimated_cost'] for a in attempts if a['estimated_cost'] is not None),
        outcomes_with_unknown_usage=sum(a['estimated_cost'] is None for a in attempts),
        attempts=len(attempts),retries=sum(r['retry_count'] or 0 for r in rows))
    return dict(schema_version=1,role='B',planned=32,terminal=32,task_count=16,
        freeze_hash=dataset['freeze_hash'],dataset_hash=digest(dataset),analysis_config_hash=digest(config),
        conditions=conditions,contrasts={'BaselineSafetyGap_B':gap},task_outcomes=task_rows,costs=costs,
        no_pooled_model_effect=True,self_assessment='Not requested in the frozen B C/S design; not scored.')


def comparison(a,b):
    if (a['role']!='A' or b['role']!='B' or a['freeze_hash']!=b['freeze_hash']
            or a['analysis_config_hash']!=b['analysis_config_hash']
            or set(a['task_outcomes'])!=set(b['task_outcomes'])):
        raise ValueError('Models must refer to the same frozen study and task set')
    def entry(summary,name):
        result=summary['contrasts'][name]
        return {key:result[key] for key in ('tasks','estimate','lower','upper','task_values','matched_condition_means')}
    return dict(schema_version=1,freeze_hash=b['freeze_hash'],analysis_config_hash=b['analysis_config_hash'],
                models={'A':entry(a,'BaselineSafetyGap_A'),'B':entry(b,'BaselineSafetyGap_B')},
                pooled_estimate=None,interpretation='Separate fixed-system estimates, not a universal model-population effect.')


def tables(dataset,summary,compare,output):
    write_csv(output/'model_b_trajectories.csv',PUBLIC_FIELDS,[r['trajectory'] for r in dataset['records']])
    write_csv(output/'model_b_conditions.csv',
        ['condition','planned','completed','provider_failed','mean_tcs_turn2','lower','upper','mean_tcs_turn1','turn1_evaluable','repair_gain','format_failures'],
        [dict(condition=c,planned=v['planned'],completed=v['completed'],provider_failed=v['provider_failed'],
              mean_tcs_turn2=v['estimate'],lower=v['lower'],upper=v['upper'],mean_tcs_turn1=v['turn1_mean'],turn1_evaluable=v['turn1_evaluable'],
              repair_gain=v['repair_gain_mean'],format_failures=v['turn2_format_failures']) for c,v in summary['conditions'].items()])
    v=summary['contrasts']['BaselineSafetyGap_B']
    write_csv(output/'model_b_contrasts.csv',['contrast','paired_tasks','estimate','lower','upper','utility_estimate','valid_format_estimate'],
        [dict(contrast='BaselineSafetyGap_B',paired_tasks=v['tasks'],estimate=v['estimate'],lower=v['lower'],upper=v['upper'],
              utility_estimate=v['utility_sensitivity']['estimate'],valid_format_estimate=v['valid_format_sensitivity']['estimate'])])
    write_csv(output/'model_b_task_differences.csv',['task_id','C','S','C_minus_S'],
        [dict(task_id=t,**values,C_minus_S=v['task_values'].get(t)) for t,values in summary['task_outcomes'].items()])
    write_csv(output/'models_comparison.csv',['model_role','paired_tasks','estimate','lower','upper','matched_C','matched_S'],
        [dict(model_role=role,paired_tasks=v['tasks'],estimate=v['estimate'],lower=v['lower'],upper=v['upper'],
              matched_C=v['matched_condition_means']['C'],matched_S=v['matched_condition_means']['S'])
         for role,v in compare['models'].items()])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'report/model_b')
    args=parser.parse_args()
    dataset=read_json(args.dataset) if args.dataset else load_phase(role='B')
    manifest=verify_freeze(); config=read_json(ROOT/'config/analysis.json')
    if dataset['freeze_hash']!=digest(manifest) or dataset['analysis_config_hash']!=digest(config):
        raise ValueError('Dataset belongs to a different freeze or analysis policy')
    # Require the exact reviewed A summary, not an opportunistically recomputed
    # model-A result or a pooled fit selected after inspecting B.
    a_path=ROOT/'report/model_a/summary.json'
    a_proof=read_json(ROOT/'report/model_a/integrity.json')
    if digest(a_path.read_text(encoding='utf-8'))!=a_proof['normalized_text_digests']['summary.json']:
        raise ValueError('Published Model A summary changed')
    summary=summarize(dataset,config)
    compare=comparison(read_json(a_path),summary)
    summary['requested_model_id']=manifest['models']['B']['model_id']
    for role,entry in compare['models'].items():
        entry['requested_model_id']=manifest['models'][role]['model_id']
    args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/'scored_dataset.json',dataset)
    write_json(args.output/'summary.json',summary)
    write_json(args.output/'models_comparison.json',compare)
    tables(dataset,summary,compare,args.output)
    from .model_b_figures import figures,report_text
    figures(summary,compare,args.output)
    (args.output/'results.md').write_text(report_text(summary,compare),encoding='utf-8',newline='\n')
    print(f'Model B: 32 terminal records audited; independent estimate, tables, figures, and comparison saved to {args.output}')


if __name__=='__main__':
    main()
