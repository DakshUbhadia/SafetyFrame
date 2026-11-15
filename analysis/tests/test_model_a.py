import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis.model_a import load_phase,summarize,tables
from analysis.model_a_figures import report_text
from harness.artifacts import read_json
from harness.preflight import ROOT
from harness.scoring import assess


def fixture():
    records=[]
    for index in range(1,17):
        task=f'task_{index:03d}'
        for condition,score in [('C',1),('S',.6),('CD',.8),('SD',.8)]:
            requirements={f'R{i}':i<=round(score*5) for i in range(1,6)}
            claims=({r:'implemented' if passed else 'not_fully_implemented' for r,passed in requirements.items()}
                    if condition in ('CD','SD') else None)
            turn=dict(requirements=requirements,claims=claims,claim_issues=[],assessment=assess(requirements,claims))
            row=dict(run_id=f'main-A-{task}-{condition}',task_id=task,condition=condition,status='completed',
                tcs_turn1=score,tcs_turn2=score,artifact_tcs_turn1=score,artifact_tcs_turn2=score,
                format_success_turn1=True,format_success_turn2=True,repair_gain=0,
                provider_failure_type='none',retry_count=0,end_to_end_utility_score=score)
            records.append(dict(trajectory=row,turns=[copy.deepcopy(turn),copy.deepcopy(turn)],attempts=[]))
    return dict(records=records,freeze_hash='fixture')


class ModelAAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.config=read_json(ROOT/'config/analysis.json')

    def test_full_factorial_contrast_signs_and_task_bootstrap(self):
        summary=summarize(fixture(),self.config)
        for name,expected in [('BaselineSafetyGap_A',.4),('DisclosureEffect_C_A',-.2),
                              ('DisclosureEffect_S_A',.2),('DisclosureFramingInteraction_A',.4)]:
            estimate=summary['contrasts'][name]
            self.assertEqual(estimate['tasks'],16)
            self.assertAlmostEqual(estimate['estimate'],expected)
            self.assertAlmostEqual(estimate['lower'],expected)
            self.assertAlmostEqual(estimate['upper'],expected)
        self.assertTrue(summary['no_model_b_results'])
        self.assertEqual(summary['self_assessment']['SD']['2']['metrics']['urdr_strict']['micro'],1)

    def test_provider_missingness_is_per_contrast_and_utility_keeps_failed_task(self):
        data=fixture()
        row=next(r for r in data['records'] if r['trajectory']['task_id']=='task_001' and r['trajectory']['condition']=='SD')
        row['trajectory'].update(status='provider_failed',provider_failure_type='timeout',tcs_turn2=None,
                                 end_to_end_utility_score=0,repair_gain=None)
        row['turns']=row['turns'][:1]
        summary=summarize(data,self.config)
        self.assertEqual(summary['contrasts']['BaselineSafetyGap_A']['tasks'],16)
        self.assertEqual(summary['contrasts']['DisclosureFramingInteraction_A']['tasks'],15)
        self.assertEqual(summary['contrasts']['DisclosureFramingInteraction_A']['utility_sensitivity']['tasks'],16)
        self.assertEqual(summary['conditions']['SD']['provider_failed'],1)
        self.assertEqual(summary['self_assessment']['SD']['2']['evaluable_trajectories'],15)

    def test_format_failure_zero_is_retained_but_valid_format_sensitivity_is_paired(self):
        data=fixture()
        row=data['records'][1]['trajectory']
        row.update(tcs_turn2=0,format_success_turn2=False,repair_gain=-.6,end_to_end_utility_score=0)
        summary=summarize(data,self.config)
        self.assertEqual(summary['conditions']['S']['turn2_format_failures'],1)
        self.assertEqual(summary['contrasts']['BaselineSafetyGap_A']['tasks'],16)
        self.assertEqual(summary['contrasts']['BaselineSafetyGap_A']['valid_format_sensitivity']['tasks'],15)
        self.assertAlmostEqual(summary['conditions']['S']['artifact_turn2_mean'],.6)

    def test_missing_claims_and_undefined_precision_are_not_invented_as_zero(self):
        data=fixture()
        for record in data['records']:
            if record['trajectory']['condition']=='CD':
                for turn in record['turns']:
                    turn['claims']={r:'missing' for r in turn['requirements']}
        summary=summarize(data,self.config)
        values=summary['self_assessment']['CD']['2']
        self.assertEqual(values['counts']['claimed_missing'],80)
        self.assertEqual(values['metrics']['urdr_strict']['micro'],0)
        self.assertIsNone(values['metrics']['completion_precision']['micro'])

    def test_incomplete_duplicate_or_nonterminal_phase_is_rejected(self):
        for alteration in ('missing','duplicate','nonterminal'):
            data=fixture()
            if alteration=='missing': data['records'].pop()
            elif alteration=='duplicate': data['records'][0]=copy.deepcopy(data['records'][1])
            else: data['records'][0]['trajectory']['status']='running'
            with self.assertRaises(ValueError): summarize(data,self.config)
        with tempfile.TemporaryDirectory() as temporary:
            with patch('analysis.model_a.verify_freeze',return_value={}):
                with self.assertRaisesRegex(ValueError,'incomplete'):
                    load_phase(Path(temporary))

    def test_tables_and_narrative_preserve_counts_and_na(self):
        data=fixture(); result=summarize(data,self.config)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            tables(data,result,output)
            self.assertEqual(len((output/'model_a_task_differences.csv').read_text().splitlines()),17)
            self.assertEqual(len((output/'model_a_trajectories.csv').read_text().splitlines()),65)
        narrative=report_text(result)
        self.assertIn('Model B has not been analyzed',narrative)
        self.assertIn('16/16',narrative)
        self.assertIn('0.400',narrative)


if __name__=='__main__':
    unittest.main()
