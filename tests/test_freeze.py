import copy
from collections import Counter
import csv
import io
import platform
import runpy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import warnings
from unittest.mock import Mock,patch

import yaml

from harness.artifacts import digest,read_json,write_json
from harness.bootstrap import complete_contrast,paired_bootstrap,quantile
from harness.build_blocks import build_rows,csv_text,schedule_text
from harness.design_sensitivity import sensitivity_rows
from harness.freeze import authorize_final,file_hash,frozen_files,planned_rows,validate_plan,verify_freeze
from harness.preflight import ROOT
from harness.run_frozen import FrozenProvider,enforce_order
from harness.budget import BudgetLedger
from harness.run_tests import TestRunner
from harness.task_bundle import TaskBundle
from harness.scoring import aggregate_assessments,assess


class ScheduleAndAnalysisTests(unittest.TestCase):
    def test_schedule_reproduces_complete_contiguous_blocks_and_distinct_seed_changes_order(self):
        config=read_json(ROOT/'config/study.json'); benchmark=read_json(ROOT/'config/benchmark.json')
        rows=build_rows(config,benchmark,2026111506)
        self.assertEqual(csv_text(rows),schedule_text())
        self.assertEqual(len(rows),96)
        self.assertEqual(len({r['run_id'] for r in rows}),96)
        self.assertEqual(Counter(r['role'] for r in rows),{'A':64,'B':32})
        self.assertEqual([r['role'] for r in rows],['A']*64+['B']*32)
        self.assertNotEqual(rows,build_rows(config,benchmark,2026111507))
        blocks={}
        for row in rows: blocks.setdefault(row['block_id'],[]).append(row)
        self.assertEqual(len(blocks),32)
        for block in blocks.values():
            self.assertEqual({r['condition'] for r in block},set(config['models'][block[0]['role']]['conditions']))
            orders=[r['execution_order'] for r in block]
            self.assertEqual(orders,list(range(orders[0],orders[0]+len(block))))
            self.assertEqual([r['within_block_order'] for r in block],list(range(1,len(block)+1)))
        self.assertTrue({r['task_id'] for r in rows}.isdisjoint(benchmark['excluded_task_ids']))

    def test_missingness_is_per_contrast_and_interaction_sign_is_prespecified(self):
        tasks={'a':dict(C=.8,S=.4,CD=1,SD=.5),'b':dict(C=.6,S=.4,CD=None,SD=.7)}
        baseline=complete_contrast(tasks,{'C':1,'S':-1})
        interaction=complete_contrast(tasks,{'SD':1,'S':-1,'CD':-1,'C':1})
        self.assertEqual(set(baseline),{'a','b'})
        self.assertEqual(set(interaction),{'a'})
        self.assertAlmostEqual(interaction['a'],-.1)

    def test_bootstrap_uses_tasks_is_reproducible_and_handles_empty_singleton(self):
        settings=read_json(ROOT/'config/analysis.json')['bootstrap']
        self.assertEqual(settings['resamples'],10000)
        self.assertEqual(paired_bootstrap({},settings),dict(tasks=0,estimate=None,lower=None,upper=None))
        self.assertIsNone(paired_bootstrap({'x':.2},settings)['lower'])
        result=paired_bootstrap({'a':.25,'b':.25},settings)
        self.assertEqual(result,dict(tasks=2,estimate=.25,lower=.25,upper=.25))
        self.assertEqual(paired_bootstrap({'b':1,'a':-1},settings),paired_bootstrap({'a':-1,'b':1},settings))
        self.assertEqual(quantile([0,10],.25),2.5)

    def test_micro_macro_missing_uncertain_and_zero_denominators(self):
        a=assess({'R1':False,'R2':False},{'R1':'not_fully_implemented','R2':'uncertain'})
        b=assess({'R1':False},{'R1':'missing'})
        result=aggregate_assessments([a,b])
        self.assertEqual(result['urdr_strict']['micro'],1/3)
        self.assertEqual(result['urdr_strict']['macro'],.25)
        self.assertEqual(result['urdr_lenient']['micro'],2/3)
        self.assertIsNone(result['completion_precision']['micro'])
        empty=aggregate_assessments([assess({'R1':True},{'R1':'implemented'})])
        self.assertIsNone(empty['urdr_strict']['micro'])
        self.assertEqual(empty['completion_precision']['micro'],1)

    def test_sensitivity_is_pre_outcome_assumption_table(self):
        rows=sensitivity_rows(read_json(ROOT/'config/analysis.json'))
        self.assertEqual(len(rows),12)
        self.assertEqual(rows[0],dict(tasks=16,assumed_paired_contrast_sd=.1,approximate_95pct_ci_half_width=.049))
        self.assertEqual(rows[3]['approximate_95pct_ci_half_width'],.196)

    def test_order_guard_rejects_skipping_unresolved_run_before_provider_construction(self):
        rows=list(csv.DictReader(io.StringIO(schedule_text())))
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError,'unresolved'):
                enforce_order(rows[1],rows,Path(temporary))
            enforce_order(rows[0],rows,Path(temporary))


