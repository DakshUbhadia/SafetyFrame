"""Scientific regression tests for recomputation, missingness and plotting inputs."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from analysis.bootstrap import estimate
from analysis.figures import figure_data
from analysis.primary import compute, rederive
from analysis.repair import summarize as repair
from analysis.self_assessment import summarize as self_assessment
from analysis.tests.test_model_a import fixture as fixture_a
from harness.artifacts import read_json
from harness.preflight import ROOT
from harness.scoring import assess
from scripts.finish_analysis import FILES, compare


def fixture(role='A'):
    data = fixture_a(); data['role'] = role
    if role == 'B':
        data['records'] = [r for r in data['records'] if r['trajectory']['condition'] in ('C', 'S')]
    for r in data['records']:
        row = r['trajectory']
        row.update(requirements_total=5, primary_analysis_included=True)
        if role == 'B': row['run_id'] = row['run_id'].replace('main-A', 'main-B')
        for number, turn in enumerate(r['turns'], 1):
            passed = sum(turn['requirements'].values())
            turn.update(tcs=row[f'tcs_turn{number}'], artifact_tcs=row[f'artifact_tcs_turn{number}'],
                        format_success=True, requirements_passed=passed)
            row[f'requirements_passed_turn{number}'] = passed
    return data


def fail_second(record):
    row = record['trajectory']
    row.update(status='provider_failed', provider_failure_type='5xx', primary_analysis_included=False,
               end_to_end_utility_score=0, repair_gain=None)
    for key in ('tcs', 'artifact_tcs', 'format_success', 'requirements_passed'):
        row[f'{key}_turn2'] = None
    record['turns'] = record['turns'][:1]


class FinalAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(ROOT / 'config/analysis.json')
        self.config['bootstrap']['resamples'] = 101  # Synthetic checks, not study estimates.

    def test_recompute_preserves_inputs_and_rejects_inconsistent_scores_counts_claims(self):
        original = fixture(); saved = deepcopy(original)
        self.assertEqual(rederive(original), saved)
        self.assertEqual(original, saved)
        for kind in ('score', 'count', 'format', 'assessment', 'repair', 'missing_turn', 'claims'):
            data = fixture(); r = data['records'][2]
            if kind == 'score': r['trajectory']['tcs_turn2'] = 0
            elif kind == 'count': r['turns'][1]['requirements_passed'] = 0
            elif kind == 'format': r['turns'][1]['format_success'] = False
            elif kind == 'assessment': r['turns'][1]['assessment']['failed_acknowledged'] = 99
            elif kind == 'repair': r['trajectory']['repair_gain'] = 1
            elif kind == 'missing_turn': r['turns'].pop()
            else: r['turns'][1]['claims']['R1'] = 'unknown'
            with self.subTest(kind=kind), self.assertRaises(ValueError): rederive(data)

    def test_provider_failed_second_turn_keeps_first_turn_but_no_second_score(self):
        data = fixture('B'); fail_second(data['records'][1])
        result = rederive(data)
        self.assertEqual(result['records'][1]['trajectory']['tcs_turn1'], .6)
        self.assertIsNone(result['records'][1]['trajectory']['tcs_turn2'])
        data['records'][1]['trajectory']['tcs_turn2'] = 0
        with self.assertRaises(ValueError): rederive(data)

    def test_paired_task_bootstrap_cancels_common_task_variation(self):
        tasks = {'a': {'C': .9, 'S': .7}, 'b': {'C': .3, 'S': .1}, 'missing': {'C': 1, 'S': None}}
        result = estimate(tasks, {'C': 1, 'S': -1}, self.config['bootstrap'])
        self.assertEqual(result['tasks'], 2)
        for key in ('estimate', 'lower', 'upper'): self.assertAlmostEqual(result[key], .2)
        self.assertEqual(set(result['task_values']), {'a', 'b'})
        self.assertEqual(result, estimate(dict(reversed(list(tasks.items()))), {'C': 1, 'S': -1}, self.config['bootstrap']))

    def test_empty_and_singleton_contrasts_have_no_interval(self):
        for matrix, count, point in [({}, 0, None), ({'x': {'C': .6, 'S': .2}}, 1, .4)]:
            result = estimate(matrix, {'C': 1, 'S': -1}, self.config['bootstrap'])
            self.assertEqual(result['tasks'], count)
            if point is None: self.assertIsNone(result['estimate'])
            else: self.assertAlmostEqual(result['estimate'], point)
            self.assertIsNone(result['lower']); self.assertIsNone(result['upper'])

    def test_claim_metrics_distinguish_micro_macro_uncertain_missing_and_na(self):
        data = fixture()
        for r in data['records']:
            if r['trajectory']['condition'] == 'CD':
                r['turns'] = []
        selected = [r for r in data['records'] if r['trajectory']['condition'] == 'CD'][:2]
        for r, requirements, claims in [
                (selected[0], {'R1':False}, {'R1':'not_fully_implemented'}),
                (selected[1], {'R1':False,'R2':False,'R3':False}, {'R1':'uncertain','R2':'missing','R3':'implemented'})]:
            r['turns'] = [dict(requirements=requirements, claims=claims, claim_issues=[])]
        rows = {r['metric']:r for r in self_assessment(data) if r['condition']=='CD' and r['turn']==1}
        self.assertEqual(rows['urdr_strict']['numerator'],1)
        self.assertEqual(rows['urdr_strict']['denominator'],4)
        self.assertEqual(rows['urdr_strict']['micro'],.25)
        self.assertEqual(rows['urdr_strict']['macro'],.5)
        self.assertEqual(rows['urdr_lenient']['micro'],.5)
        self.assertEqual(rows['false_completion_rate']['micro'],.25)
        self.assertEqual(rows['completion_precision']['defined_tasks'],1)
        no_claims = fixture()
        for r in no_claims['records']:
            if r['trajectory']['condition']=='CD':
                for turn in r['turns']: turn['claims']={key:'missing' for key in turn['requirements']}
        row=next(r for r in self_assessment(no_claims) if r['condition']=='CD' and r['turn']==2 and r['metric']=='completion_precision')
        self.assertIsNone(row['micro']); self.assertEqual(row['denominator'],0)
        self.assertIsNone(row['macro']); self.assertEqual(row['defined_tasks'],0)
        self.assertEqual(self_assessment(fixture('B')), [])

    def test_repair_uses_completed_pairs_with_observed_first_turn_reported_separately(self):
        data=fixture('B'); fail_second(data['records'][1])
        data['records'][1]['turns'][0]['tcs']=0
        rows={r['condition']:r for r in repair(data)}
        self.assertEqual(rows['S']['observed_turn1'],16)
        self.assertEqual(rows['S']['completed_pairs'],15)
        self.assertAlmostEqual(rows['S']['turn1_mean_all_observed'],.5625)
        self.assertAlmostEqual(rows['S']['turn1_mean_completed'],.6)
        self.assertEqual(rows['S']['mean_repair_gain'],0)

    def test_combined_analysis_preserves_contrast_specific_missingness_and_format(self):
        a=fixture(); b=fixture('B')
        fail_second(a['records'][3]); fail_second(b['records'][1])
        r=a['records'][7]; r['turns'][1].update(format_success=False,tcs=0)
        r['trajectory'].update(format_success_turn2=False,tcs_turn2=0,repair_gain=-.8,end_to_end_utility_score=0)
        result=compute({'A':rederive(a),'B':rederive(b)},self.config)
        select=lambda name,kind: next(r for r in result['contrasts'] if r['contrast']==name and r['estimand']==kind)
        self.assertEqual(select('BaselineSafetyGap_A','primary')['tasks'],16)
        self.assertEqual(select('DisclosureFramingInteraction_A','primary')['tasks'],15)
        self.assertEqual(select('DisclosureFramingInteraction_A','provider_utility')['tasks'],16)
        self.assertEqual(select('DisclosureFramingInteraction_A','valid_format')['tasks'],14)
        self.assertEqual(select('BaselineSafetyGap_B','primary')['tasks'],15)
        self.assertIsNone(result['pooled_estimate'])
        self.assertEqual(sum(r['terminal_provider_failures_at_turn'] for r in result['failures']),2)
        self.assertEqual(sum(r['format_failures'] for r in result['failures']),1)
        self.assertEqual(sum(r['harness_unresolved'] for r in result['conditions']),0)

    def test_every_plotting_value_is_selected_from_exported_tables(self):
        result=compute({'A':fixture(),'B':fixture('B')},self.config)
        plotted=figure_data(result)
        for figure,table in [('figure_1','conditions'),('figure_2','task_contrasts'),('figure_3','contrasts'),
                             ('figure_4','self_assessment'),('figure_5','repair')]:
            self.assertTrue(all(row in result[table] for row in plotted[figure]))
        self.assertEqual(len(plotted['figure_2']),32)
        undefined=[r for r in plotted['figure_4'] if r['metric']=='completion_precision']
        self.assertEqual(len(undefined),2)
        plotted['figure_1'][0]['mean']=-1
        self.assertNotEqual(result['conditions'][0]['mean'],-1)

    def test_reproduction_requires_all_ten_outputs_and_detects_numeric_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a'; b=Path(tmp)/'b'; a.mkdir(); b.mkdir()
            for name in FILES:
                (a/name).write_text('same\n',encoding='utf-8'); (b/name).write_text('same\n',encoding='utf-8')
            self.assertEqual(len(compare(a,b)),10)
            (b/'contrasts.csv').write_text('different\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'contrasts.csv'): compare(a,b)


if __name__=='__main__':
    unittest.main()
