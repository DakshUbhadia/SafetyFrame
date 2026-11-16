import copy
from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis.model_a import load_phase,summarize as summarize_a
from analysis.model_b import comparison,summarize,tables
from analysis.model_b_figures import report_text
from analysis.tests.test_model_a import fixture as fixture_a
from harness.artifacts import read_json,write_json
from harness.preflight import ROOT
from scripts.finish_model_b import NUMERICAL_FILES,compare_outputs,ready


def fixture():
    data=fixture_a()
    data['role']='B'
    data['records']=[r for r in data['records'] if r['trajectory']['condition'] in ('C','S')]
    for r in data['records']:
        r['trajectory']['run_id']=r['trajectory']['run_id'].replace('main-A-','main-B-')
        for index,turn in enumerate(r['turns'],1):
            turn['format_success']=r['trajectory'][f'format_success_turn{index}']
    return data


class ModelBTests(unittest.TestCase):
    def setUp(self):
        self.config=read_json(ROOT/'config/analysis.json')

    def test_independent_gap_and_matching_prespecified_task_bootstrap(self):
        result=summarize(fixture(),self.config)
        self.assertEqual(result['role'],'B')
        self.assertEqual(result['planned'],32)
        gap=result['contrasts']['BaselineSafetyGap_B']
        self.assertEqual(gap['tasks'],16)
        for key in ('estimate','lower','upper'): self.assertAlmostEqual(gap[key],.4)
        self.assertEqual(set(result['conditions']),{'C','S'})
        self.assertNotIn('self_assessment',result['contrasts'])
        self.assertTrue(result['no_pooled_model_effect'])

    def test_provider_failure_is_missing_in_primary_but_zero_in_utility(self):
        data=fixture()
        r=data['records'][1]
        r['trajectory'].update(status='provider_failed',tcs_turn2=None,repair_gain=None,
                               end_to_end_utility_score=0,provider_failure_type='5xx')
        r['turns']=r['turns'][:1]
        result=summarize(data,self.config); gap=result['contrasts']['BaselineSafetyGap_B']
        self.assertEqual(gap['tasks'],15)
        self.assertAlmostEqual(gap['estimate'],.4)
        self.assertEqual(gap['utility_sensitivity']['tasks'],16)
        self.assertAlmostEqual(gap['utility_sensitivity']['estimate'],.4375)
        self.assertEqual(result['conditions']['S']['provider_failed'],1)
        self.assertEqual(result['conditions']['S']['turn1_evaluable'],16)
        self.assertEqual(result['conditions']['S']['completed'],15)

    def test_format_failure_is_zero_primary_with_artifact_score_kept_separate(self):
        data=fixture()
        data['records'][0]['trajectory'].update(tcs_turn2=0,repair_gain=-1,
            end_to_end_utility_score=0,format_success_turn2=False)
        data['records'][0]['turns'][1]['format_success']=False
        result=summarize(data,self.config); gap=result['contrasts']['BaselineSafetyGap_B']
        self.assertEqual(gap['tasks'],16)
        self.assertEqual(gap['valid_format_sensitivity']['tasks'],15)
        self.assertEqual(result['conditions']['C']['artifact_turn2_mean'],1)
        self.assertEqual(result['conditions']['C']['turn2_format_failures'],1)

    def test_incomplete_duplicate_nonterminal_and_wrong_phase_data_are_rejected(self):
        for case in ('missing','duplicate','nonterminal','role','disclosure','claims'):
            data=fixture()
            if case=='missing': data['records'].pop()
            elif case=='duplicate': data['records'][0]=copy.deepcopy(data['records'][1])
            elif case=='nonterminal': data['records'][0]['trajectory']['status']='running'
            elif case=='role': data['role']='A'
            elif case=='disclosure': data['records'][0]['trajectory']['condition']='CD'
            else: data['records'][0]['turns'][0]['claims']={'R1':'implemented'}
            with self.subTest(case=case),self.assertRaises(ValueError): summarize(data,self.config)

    def test_shared_loader_checks_b_completion_without_reading_a_as_b(self):
        with tempfile.TemporaryDirectory() as temporary,patch('analysis.model_a.verify_freeze',return_value={}):
            with self.assertRaisesRegex(ValueError,'Model B is incomplete'):
                load_phase(Path(temporary),role='B')
        with self.assertRaisesRegex(ValueError,'Unknown'): load_phase(role='C')

    def test_comparison_preserves_separate_estimates_and_common_freeze(self):
        a=summarize_a(fixture_a(),self.config)
        b=summarize(fixture(),self.config)
        result=comparison(a,b)
        self.assertEqual(set(result['models']),{'A','B'})
        self.assertIsNone(result['pooled_estimate'])
        b['freeze_hash']='different'
        with self.assertRaises(ValueError): comparison(a,b)

    def test_released_tables_narrative_and_pair_counts(self):
        data=fixture(); b=summarize(data,self.config)
        compare=comparison(summarize_a(fixture_a(),self.config),b)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary); tables(data,b,compare,output)
            self.assertEqual(len((output/'model_b_trajectories.csv').read_text().splitlines()),33)
            self.assertEqual(len((output/'model_b_task_differences.csv').read_text().splitlines()),17)
            self.assertEqual(len((output/'models_comparison.csv').read_text().splitlines()),3)
        text=report_text(b,compare)
        self.assertIn('0.400',text)
        self.assertIn('not a universal pooled',text)


class ModelBFinalizerTests(unittest.TestCase):
    def test_wait_gate_and_operational_review_are_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaises(ValueError): ready(root)
            progress=root/'data/main/collector-B.json'
            write_json(progress,dict(status='running'))
            with self.assertRaises(ValueError): ready(root)
            (root/'data/main/.phase-collector.lock').touch()
            self.assertFalse(ready(root))
            write_json(progress,dict(status='operational_review_required'))
            with self.assertRaises(ValueError): ready(root)
            write_json(progress,dict(status='terminal',phase_total=32))
            self.assertTrue(ready(root))

    def test_reproduction_checks_comparison_and_all_b_tables(self):
        with tempfile.TemporaryDirectory() as temporary:
            a=Path(temporary)/'a'; b=Path(temporary)/'b'; a.mkdir(); b.mkdir()
            for name in NUMERICAL_FILES:
                (a/name).write_text('same\n'); (b/name).write_text('same\n')
            self.assertEqual(len(compare_outputs(a,b)),10)
            (b/'models_comparison.csv').write_text('different')
            with self.assertRaisesRegex(ValueError,'comparison'): compare_outputs(a,b)


if __name__=='__main__':
    unittest.main()