class PacingTests(unittest.TestCase):
    def test_module_entry_point_uses_canonical_provider_class(self):
        with warnings.catch_warnings(),patch('harness.run_frozen.main',return_value=0) as entry:
            warnings.simplefilter('ignore',RuntimeWarning)
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_module('harness.run_frozen',run_name='__main__')
            self.assertEqual(stopped.exception.code,0)
            entry.assert_called_once_with()

    def test_pacing_persists_across_instances_and_reverifies_before_sending(self):
        config=read_json(ROOT/'config/study.json'); execution=read_json(ROOT/'config/execution.json')
        manifest={'test':'unchanged'}
        now=[1000.0]; sleeps=[]
        def sleep(seconds): sleeps.append(seconds); now[0]+=seconds
        with tempfile.TemporaryDirectory() as temporary,patch('harness.run_frozen.ROOT',Path(temporary)),patch('harness.run_frozen.verify_freeze',return_value=manifest):
            starts=[]
            for _ in range(3):
                provider=FrozenProvider(config,execution,manifest,'A',clock=lambda:now[0],sleep=sleep)
                provider.inner=Mock()
                provider.inner.generate.side_effect=lambda messages,model:starts.append(now[0])
                provider.generate([],config['models']['A'])
            self.assertEqual(starts,[1000,1060,1120])
            self.assertEqual(sum(sleeps),120)
            provider.inner.generate.reset_mock()
            with patch('harness.run_frozen.verify_freeze',return_value={'test':'changed'}):
                with self.assertRaises(ValueError): provider.generate([],config['models']['A'])
            provider.inner.generate.assert_not_called()


class FreezeIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory(prefix='safetyframe-freeze-test-')
        cls.root=Path(cls.temporary.name)
        # A real temporary Git checkpoint covers the actual artifact set. No
        # Docker execution, credentials, provider construction, or main outcomes.
        for name in frozen_files():
            target=cls.root/name; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
        def git(*args):
            result=subprocess.run(['git','-C',str(cls.root),*args],capture_output=True)
            if result.returncode: raise RuntimeError(result.stderr.decode())
            return result.stdout.decode().strip()
        cls.git=staticmethod(git)
        git('init','-q'); git('add','.')
        git('-c','user.name=Freeze Test','-c','user.email=test@example.invalid','commit','-qm','Fixture source')
        checkpoint=git('rev-parse','HEAD')
        config,analysis,execution=validate_plan(cls.root)
        benchmark=read_json(cls.root/'config/benchmark.json')
        cls.manifest=dict(schema_version=1,final_outcomes_observed=False,git_commit=checkpoint,
            files={name:file_hash(cls.root/name) for name in frozen_files(cls.root)},
            models=config['models'],configuration_hash=digest(config),analysis=analysis,
            executor=execution['executor'],schedule_seed=execution['schedule_seed'],
            task_ids=[t['task_id'] for t in benchmark['tasks']],task_count=16,
            tasks={t['task_id']:t['artifact_hashes'] for t in benchmark['tasks']},
            runtime={'python':platform.python_version(),'pyyaml':yaml.__version__})
        write_json(cls.root/'freeze_manifest.json',cls.manifest)
        git('add','freeze_manifest.json')
        git('-c','user.name=Freeze Test','-c','user.email=test@example.invalid','commit','-qm','Fixture manifest')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_committed_freeze_covers_runtime_and_all_actual_artifacts(self):
        self.assertEqual(verify_freeze(self.root)['task_count'],16)

    def test_task_prompt_analysis_and_schedule_tampering_fail_closed(self):
        for name in ('rendered_tasks/task_001_C/starter/performance_monitor.py',
                     'prompts/capability.txt','config/analysis.json','data/run_manifest.csv'):
            path=self.root/name; before=path.read_bytes()
            try:
                path.write_bytes(before+b'\n# changed\n')
                with self.assertRaisesRegex(ValueError,'artifact changed'):
                    verify_freeze(self.root)
            finally: path.write_bytes(before)

    def test_manifest_change_and_uncommitted_freeze_are_rejected(self):
        path=self.root/'freeze_manifest.json'; before=path.read_bytes()
        try:
            changed=copy.deepcopy(self.manifest); changed['extra']='uncommitted modification'
            write_json(path,changed)
            with self.assertRaisesRegex(ValueError,'committed version'): verify_freeze(self.root)
        finally: path.write_bytes(before)

    def test_normalized_hash_allows_line_endings_but_not_content_changes(self):
        path=self.root/'prompts/capability.txt'; before=path.read_bytes()
        try:
            expected=file_hash(path); path.write_bytes(before.replace(b'\n',b'\r\n'))
            self.assertEqual(file_hash(path),expected)
            verify_freeze(self.root)
        finally: path.write_bytes(before)

    def test_final_authorization_binds_schedule_task_provider_and_budget_without_inference(self):
        row=planned_rows(self.root)[0]
        config=read_json(self.root/'config/study.json')
        execution=read_json(self.root/'config/execution.json')
        task=TaskBundle.load(self.root/row['task_path'])
        provider=FrozenProvider(config,execution,self.manifest,row['role'])
        provider.inner=Mock()
        runner=TestRunner('docker',execution['executor']['image'],execution['executor']['timeout_seconds'])
        ledger=BudgetLedger(self.root/'data/usage_ledger.json',config,spend_ceiling=40)
        def authorize(output):
            return authorize_final(task,row['condition'],config,row['role'],provider,runner,output,
                                   row['run_id'],row['block_id'],int(row['within_block_order']),ledger)
        with patch('harness.freeze.ROOT',self.root),patch('harness.freeze.verify_freeze',return_value=self.manifest),patch('harness.run_frozen.ROOT',self.root):
            self.assertEqual(authorize(self.root/'data/main'),self.manifest)
            with self.assertRaises(ValueError): authorize(self.root/'data/alternate')
            ledger.spend_ceiling=2800
            with self.assertRaises(ValueError): authorize(self.root/'data/main')
        provider.inner.generate.assert_not_called()


if __name__=='__main__':
    unittest.main()
