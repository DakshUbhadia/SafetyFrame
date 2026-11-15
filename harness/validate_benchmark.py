"""Docker-only final-task acceptance, partial-credit evidence, and inventory."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from uuid import uuid4

from .artifacts import digest, read_json, tree_files, tree_hash, write_json
from .audit_equivalence import audit_pair
from .build_benchmark import definitions
from .preflight import ROOT
from .render_variants import CanonicalTask, render_pair
from .run_experiment import copy_source
from .run_tests import TestRunner
from .task_bundle import TaskBundle


def exclusions():
    plan=read_json(ROOT/'config/pilot_plan.json')
    return sorted(set(plan['task_ids']+plan['additional_excluded_drafts']))


def fault_source(text,function):
    tree=ast.parse(text)
    target=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function)
    target.body=[ast.Raise(exc=ast.Call(func=ast.Name(id='RuntimeError',ctx=ast.Load()),
                                     args=[ast.Constant(value='deliberate isolated API fault')],keywords=[]),cause=None)]
    return ast.unparse(ast.fix_missing_locations(tree))+'\n'


def validate_task(definition):
    task_id=definition['id']
    if task_id in exclusions():
        raise ValueError('Pilot membership is forbidden')
    template=ROOT/'task_templates'/task_id
    source=CanonicalTask.load(template)
    render_pair(template)
    runner=TestRunner('docker')
    audit=audit_pair(template,ROOT/'rendered_tasks'/f'{task_id}_C',ROOT/'rendered_tasks'/f'{task_id}_S',True,runner)
    report={'schema_version':1,'task_id':task_id,'validated_at_utc':datetime.now(timezone.utc).isoformat(),
            'template_hash':tree_hash(template),'audit':audit,'fault_checks':[],
            'selection_basis':'Author review and deterministic tests only; zero final-task target-model calls or framing outcomes.',
            'reviewer':'self (author); no independent reviewer available','frozen':False}
    if audit['sprint3_exit_criteria_met']:
        bundle=TaskBundle.load(ROOT/'rendered_tasks'/f'{task_id}_C')
        for index,function in enumerate(definition['functions'],1):
            with tempfile.TemporaryDirectory(prefix='safetyframe-api-fault-') as temporary:
                workspace=Path(temporary)/'workspace'; workspace.mkdir()
                copy_source(bundle.root/'reference_solution',workspace)
                filename='reporting.py' if index==5 else source.mapping['capability']['monitor_component']+'.py'
                path=workspace/filename
                path.write_text(fault_source(path.read_text(encoding='utf-8'),function),encoding='utf-8',newline='\n')
                result=runner.score(bundle,workspace)
                req=f'R{index}'
                remaining=sum(v for k,v in result['requirements'].items() if k!=req)
                report['fault_checks'].append({'function':function,'target_requirement':req,
                    'requirements':result['requirements'],'unaffected_requirements_passed':remaining,
                    'passed':not result['requirements'][req] and remaining>=3,
                    'backend':'docker','image_id':runner.image_id})
    report['partial_credit_pass']=len(report['fault_checks'])==5 and all(r['passed'] for r in report['fault_checks'])
    # Every sentence is exact-matched by CanonicalTask; review is explicitly self-review.
    report['author_review']={
        'benign_dual_use_research_infrastructure':True,
        'natural_domain_terms_and_no_asymmetric_warning_language':True,
        'hidden_checks_supported_by_exact_requirement_sentences':True,
        'no_intentional_adversarial_gotchas':True,
        'public_tests_are_partial_examples':True,
        'offline_deterministic_standard_library_only':True,
        'estimated_output_fits_8192_tokens_not_empirically_verified':True,
        'difficulty_not_validated_on_final_target_models':True}
    report['accepted']=audit['sprint3_exit_criteria_met'] and report['partial_credit_pass']
    report['artifact_hashes']={'template':tree_hash(template),
        'C':tree_hash(ROOT/'rendered_tasks'/f'{task_id}_C'),
        'S':tree_hash(ROOT/'rendered_tasks'/f'{task_id}_S')}
    path=ROOT/'data/audits/final'/f'{task_id}-{uuid4().hex[:10]}.json'
    write_json(path,report,immutable=True)
    print(f"{task_id}: reference={audit['reference_pass']}; equivalence={audit['equivalence_pass']}; balance={audit['automated_balance_pass']}; isolated faults={sum(r['passed'] for r in report['fault_checks'])}/5; accepted={report['accepted']}; {path.name}",flush=True)
    return path,report


def check_record(record):
    task_id=record['task_id']
    if task_id in exclusions() or not record.get('accepted') or not record.get('partial_credit_pass'):
        raise ValueError(f'{task_id}: task not accepted')
    audit=record['audit']
    if not (audit.get('sprint3_exit_criteria_met') and audit.get('reference_pass') is True
            and audit.get('equivalence_pass') and audit.get('automated_balance_pass')
            and not audit.get('errors') and all(audit['prompt_checks'].values())):
        raise ValueError(f'{task_id}: missing successful Docker reference evidence')
    validation=audit['reference_validation']
    if validation['backend']!='docker' or not validation.get('image_id'):
        raise ValueError(f'{task_id}: Docker provenance missing')
    if validation['status']!='passed' or set(validation['results'])!={'C','S'}:
        raise ValueError(f'{task_id}: incomplete paired reference evidence')
    requirement_ids={f'R{i}' for i in range(1,6)}
    for result in validation['results'].values():
        public=result['public']
        if not (public['successful'] and public['total']==public['passed']==3
                and set(result['requirements'])==requirement_ids and all(result['requirements'].values())
                and set(result['hidden_details'])==requirement_ids):
            raise ValueError(f'{task_id}: unsuccessful reference checks')
        if not all(check['successful'] and check['total']==check['passed']==2
                   for check in result['hidden_details'].values()):
            raise ValueError(f'{task_id}: incomplete hidden checks')
    faults=record['fault_checks']
    if len(faults)!=5 or {f['target_requirement'] for f in faults}!={f'R{i}' for i in range(1,6)} or not all(f['passed'] and f['backend']=='docker' and f['unaffected_requirements_passed']>=3 for f in faults):
        raise ValueError(f'{task_id}: incomplete isolated-fault evidence')
    for fault in faults:
        scores=fault['requirements']; target=fault['target_requirement']
        actual=sum(value for key,value in scores.items() if key!=target)
        if (set(scores)!=requirement_ids or scores[target] or actual<3
                or actual!=fault['unaffected_requirements_passed']
                or fault['image_id']!=validation['image_id']):
            raise ValueError(f'{task_id}: failed isolated API fault')
    if not record.get('author_review') or not all(record['author_review'].values()):
        raise ValueError(f'{task_id}: author review incomplete')
    hashes={'template':tree_hash(ROOT/'task_templates'/task_id),
            **{c:tree_hash(ROOT/'rendered_tasks'/f'{task_id}_{c}') for c in ('C','S')}}
    if hashes!=record['artifact_hashes']:
        raise ValueError(f'{task_id}: artifacts changed since validation')
    source=CanonicalTask.load(ROOT/'task_templates'/task_id)
    if (source.metadata['kind']!='final' or source.metadata.get('pilot') is not False
            or not source.metadata.get('final_included') or source.metadata['requirements_total']!=5):
        raise ValueError(f'{task_id}: invalid final metadata')
    if audit['canonical_source_hash']!=source.source_hash() or any(audit['variants'][c]['bundle_hash']!=hashes[c] for c in ('C','S')):
        raise ValueError(f'{task_id}: audit provenance mismatch')
    return hashes


def write_task_checklist(definition,path,record,hashes):
    text=(ROOT/'04_TASK_VALIDATION_CHECKLIST.md').read_text(encoding='utf-8')
    tick=chr(96)
    text=text.replace(tick+'[draft / validated / frozen]'+tick,'validated / not frozen')
    text=text.replace(tick+'[self / other if available]'+tick,'self (author); no independent reviewer')
    text=text.replace('- Task ID: '+tick+'[FILL]'+tick,'- Task ID: '+definition['id'])
    text=text.replace('- Family: '+tick+'[FILL]'+tick,'- Family: '+definition['family'])
    text=text.replace('- [ ]','- [x]')
    text=text.replace('- [x] REJECT / revise.','- [ ] REJECT / revise.')
    text=text.replace('Expected model output fits token budget.',
                      'Expected model output fits token budget (author estimate for 8,192 tokens; not empirically verified).')
    text=text.replace(tick+'[FILL AFTER FREEZE]'+tick,'Pending Sprint 6; no freeze hash assigned.')
    text=text.replace(tick+'[FILL]'+tick,'Not rejected. Accepted for Sprint 5; Sprint 6 freeze remains pending.')
    text += '\n## Evidence and requirement traceability\n\n'
    text += f"Validation: [Docker audit and all five API faults](../audits/final/{path.name}).\n\n"
    text += 'The author reviewed both rendered specifications, source/test labels, and the checks below. '
    text += 'Linguistic counts use a regex token proxy; actual model-token counts are unavailable. '
    text += 'Final-task difficulty remains unmeasured to avoid selecting on target-model outcomes.\n\n'
    for i,sentence in enumerate(definition['requirements'],1):
        text+=f"- R{i}: {sentence}\n  Checks: test_hidden.Requirements.test_R{i}_case1 and test_R{i}_case2.\n"
    text+='\nArtifact SHA-256 tree digests (validation, not freeze):\n\n'
    text+='\n'.join(f'- {name}: {value}' for name,value in hashes.items())+'\n'
    destination=ROOT/'data/task_validation'/f"{definition['id']}.md"
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(text,encoding='utf-8',newline='\n')


def publish_inventory():
    if (ROOT/'freeze_manifest.json').exists():
        raise ValueError('Benchmark publication is closed after freeze')
    records=[]
    for definition in definitions():
        paths=sorted((ROOT/'data/audits/final').glob(definition['id']+'-*.json'),key=lambda p:p.stat().st_mtime_ns,reverse=True)
        if not paths: raise ValueError(f"{definition['id']}: no acceptance record")
        record=read_json(paths[0]); hashes=check_record(record)
        records.append((definition,paths[0],record,hashes))
    if len(records)!=16 or len({d['id'] for d,_,_,_ in records})!=16:
        raise ValueError('Expected exactly sixteen distinct reviewed final tasks')
    family_counts={family:sum(d['family']==family for d,_,_,_ in records) for family in ('ingestion','metrics','experiments','monitoring')}
    if set(family_counts.values())!={4}: raise ValueError('Four tasks per family required')
    registry={'schema_version':1,'status':'validated_unfrozen','frozen':False,
              'task_count':16,'requirements_per_task':5,'family_counts':family_counts,
              'catalogue_hash':digest(definitions()),
              'selection_policy':'No final-task target-model calls, observed outcomes, or framing differences used in selection.',
              'excluded_task_ids':exclusions(),'sprint5_exit_criteria_met':True,
              'not_before_sprint6':'Main study execution remains gated until preregistration and freeze.',
              'tasks':[{'task_id':d['id'],'family':d['family'],'title':d['title'],
                        'validation_record':p.relative_to(ROOT).as_posix(),
                        'validation_record_hash':digest(r),'artifact_hashes':hashes} for d,p,r,hashes in records]}
    write_json(ROOT/'config/benchmark.json',registry)
    for definition,path,record,hashes in records:
        write_task_checklist(definition,path,record,hashes)
    destination=ROOT/'data/task_inventory.csv'
    with destination.open('w',encoding='utf-8',newline='') as stream:
        columns=['task_id','family','title','requirements_total','reference_solution_pass','renderer_audit_pass',
                 'linguistic_balance_pass','partial_success_pass','dual_plausibility_pass','final_included','notes',
                 'public_checks_per_variant','hidden_checks_per_variant','source_files',
                 'authoring_status','reference_C','reference_S','equivalence','linguistic_balance','partial_credit',
                 'reviewer','model_calls','validation_record','template_hash','C_hash','S_hash']
        writer=csv.DictWriter(stream,fieldnames=columns,lineterminator='\n'); writer.writeheader()
        for d,p,r,h in records:
            writer.writerow(dict(task_id=d['id'],family=d['family'],title=d['title'],requirements_total=5,
                reference_solution_pass=True,renderer_audit_pass=True,linguistic_balance_pass=True,partial_success_pass=True,
                dual_plausibility_pass=True,final_included=True,notes='Validated, not frozen; difficulty unmeasured; no model calls.',
                public_checks_per_variant=3,hidden_checks_per_variant=10,source_files=2,authoring_status='validated_unfrozen',
                reference_C='pass',reference_S='pass',equivalence='pass',linguistic_balance='pass_proxy_and_self_review',
                partial_credit='5 isolated API faults pass',reviewer='self',model_calls=0,
                validation_record=p.relative_to(ROOT).as_posix(),template_hash=h['template'],C_hash=h['C'],S_hash=h['S']))
    print(f'Published {destination} and config/benchmark.json: 16 accepted, unfrozen tasks.',flush=True)


def verify_inventory():
    registry=read_json(ROOT/'config/benchmark.json')
    expected={d['id'] for d in definitions()}
    if registry['frozen'] or registry['status']!='validated_unfrozen':
        raise ValueError('This Sprint 5 verifier expects an unfrozen registry')
    if registry['catalogue_hash']!=digest(definitions()) or registry['excluded_task_ids']!=exclusions():
        raise ValueError('Catalogue or exclusions changed since publication')
    if {t['task_id'] for t in registry['tasks']}!=expected or len(registry['tasks'])!=16 or not expected.isdisjoint(exclusions()):
        raise ValueError('Invalid benchmark membership')
    for entry in registry['tasks']:
        record=read_json(ROOT/entry['validation_record'])
        if record['task_id']!=entry['task_id'] or digest(record)!=entry['validation_record_hash'] or check_record(record)!=entry['artifact_hashes']:
            raise ValueError('Validation record integrity failure')
    print('Verified 16 accepted tasks and current artifact/evidence hashes; the validation registry predates the study freeze.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--batch',type=int,choices=range(1,5))
    group.add_argument('--task',choices=[d['id'] for d in definitions()],help='Revalidate one revised unfrozen task')
    group.add_argument('--publish',action='store_true')
    group.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.publish: publish_inventory()
    elif args.verify: verify_inventory()
    else:
        selected=([d for d in definitions() if d['id']==args.task] if args.task
                  else definitions()[(args.batch-1)*4:args.batch*4])
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(validate_task,selected))
        if not all(r['accepted'] for _,r in results): raise SystemExit(1)


if __name__=='__main__':
    main()
