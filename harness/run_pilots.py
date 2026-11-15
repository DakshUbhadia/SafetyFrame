"""Prepare, run, and summarize excluded capability-only primary-model calibration."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
from uuid import uuid4

from .artifacts import digest, read_json, safe_name, write_json
from .audit_equivalence import audit_pair
from .budget import BudgetLedger
from .pilot_catalog import PILOTS
from .preflight import ROOT, budget_projection, load_env, validate_config
from .providers.adaption import AdaptionProvider
from .render_variants import render_pair
from .run_experiment import run_trajectory
from .run_tests import TestRunner
from .task_bundle import TaskBundle


def default_task_ids(mode):
    tasks=[item['id'] for item in PILOTS]
    if mode=='run':
        plan=read_json(ROOT/'config/pilot_plan.json')
        rejected=set(plan.get('stress_trial_task_ids',[]))
        tasks=[task for task in tasks if task not in rejected]
    return tasks


def prepare(task_ids, image, output):
    records={}
    for task_id in task_ids:
        print('Preparing '+task_id,flush=True)
        template=ROOT/'task_templates'/task_id
        pair=render_pair(template)
        report=audit_pair(template,pair['C'],pair['S'],True,TestRunner('docker',image))
        audit_path=ROOT/'data'/'audits'/'pilots'/(task_id+'-'+uuid4().hex[:10]+'.json')
        write_json(audit_path,report,immutable=True)
        if not report['sprint3_exit_criteria_met']:
            raise ValueError('Pilot failed reference/equivalence/balance validation: '+task_id)
        records[task_id]={'task_hash':TaskBundle.load(pair['C']).hashes()['task_hash'],
                          'audit_path':str(audit_path),'image_id':report['reference_validation']['image_id'],'excluded_from_final':True}
    output.mkdir(parents=True,exist_ok=True)
    prior=read_json(output/'preparation.json') if (output/'preparation.json').exists() else {}
    write_json(output/'preparation.json',{**prior,**records})
    return records


def summarize(output, campaign, task_ids):
    profiles={item['id']:item['profile'] for item in PILOTS}
    rows=[]
    for task_id in task_ids:
        path=output/'scored'/f'{campaign}-{task_id}.json'
        if not path.exists():
            rows.append({'task_id':task_id,'profile':profiles[task_id],'status':'not_run'})
            continue
        record=read_json(path)
        row=record['trajectory']
        if row['phase']!='pilot' or row['condition']!='C' or row['primary_analysis_included']:
            raise ValueError('Calibration summary accepts only excluded capability pilots')
        rows.append({key:row[key] for key in ('task_id','status','model_id','tcs_turn1','tcs_turn2','repair_gain',
                    'format_success_turn1','format_success_turn2','input_tokens','output_tokens','latency_seconds',
                    'reported_cost','estimated_cost','cost_accounting_complete','provider_failure_type','retry_count')} |
                    {'profile':profiles[task_id],'failed_requirements_turn2':[rid for rid,passed in record['turns'][1]['requirements'].items() if not passed] if len(record['turns'])==2 else None})
    completed=[row for row in rows if row['status']=='completed']
    eligible=[row for row in completed if row['format_success_turn1'] and row['format_success_turn2']]
    partial=[row['task_id'] for row in eligible if .45<=row['tcs_turn2']<=.85]
    return {'campaign':campaign,'checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'conditions':['C'],'model_role':'A','all_excluded_from_final':True,'task_ids':task_ids,'rows':rows,
            'completed':len(completed),'expected':len(task_ids),
            'mean_tcs_turn1':mean(row['tcs_turn1'] for row in completed) if completed else None,
            'mean_tcs_turn2':mean(row['tcs_turn2'] for row in completed) if completed else None,
            'format_failure_turns':sum(not row[key] for row in completed for key in ('format_success_turn1','format_success_turn2')),
            'final_full_successes':sum(row['tcs_turn2']==1 for row in eligible),
            'observed_headroom_profiles':partial,
            'headroom_observed':bool(partial),
            'estimated_known_cost':sum(row['estimated_cost'] for row in completed if row['estimated_cost'] is not None),
            'reported_known_cost':sum(row['reported_cost'] for row in completed if row['reported_cost'] is not None),
            'cost_accounting_complete':bool(completed) and len(completed)==len(rows) and all(row['cost_accounting_complete'] for row in completed),
            'interpretation':'Descriptive pilot calibration only; no framing effects, confidence intervals, or final-study inference.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--run',action='store_true')
    mode.add_argument('--summarize',action='store_true')
    parser.add_argument('--task-ids',nargs='+')
    parser.add_argument('--campaign',default='sprint4-v1')
    parser.add_argument('--output',type=Path,default=ROOT/'data'/'pilot')
    parser.add_argument('--image',default='python:3.13-slim')
    args=parser.parse_args()
    if args.task_ids is None:
        args.task_ids=default_task_ids('run' if args.run else 'prepare' if args.prepare else 'summarize')
    try:
        safe_name(args.campaign)
        known={item['id'] for item in PILOTS}
        if len(args.task_ids)!=len(set(args.task_ids)) or not set(args.task_ids)<=known:
            raise ValueError('Unknown or duplicate pilot IDs')
        if args.prepare:
            prepare(args.task_ids,args.image,args.output)
            return 0
        if args.run:
            load_env(ROOT/'.env')
            config=read_json(ROOT/'config'/'study.json'); validate_config(config)
            if budget_projection(config)['status']!='estimated_fit': raise ValueError('Study cost projection does not fit')
            preparation=read_json(args.output/'preparation.json')
            runner=TestRunner('docker',args.image); runner.verify()
            model=config['models']['A']
            provider=AdaptionProvider(config['providers'][model['provider']])
            ledger=BudgetLedger(ROOT/'data'/'usage_ledger.json',config,spend_ceiling=config['budget']['pilot_allowance'])
            for order,task_id in enumerate(args.task_ids,1):
                task=TaskBundle.load(ROOT/'rendered_tasks'/(task_id+'_C'))
                if task.metadata['kind']!='pilot' or task.hashes()['task_hash']!=preparation[task_id]['task_hash']:
                    raise ValueError('Pilot changed after reference validation')
                if runner.image_id!=preparation[task_id].get('image_id'):
                    raise ValueError('Docker image changed after reference validation')
                print('Running capability pilot '+task_id+' using '+model['model_id'],flush=True)
                result=run_trajectory(task,'C',config,'A',provider,runner,args.output,
                                      args.campaign+'-'+task_id,'pilot-'+task_id,1,ledger)
                row=result['trajectory']
                print(f"{task_id}: {row['status']}; TCS {row['tcs_turn1']} -> {row['tcs_turn2']}; estimated credits {row['estimated_cost']}",flush=True)
                write_json(args.output/(args.campaign+'-summary.json'),summarize(args.output,args.campaign,args.task_ids))
                if row['status']!='completed': raise RuntimeError('Stop on provider failure; reconcile before continuing')
        summary=summarize(args.output,args.campaign,args.task_ids)
        path=args.output/(args.campaign+'-summary.json'); write_json(path,summary)
        print(f"Completed {summary['completed']}/{summary['expected']}; headroom observed: {summary['headroom_observed']}; summary: {path}")
        return 0 if summary['completed']==summary['expected'] else 1
    except (ValueError,KeyError,OSError,RuntimeError) as exc:
        print(f'Pilot work stopped ({type(exc).__name__}): {exc}',flush=True)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
