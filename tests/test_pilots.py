import copy
import json
from pathlib import Path
import tempfile
import unittest
import io
from unittest.mock import patch

from harness.artifacts import read_json,tree_hash,write_json
from harness.build_pilots import build_pilots
from harness.budget import BudgetLedger
from harness.pilot_catalog import PILOTS
from harness.preflight import ROOT,validate_config
from harness.render_variants import CanonicalTask
from harness.run_pilots import default_task_ids,summarize
from harness.run_tests import TestRunner
from harness.providers.adaption import AdaptionProvider,ProviderFailure,read_event_stream
import os


class PilotTests(unittest.TestCase):
    def test_fresh_tasks_are_disposable_and_span_requested_profiles(self):
        self.assertTrue(4<=len(PILOTS)<=6)
        self.assertEqual(len({d['id'] for d in PILOTS}),len(PILOTS))
        self.assertTrue(any(len(d['files'])==2 for d in PILOTS))
        self.assertTrue(any(len(d['requirements'])==4 for d in PILOTS))
        self.assertTrue(any(len(d['requirements'])==5 for d in PILOTS))
        with tempfile.TemporaryDirectory() as directory:
            tasks=build_pilots(directory)
            before={r['task_id']:tree_hash(r['template']) for r in tasks}
            self.assertEqual(before,{r['task_id']:tree_hash(r['template']) for r in build_pilots(directory)})
            for row in tasks:
                source=CanonicalTask.load(row['template'])
                self.assertEqual(source.metadata['kind'],'pilot')
                self.assertFalse(source.metadata['final_included'])
                self.assertNotIn(source.metadata['task_id'],{'synthetic_smoke','synthetic_domain_utils'})

    def test_coding_timeout_can_be_longer_than_preflight_without_unbounded_requests(self):
        config=read_json(ROOT/'config/study.json')
        config['providers']['adaption']['timeout_seconds']=180
        validate_config(config)
        config['providers']['adaption']['timeout_seconds']=301
        with self.assertRaises(ValueError): validate_config(config)

    def test_pilot_allowance_guards_generation_separately_from_account_balance(self):
        config=read_json(ROOT/'config/study.json')
        with tempfile.TemporaryDirectory() as directory:
            ledger=BudgetLedger(Path(directory)/'ledger.json',config,spend_ceiling=0)
            with self.assertRaises(RuntimeError): ledger.reserve('paid',[],config['models']['A'])

    def test_candidate_import_failure_is_not_harness_collection_error(self):
        from harness.run_tests import FIXTURE
        result={'total':1,'passed':0,'failures':[{'test':'test_public','message':'SyntaxError in solution'}],
                'collection_failed':True,'successful':False}
        runner=TestRunner('docker'); runner.image_id='sha256:test'
        with patch('harness.run_tests.bounded_process',return_value=(0,json.dumps(result),False,False)),patch('harness.run_tests.subprocess.run'):
            scored=runner.check(FIXTURE/'starter',FIXTURE/'public_tests',[],3)
        self.assertEqual(scored['total'],3)
        self.assertEqual(scored['passed'],0)
        self.assertTrue(scored['collection_failure'])

    def test_summary_is_descriptive_and_refuses_final_or_framing_data(self):
        task=PILOTS[0]['id']; campaign='test'
        row={'task_id':task,'phase':'pilot','condition':'C','primary_analysis_included':False,
             'status':'completed','model_id':'test-model','tcs_turn1':.5,'tcs_turn2':.75,'repair_gain':.25,
             'format_success_turn1':True,'format_success_turn2':True,'input_tokens':100,'output_tokens':100,
             'latency_seconds':2,'reported_cost':.01,'estimated_cost':.01,'cost_accounting_complete':True,
             'provider_failure_type':'none','retry_count':0}
        record={'trajectory':row,'turns':[{'requirements':{'R1':True}},{'requirements':{'R1':False}}]}
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory); path=output/'scored'/f'{campaign}-{task}.json'
            write_json(path,record)
            summary=summarize(output,campaign,[task])
            self.assertTrue(summary['headroom_observed'])
            self.assertEqual(summary['observed_headroom_profiles'],[task])
            self.assertEqual(summary['rows'][0]['failed_requirements_turn2'],['R1'])
            self.assertEqual(summary['conditions'],['C'])
            row['condition']='S'; write_json(path,record)
            with self.assertRaises(ValueError): summarize(output,campaign,[task])

    def test_stream_requires_terminal_response_and_preserves_usage(self):
        raw={'model':'test-model','status':'completed','output_text':'complete code','usage':{'output_tokens':4}}
        events=[{'type':'response.output_text.delta','delta':'partial'}, {'type':'response.completed','response':raw}]
        stream=io.BytesIO((''.join('data: '+json.dumps(event)+'\n\n' for event in events)).encode())
        result,saved=read_event_stream(stream,10)
        self.assertEqual(result,raw); self.assertEqual(saved,events)
        with self.assertRaises(ProviderFailure):
            read_event_stream(io.BytesIO(b'data: {"type":"response.output_text.delta","delta":"partial"}\n\n'),10)

    def test_stream_accepts_only_explicit_backend_identity_and_keeps_events(self):
        config=read_json(ROOT/'config/study.json')
        config['providers']['adaption']['stream']=True
        model=config['models']['A']
        class Response(io.BytesIO):
            headers={'Content-Type':'text/event-stream','x-request-id':'stream-request'}
        for returned,allowed in [('qwen3.5-397b-a17b-nvfp4',True),('unapproved-model',False)]:
            raw={'model':returned,'status':'completed','output_text':'complete implementation','usage':{'output_tokens':1}}
            event={'type':'response.completed','response':raw}
            body=('data: '+json.dumps(event)+'\n\n').encode()
            with patch.dict(os.environ,{'ADAPTION_API_KEY':'fake-key'}),patch('harness.providers.adaption.build_opener') as opener:
                opener.return_value.open.return_value=Response(body)
                if allowed:
                    result=AdaptionProvider(config['providers']['adaption']).generate([],model)
                    self.assertEqual(result['raw'],raw)
                    self.assertEqual(result['raw_stream_events'],[event])
                else:
                    with self.assertRaises(ProviderFailure) as error:
                        AdaptionProvider(config['providers']['adaption']).generate([],model)
                    self.assertEqual(error.exception.kind,'model_mismatch')

    def test_rejected_stress_profile_is_not_repeated_by_default(self):
        self.assertEqual(len(default_task_ids('prepare')),6)
        self.assertEqual(len(default_task_ids('run')),5)
        self.assertNotIn('pilot_006_jsonpatch',default_task_ids('run'))


if __name__=='__main__': unittest.main()
