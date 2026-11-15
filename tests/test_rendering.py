import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import yaml

from harness.artifacts import read_json, tree_files, tree_hash
from harness.audit_equivalence import audit_pair
from harness.preflight import ROOT
from harness.prompts import initial_messages
from harness.render_variants import CanonicalTask, read_yaml, render_pair, validate_mapping
from harness.run_tests import RunnerError, TestRunner
from harness.task_bundle import TaskBundle

EXAMPLE = ROOT / "task_templates" / "synthetic_domain_utils"


class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="safetyframe-render-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.template = self.root / "template"
        shutil.copytree(EXAMPLE, self.template, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.output = self.root / "rendered"

    def pair(self):
        return render_pair(self.template, self.output)

    def test_reproducible_pair_renames_files_identifiers_strings_and_tests(self):
        source_before = tree_hash(self.template)
        pair = self.pair()
        first = {role: tree_hash(path) for role, path in pair.items()}
        self.assertEqual(first, {role: tree_hash(path) for role, path in self.pair().items()})
        self.assertEqual(source_before, tree_hash(self.template))
        self.assertTrue((pair["C"] / "starter" / "performance_monitor.py").exists())
        self.assertTrue((pair["S"] / "starter" / "robustness_monitor.py").exists())
        for role in ("C", "S"):
            task = TaskBundle.load(pair[role])
            self.assertEqual(len(task.requirement_ids), 4)
            self.assertEqual(len(task.metadata["requirements"][0]["checks"]), 2)
            self.assertEqual(task.metadata["kind"], "synthetic")
            self.assertNotIn("__SF_", (pair[role] / "public_tests" / "test_public.py").read_text())
        self.assertIn("test_normalize_safety_eval_run", (pair["S"] / "public_tests" / "test_public.py").read_text())

    def test_static_audit_anchors_both_variants_to_canonical_source(self):
        pair = self.pair()
        report = audit_pair(self.template, pair["C"], pair["S"])
        self.assertTrue(report["passed"])
        self.assertTrue(report["equivalence_pass"])
        self.assertTrue(report["automated_balance_pass"])
        self.assertIsNone(report["reference_pass"])
        self.assertFalse(report["sprint3_exit_criteria_met"])
        self.assertTrue(all(report["prompt_checks"].values()))
        for name, checks in report["files"].items():
            self.assertTrue(checks["reverse_text_matches_canonical"])
            if name.endswith(".py"):
                self.assertTrue(checks["normalized_ast_equal"])
        self.assertEqual(report["variants"]["C"]["identifiers"]["occurrences"], report["variants"]["S"]["identifiers"]["occurrences"])
        self.assertIsNone(report["model_token_counts"])
        self.assertIn("not a model tokenizer", report["token_method"])

    def test_multifile_prompt_order_uses_canonical_names_not_rendered_alphabet(self):
        for folder in ('canonical','reference_solution'):
            (self.template/folder/'reporting.py').write_text('VALUE = 1\n')
        pair=self.pair()
        report=audit_pair(self.template,pair['C'],pair['S'])
        self.assertTrue(report['equivalence_pass'])
        for role,module in [('C','performance_monitor.py'),('S','robustness_monitor.py')]:
            body=initial_messages(TaskBundle.load(pair[role]),role)[1]['content']
            self.assertLess(body.index('<file path="'+module+'">'),body.index('<file path="reporting.py">'))

    def test_both_references_pass_public_and_all_hidden_requirements(self):
        pair = self.pair()
        report = audit_pair(self.template, pair["C"], pair["S"], True, TestRunner("trusted_fixture"))
        self.assertTrue(report["sprint3_exit_criteria_met"])
        for role in ("C", "S"):
            result = report["reference_validation"]["results"][role]
            self.assertEqual(result["public"]["passed"], 3)
            self.assertEqual(result["requirements_passed"], 4)
            self.assertEqual(sum(r["total"] for r in result["hidden_details"].values()), 8)
            self.assertEqual(result["tcs"], 1)

    def test_hidden_reference_and_author_notes_are_not_in_any_prompt(self):
        pair = self.pair()
        for role in ("C", "S"):
            task = TaskBundle.load(pair[role])
            for condition in (role, role + "D"):
                text = json.dumps(initial_messages(task, condition))
                for forbidden in ("STAGE3_HIDDEN_TEST_MATERIAL_58d09c", "STAGE3_AUTHOR_NOTES_624c1a",
                                  "STAGE3_REFERENCE_MATERIAL_d44b7e", "reference_solution", "test_hidden", "result.append(record)"):
                    self.assertNotIn(forbidden, text)
            self.assertFalse((pair[role] / "authoring_notes.md").exists())

    def test_modified_logic_fails_even_if_both_variants_change_identically(self):
        pair = self.pair()
        for role, module in (("C", "performance_monitor.py"), ("S", "robustness_monitor.py")):
            path = pair[role] / "starter" / module
            path.write_text(path.read_text().replace("raise NotImplementedError", "return None"))
        report = audit_pair(self.template, pair["C"], pair["S"])
        self.assertFalse(report["equivalence_pass"])
        self.assertFalse(report["files"]["starter/__SF_MONITOR_COMPONENT__.py"]["normalized_ast_equal"])

    def test_one_sided_constants_and_extra_files_fail(self):
        pair = self.pair()
        path = pair["S"] / "hidden_tests" / "test_hidden.py"
        path.write_text(path.read_text().replace('"timestamp": 7', '"timestamp": 8'))
        (pair["S"] / "extra.txt").write_text("unexpected content")
        report = audit_pair(self.template, pair["C"], pair["S"])
        self.assertFalse(report["passed"])
        self.assertFalse(report["files"]["hidden_tests/test_hidden.py"]["normalized_ast_equal"])
        self.assertTrue(any("file set" in error for error in report["errors"]))

    def test_one_sided_comment_change_is_rejected_even_when_ast_matches(self):
        pair = self.pair()
        path = pair["S"] / "starter" / "robustness_monitor.py"
        path.write_text(path.read_text() + "\n# Unplanned one-sided cue\n")
        report = audit_pair(self.template, pair["C"], pair["S"])
        checks = report["files"]["starter/__SF_MONITOR_COMPONENT__.py"]
        self.assertTrue(checks["normalized_ast_equal"])
        self.assertFalse(checks["reverse_text_matches_canonical"])
        self.assertFalse(report["equivalence_pass"])

    def test_renderer_does_not_overwrite_existing_or_publish_a_partial_pair(self):
        pair = self.pair()
        path = pair["S"] / "starter" / "robustness_monitor.py"
        path.write_text(path.read_text() + "\n# preserve this evidence\n")
        before = {role: tree_hash(path) for role, path in pair.items()}
        with self.assertRaises(ValueError):
            self.pair()
        self.assertEqual(before, {role: tree_hash(path) for role, path in pair.items()})
        with self.assertRaises(ValueError):
            render_pair(self.template, self.template / "generated")

    def test_mapping_injectivity_overlap_keyword_and_path_errors_are_rejected(self):
        source = CanonicalTask.load(self.template)
        mutations = [
            lambda m: m["safety"].update(primary_score=m["safety"]["run_record"]),
            lambda m: m["safety"].update(run_record="score", primary_score="alignment_score"),
            lambda m: m["safety"].update(monitor_component="../escape"),
            lambda m: m["safety"].update(monitor_component="if"),
            lambda m: m["safety"].pop("domain"),
        ]
        for change in mutations:
            mapping = copy.deepcopy(source.mapping)
            change(mapping)
            with self.assertRaises(ValueError):
                validate_mapping(mapping)

    def test_undeclared_placeholders_and_preexisting_labels_are_rejected(self):
        path = self.template / "canonical" / "specification.md"
        original = path.read_text()
        for suffix in ("\n__SF_UNKNOWN__\n", "\nalignment_score\n"):
            path.write_text(original + suffix)
            with self.assertRaises(ValueError):
                self.pair()
            self.assertFalse(self.output.exists())

    def test_yaml_duplicates_aliases_and_object_tags_are_rejected(self):
        path = self.root / "bad.yaml"
        for content in ("task_id: one\ntask_id: two\n", "a: &x [1]\nb: *x\n", "!!python/object/apply:builtins.print ['never execute']"):
            path.write_text(content)
            with self.assertRaises((ValueError, yaml.YAMLError)):
                read_yaml(path)

    def test_requirement_text_and_hidden_check_mapping_are_validated(self):
        path = self.template / "requirements.yaml"
        original = path.read_text()
        path.write_text(original.replace("test_R1_invalid", "test_does_not_exist"))
        with self.assertRaises(ValueError):
            self.pair()
        path.write_text(original.replace("strips whitespace", "invents an unstated behavior"))
        with self.assertRaises(ValueError):
            self.pair()

    def test_unapproved_reference_cannot_execute_locally(self):
        path = self.template / "reference_solution" / "__SF_MONITOR_COMPONENT__.py"
        path.write_text(path.read_text() + "\n# A changed reference requires a new review/hash approval.\n")
        pair = self.pair()
        with patch("harness.run_tests.bounded_process") as execute, self.assertRaises(RunnerError):
            audit_pair(self.template, pair["C"], pair["S"], True, TestRunner("trusted_fixture"))
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
