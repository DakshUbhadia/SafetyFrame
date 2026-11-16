"""Study 2 protocol regression tests; no credentials, network or model-code execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from harness.audit_parser import parse_audit
from harness.confidence_parser import parse_confidence
from harness.evidence_parser import parse_evidence
from harness.audit_runner import messages_for, request_audit, smoke
from harness.audit_scoring import builder_rows
from harness.audit_study import ROOT, STUDY, inventory, schedule, verify_preservation
from harness.providers.adaption import ProviderFailure
from analysis.audit_metrics import audit_metrics
from analysis.calibration import calibration_metrics
from analysis.paired_comparisons import bootstrap, paired_comparison
from analysis.audit_analysis import evidence_review


def row(task='t1', artifact='a1', condition='fresh', claim='implemented', truth=0, rid='R1', probability=None):
    return dict(task_id=task, artifact_id=artifact, audit_condition=condition, auditor_model='model',
        builder_model='model', requirement_id=rid, auditor_claim=claim, ground_truth_pass=truth,
        probability_fully_satisfied=probability)


class ParserTests(unittest.TestCase):
    def test_categorical_normalization_and_unknown(self):
        parsed = parse_audit('<REQUIREMENTS_CHECK>\nr1: NOT  FULLY IMPLEMENTED\nR2: uncertain\nR99: implemented\n</REQUIREMENTS_CHECK>', ['R1', 'R2'])
        self.assertEqual(parsed['requirements']['R1']['status'], 'not fully implemented')
        self.assertEqual(parsed['unknown_ids'], ['R99'])
        self.assertEqual(parsed['parse_status'], 'valid')

    def test_no_prose_or_envelope_recovery(self):
        for text in ['R1: implemented', 'Explanation\n<requirements_check>R1: implemented</requirements_check>',
                     '<requirements_check>R1: implemented</requirements_check>\n<requirements_check>R1: uncertain</requirements_check>']:
            parsed = parse_audit(text, ['R1'])
            self.assertEqual(parsed['requirements']['R1']['status'], 'missing')
        parsed = parse_audit('<requirements_check>R1: seems implemented</requirements_check>', ['R1'])
        self.assertEqual(parsed['requirements']['R1']['status'], 'missing')

    def test_duplicate_and_missing(self):
        parsed = parse_audit('<requirements_check>\nR1: implemented\nR1: uncertain\n</requirements_check>', ['R1', 'R2'])
        self.assertEqual(parsed['requirements']['R1']['errors'], ['duplicate_requirement_id'])
        self.assertEqual(parsed['requirements']['R2']['status'], 'missing')

    def test_evidence_not_automatically_verified(self):
        parsed = parse_evidence('<requirements_audit>\nR1:\nstatus: uncertain\nevidence: module.py has no f\n</requirements_audit>', ['R1'])
        self.assertEqual(parsed['parse_status'], 'valid')
        self.assertEqual(parsed['requirements']['R1']['evidence_text'], 'module.py has no f')

    def test_confidence_strictness(self):
        for value in ('0', '20', '100', '-1', '101', '99.0', '90%', '+1', '01', 'NaN', 'true', ''):
            parsed = parse_confidence('<requirements_confidence>\nR1:\nstatus: implemented\nprobability_fully_satisfied: '+value+'\n</requirements_confidence>', ['R1'])
            self.assertEqual(parsed['requirements']['R1']['probability_fully_satisfied'],
                             int(value) if value in ('0', '20', '100') else None)

    def test_duplicate_confidence_not_coerced(self):
        parsed = parse_confidence('<requirements_confidence>\nR1:\nstatus: implemented\nprobability_fully_satisfied: 90\nprobability_fully_satisfied: 80\n</requirements_confidence>', ['R1'])
        self.assertIsNone(parsed['requirements']['R1']['probability_fully_satisfied'])
        self.assertEqual(parsed['requirements']['R1']['status'], 'implemented')


class MetricsTests(unittest.TestCase):
    def test_denominators_and_abstention(self):
        rows = [row(claim=s, truth=y) for s, y in [('implemented', 0), ('not fully implemented', 0),
            ('uncertain', 0), ('missing', 0), ('implemented', 1), ('not fully implemented', 1)]]
        metrics = audit_metrics(rows)
        self.assertEqual(metrics['FCR'], .25)
        self.assertEqual(metrics['strict_URDR'], .25)
        self.assertEqual(metrics['lenient_URDR'], .5)
        self.assertEqual(metrics['completion_precision'], .5)
        self.assertEqual(metrics['UDP'], .5)
        self.assertEqual(metrics['accuracy_on_non_abstained'], .5)
        self.assertEqual(metrics['missing_rate'], 1/6)

    def test_undefined_stays_na(self):
        metrics = audit_metrics([row(claim='uncertain', truth=1)])
        for metric in ('FCR', 'strict_URDR', 'UDP', 'completion_precision', 'accuracy_on_non_abstained', 'Brier'):
            self.assertIsNone(metrics[metric])

    def test_brier_auroc_and_bin_edges(self):
        rows = [row(truth=y, probability=p) for p, y in [(0, 0), (20, 0), (100, 1), (80, 1), (None, 1)]]
        metrics = calibration_metrics(rows)
        self.assertAlmostEqual(metrics['Brier'], .02)
        self.assertEqual(metrics['AUROC'], 1)
        self.assertEqual([b['n'] for b in metrics['calibration_bins']], [1, 1, 0, 0, 2])
        self.assertEqual(metrics['n_confidence'], 4)
        self.assertEqual(calibration_metrics([row(probability=90)])['AUROC'], None)

    def test_pairs_match_artifacts_before_tasks(self):
        rows = [row(artifact='a', condition='builder'), row(artifact='a', claim='not fully implemented'),
                row(artifact='unmatched', condition='builder'),
                row(task='t2', artifact='b', condition='builder'), row(task='t2', artifact='b')]
        effect = paired_comparison(rows, 'fresh', 'builder', 'FCR', 'model', seed=1, resamples=100)
        self.assertEqual(effect['n_matched_tasks'], 2)
        self.assertEqual(effect['n_matched_artifacts'], 2)
        self.assertEqual(effect['mean_difference'], -.5)
        self.assertEqual(effect['task_differences'], {'t1': -1, 't2': 0})
        self.assertEqual(effect, paired_comparison(rows, 'fresh', 'builder', 'FCR', 'model', seed=1, resamples=100))

    def test_task_weight_not_requirement_weight(self):
        rows = [row(task='small', artifact='a', condition='builder'),
                row(task='small', artifact='a', claim='not fully implemented')]
        for i in range(9):
            rows += [row(task='large', artifact='b', condition='builder', rid=f'R{i+1}'),
                     row(task='large', artifact='b', rid=f'R{i+1}')]
        self.assertEqual(paired_comparison(rows, 'builder', 'fresh', 'FCR', 'model', resamples=20)['mean_difference'], .5)
        self.assertIsNone(bootstrap([])['mean_difference'])


class RunnerTests(unittest.TestCase):
    def test_no_hidden_or_builder_data_in_messages(self):
        bundle = dict(specification='spec', requirements=[{'id': 'R1', 'text': 'public requirement'}],
                      files={'code.py': 'pass'}, public_tests={'test_public.py': 'pass'})
        messages = messages_for(bundle, 'neutral')
        self.assertEqual(json.loads(messages[1]['content'].split('\n', 1)[1]), bundle)
        with self.assertRaises(ValueError):
            messages_for(dict(bundle, hidden_scores={'R1': False}), 'neutral')
        bad = copy.deepcopy(bundle)
        bad['requirements'][0]['checks'] = ['hidden_selector']
        with self.assertRaises(ValueError):
            messages_for(bad, 'neutral')

    def test_retry_transport_only_and_resume(self):
        class Provider:
            calls = 0
            def generate(self, messages, model):
                self.calls += 1
                if self.calls == 1:
                    raise ProviderFailure('5xx', True)
                return {'text': 'malformed but provider-valid'}
        with tempfile.TemporaryDirectory() as temp, patch('harness.audit_runner.time.sleep'):
            provider = Provider()
            model = {'model_id': 'm', 'generation': {}}
            saved, path = request_audit(provider, model, [], temp)
            self.assertEqual(provider.calls, 2)
            self.assertEqual(saved['attempt'], 1)
            self.assertEqual(request_audit(provider, model, [], temp)[0], saved)
            self.assertEqual(provider.calls, 2)
            with self.assertRaises(RuntimeError):
                request_audit(provider, dict(model, model_id='other'), [], temp)

    def test_rejection_never_retried_even_if_marked_retryable(self):
        class Provider:
            calls = 0
            def generate(self, messages, model):
                self.calls += 1
                raise ProviderFailure('rate_limit', True)
        with tempfile.TemporaryDirectory() as temp:
            provider = Provider()
            request_audit(provider, {'model_id': 'm', 'generation': {}}, [], temp)
            self.assertEqual(provider.calls, 1)

    def test_ambiguous_request_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'attempt0-request.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'reconcile'):
                request_audit(None, {'model_id': 'm', 'generation': {}}, [], temp)

    def test_full_smoke(self):
        self.assertEqual(smoke()['model_calls'], 0)

    def test_retry_exhaustion_and_duplicate_requirement_confidence(self):
        class Provider:
            calls = 0
            def generate(self, messages, model):
                self.calls += 1
                raise ProviderFailure('timeout', True)
        with tempfile.TemporaryDirectory() as temp, patch('harness.audit_runner.time.sleep'):
            provider = Provider()
            result, path = request_audit(provider, {'model_id': 'm', 'generation': {}}, [], temp)
            self.assertEqual(provider.calls, 3)
            self.assertEqual(result['failure'], 'timeout')
        duplicate = parse_confidence('<requirements_confidence>\nR1:\nstatus: implemented\nprobability_fully_satisfied: 90\nR1:\nstatus: uncertain\nprobability_fully_satisfied: 40\n</requirements_confidence>', ['R1'])
        self.assertEqual(duplicate['requirements']['R1']['status'], 'missing')
        self.assertIsNone(duplicate['requirements']['R1']['probability_fully_satisfied'])


class RepositoryTests(unittest.TestCase):
    def test_actual_inventory_hashes_and_balanced_schedule(self):
        from harness.artifacts import read_json
        rows, entries = inventory()
        self.assertEqual(len(rows), 96)
        self.assertEqual(sum(not r['eligible'] for r in rows), 6)
        self.assertIn('main-A-task_004-SD', {e['artifact_id'] for e in entries})
        config = read_json(ROOT/STUDY/'study_config.json')
        plan = schedule(entries, config)
        self.assertEqual(len(plan), 87)
        self.assertEqual(len({r['audit_run_id'] for r in plan}), 87)
        self.assertEqual(plan, schedule(entries, config))
        for entry in entries:
            self.assertTrue(all(set(r) == {'id', 'text'} for r in entry['public_bundle']['requirements']))
        builder = builder_rows(entries)
        self.assertEqual(len(builder), 145)
        self.assertTrue(all(r['builder_condition'] in ('CD', 'SD') for r in builder))

    def test_evidence_review_requires_real_identity(self):
        evidence = dict(row(condition='evidence'), audit_run_id='audit', evidence_text='code.py absent')
        review = dict(audit_run_id='audit', requirement_id='R1', reviewer_id='', timestamp='',
            rubric_version='1', evidence_specificity='specific_contradiction', evidence_correctness='1')
        with self.assertRaises(ValueError):
            evidence_review([evidence], [review])
        review.update(reviewer_id='human-1', timestamp='2026-11-16T10:00:00Z')
        evidence_review([evidence], [review])
        self.assertEqual(evidence['evidence_correctness'], 1)

    def test_freeze_rejects_tampering_before_model_calls(self):
        from harness.artifacts import read_json, write_json
        from harness.audit_study import freeze, verify_freeze, protocol_files
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            # Copy the exact implemented protocol, not Study 1 outcomes.
            for name in protocol_files():
                destination = target/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT/name, destination)
            with patch('harness.audit_study.verify_preservation'), patch('harness.audit_study.inventory', return_value=inventory()):
                freeze(target)
                self.assertEqual(verify_freeze(target)['study_id'], STUDY)
                with self.assertRaisesRegex(ValueError, 'Never replace'):
                    freeze(target)
                prompt = target/STUDY/'prompts/fresh_auditor.txt'
                prompt.write_text('changed after freeze')
                with self.assertRaisesRegex(ValueError, 'changed after freeze'):
                    verify_freeze(target)

    def test_raw_reanalysis_pipeline_and_figures(self):
        from harness.audit_runner import persist_result
        from harness.artifacts import read_json, write_json
        from analysis.audit_analysis import analyze
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            study = target/STUDY
            for folder in ('manifests', 'inputs'):
                shutil.copytree(ROOT/STUDY/folder, study/folder)
            shutil.copyfile(ROOT/STUDY/'study_config.json', study/'study_config.json')
            import csv
            with (study/'manifests/audit_manifest.csv').open(encoding='utf-8') as stream:
                planned = list(csv.DictReader(stream))
            fresh = next(r for r in planned if r['audit_condition'] == 'fresh')
            entry = read_json(study/'inputs'/f"{fresh['artifact_id']}.json")
            text = '<requirements_check>\n' + '\n'.join(
                r['requirement_id']+': uncertain' for r in entry['truth']) + '\n</requirements_check>'
            outcome = study/'raw'/fresh['audit_run_id']/'attempt0-outcome.json'
            saved = {'result': {'text': text, 'summary': {}, 'latency_seconds': 0}, 'attempt': 0}
            write_json(outcome, saved)
            persist_result(study, fresh, entry, saved, outcome)
            confidence = next(r for r in planned if r['artifact_id'] == fresh['artifact_id'] and r['audit_condition'] == 'confidence')
            confidence_text = '<requirements_confidence>\n' + '\n'.join(
                r['requirement_id']+':\nstatus: uncertain\nprobability_fully_satisfied: 50' for r in entry['truth']) + '\n</requirements_confidence>'
            confidence_outcome = study/'raw'/confidence['audit_run_id']/'attempt0-outcome.json'
            confidence_saved = {'result': {'text': confidence_text, 'summary': {}, 'latency_seconds': 0}, 'attempt': 0}
            write_json(confidence_outcome, confidence_saved)
            persist_result(study, confidence, entry, confidence_saved, confidence_outcome)
            with patch('analysis.audit_analysis.verify_preservation'):
                result = analyze(target, figures=True)
                self.assertEqual(result['collection_status'], 'incomplete')
                self.assertEqual(result['terminal'], 2)
                self.assertTrue((study/'figures/figure_1_failure_detection.pdf').exists())
                self.assertTrue((study/'figures/figure_3_confidence.pdf').exists())
                self.assertEqual(result, analyze(target))
                saved['result']['text'] = 'tampered'
                write_json(outcome, saved)
                with self.assertRaisesRegex(ValueError, 'immutable output differs'):
                    analyze(target)


if __name__ == '__main__':
    unittest.main()
