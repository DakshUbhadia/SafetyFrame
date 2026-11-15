import ast
from collections import Counter
import copy
import csv
from pathlib import Path
import tempfile
import unittest

from harness.artifacts import read_json, tree_hash
from harness.audit_equivalence import audit_pair
from harness.build_benchmark import build_task, definitions
from harness.pilot_catalog import PILOTS
from harness.preflight import ROOT
from harness.prompts import initial_messages
from harness.render_variants import render_pair
from harness.task_bundle import TaskBundle
from harness.validate_benchmark import check_record, exclusions, fault_source, verify_inventory


class BenchmarkTests(unittest.TestCase):
    def test_membership_covers_four_families_without_pilot_reuse(self):
        tasks=definitions()
        self.assertEqual(len({d['id'] for d in tasks}),16)
        self.assertEqual(Counter(d['family'] for d in tasks),
                         dict(ingestion=4,metrics=4,experiments=4,monitoring=4))
        self.assertTrue({d['id'] for d in tasks}.isdisjoint(exclusions()))
        pilot_sources={ast.dump(ast.parse(text.strip()),include_attributes=False)
                       for d in PILOTS for name,text in d['files'].items() if name.endswith('.py')}
        for task in tasks:
            self.assertNotIn(ast.dump(ast.parse(task['core'].strip()),include_attributes=False),pilot_sources)
            self.assertEqual(len(task['functions']),5)
            self.assertEqual([len(c) for c in task['cases']],[2]*5)

    def test_all_sources_are_reproducible_paired_and_keep_private_material_out_of_prompts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for definition in definitions():
                template=build_task(definition,root/'templates')
                before=tree_hash(template)
                self.assertEqual(before,tree_hash(build_task(definition,root/'templates')))
                pair=render_pair(template,root/'rendered')
                audit=audit_pair(template,pair['C'],pair['S'])
                self.assertTrue(audit['equivalence_pass'])
                self.assertTrue(audit['automated_balance_pass'])
                self.assertFalse(audit['sprint3_exit_criteria_met'])  # Static checks cannot bless a reference.
                for condition in ('C','S'):
                    bundle=TaskBundle.load(pair[condition])
                    messages=initial_messages(bundle,condition)
                    text='\n'.join(m['content'] for m in messages)
                    self.assertNotIn('_impl_',text)
                    self.assertNotIn('authoring_notes',text)
                    self.assertNotIn('test_R1_case',text)
                    self.assertNotIn('reference_solution',text)
                    self.assertEqual(bundle.metadata['kind'],'final')
                self.assertEqual(before,tree_hash(template))
                changed=copy.deepcopy(definition); changed['extra']+=' Changed.'
                with self.assertRaises(ValueError): build_task(changed,root/'templates')

    def test_fault_injection_changes_only_selected_public_api(self):
        text='def a(x):\n    return x+1\n\ndef b(x):\n    return x-1\n'
        original=ast.parse(text); changed=ast.parse(fault_source(text,'a'))
        self.assertEqual(ast.dump(original.body[1]),ast.dump(changed.body[1]))
        self.assertIsInstance(changed.body[0].body[0],ast.Raise)

    def test_acceptance_refuses_missing_docker_reference_or_incomplete_fault_evidence(self):
        registry=read_json(ROOT/'config/benchmark.json')
        record=read_json(ROOT/registry['tasks'][0]['validation_record'])
        for alter in (
            lambda r:r.update(accepted=False),
            lambda r:r['audit'].update(reference_pass=None),
            lambda r:r['audit']['reference_validation'].update(backend='trusted_fixture'),
            lambda r:r['audit']['reference_validation']['results']['S']['requirements'].update(R1=False),
            lambda r:r['audit'].update(automated_balance_pass=False),
            lambda r:r['fault_checks'].pop(),
            lambda r:r['fault_checks'][0]['requirements'].update(R1=True),
            lambda r:r['artifact_hashes'].update(C='changed'),
            lambda r:r.update(task_id=exclusions()[0]),
        ):
            changed=copy.deepcopy(record); alter(changed)
            with self.assertRaises(ValueError): check_record(changed)

    def test_published_inventory_is_backed_by_current_accepted_artifacts(self):
        verify_inventory()
        with (ROOT/'data/task_inventory.csv').open(encoding='utf-8',newline='') as stream:
            rows=list(csv.DictReader(stream))
        expected={d['id'] for d in definitions()}
        self.assertEqual({row['task_id'] for row in rows},expected)
        self.assertEqual(len(rows),16)
        for row in rows:
            self.assertEqual(row['requirements_total'],'5')
            self.assertEqual(row['final_included'],'True')
            self.assertEqual(row['model_calls'],'0')
            checklist=(ROOT/'data/task_validation'/f"{row['task_id']}.md").read_text(encoding='utf-8')
            self.assertNotIn('[FILL',checklist)
            self.assertIn('- [x] ACCEPT into final benchmark.',checklist)
            self.assertIn('Pending Sprint 6',checklist)


if __name__=='__main__':
    unittest.main()
