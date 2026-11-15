"""Offline tests of budget, state isolation, credential handling, and API evidence."""

import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from harness import preflight


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((preflight.ROOT / "config" / "study.json").read_text())

    def ready_config(self):
        config = copy.deepcopy(self.config)
        config["study"]["task_target"]=18
        config["budget"].update(unit="credits", available=200, protected_reserve=0, pilot_allowance=10, retry_allowance=10, source="test fixture")
        config["providers"]["adaption"].update(requests_per_minute=10, rate_limit_source="test fixture")
        for role in ("A", "B"):
            config["models"][role].update(model_id=f"test-{role}", family=f"family-{role}",
                selection_rationale="test fixture", settings_verified=True, settings_evidence="test fixture",
                estimated_cost_per_trajectory=1)
        return config

    def test_default_config_preserves_v4_and_costed_plan(self):
        preflight.validate_config(self.config)
        projection = preflight.budget_projection(self.config)
        self.assertEqual(projection["status"], "estimated_fit")
        self.assertEqual([row["responses"] for row in projection["scenarios"]], [192, 240])
        self.assertAlmostEqual(projection["scenarios"][0]["estimated_total"], 34.6528)
        self.assertEqual(projection["planned_spend_ceiling"], 2800)
        self.config["models"]["A"]["estimated_cost_per_trajectory"] = None
        self.assertEqual(preflight.budget_projection(self.config)["status"], "unconfirmed")

    def test_two_turn_budget_includes_pilot_and_retry_allowances(self):
        config = self.ready_config()
        self.assertEqual(preflight.budget_projection(config)["scenarios"][1]["estimated_total"], 128)
        config["budget"]["available"] = 127
        self.assertEqual(preflight.budget_projection(config)["status"], "over_budget")
        config["budget"]["available"] = float("nan")
        self.assertEqual(preflight.budget_projection(config)["status"], "unconfirmed")

    def test_wrong_design_or_insecure_url_is_rejected(self):
        for modify in (lambda c: c["study"].update(turns_per_trajectory=3),
                       lambda c: c["models"]["B"].update(conditions=["C", "S", "SD"]),
                       lambda c: c["providers"]["adaption"].update(base_url="http://example.com")):
            config = copy.deepcopy(self.config)
            modify(config)
            with self.assertRaises(ValueError):
                preflight.validate_config(config)

    def test_protected_reserve_is_excluded_from_planned_spending(self):
        config = self.ready_config()
        config["budget"].update(available=150, protected_reserve=25)
        projection = preflight.budget_projection(config)
        self.assertEqual(projection["planned_spend_ceiling"], 125)
        self.assertEqual(projection["status"], "over_budget")

    def test_unpriced_plan_never_sends_paid_smoke_requests(self):
        config = self.ready_config()
        config["models"]["A"]["estimated_cost_per_trajectory"] = None
        with patch.dict(os.environ, {"ADAPTION_API_KEY": "fake-test-key"}), patch.object(
                preflight, "request_json", return_value=({"data": [{"id": "test-A"}, {"id": "test-B"}]}, {})) as request:
            report = preflight.run_checks(config, "smoke", ["A", "B"])
        self.assertEqual(request.call_count, 1)
        self.assertFalse(report["sprint_1_complete"])
        self.assertIn("No paid request", report["smoke"]["A"]["error"])

    def test_offline_never_contacts_provider_and_cannot_certify_live_success(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(preflight, "request_json") as request:
            report = preflight.run_checks(self.config, "offline", ["A", "B"])
        request.assert_not_called()
        self.assertFalse(report["sprint_1_complete"])
        self.assertTrue(any("ADAPTION_API_KEY" in gap for gap in report["gaps"]))

    def test_env_is_literal_and_process_value_takes_precedence(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"EXISTING": "process"}, clear=True):
            path = Path(directory) / ".env"
            path.write_text('EXISTING=file\nLOCAL="$(no-execution)"\n', encoding="utf-8")
            preflight.load_env(path)
            self.assertEqual(os.environ["EXISTING"], "process")
            self.assertEqual(os.environ["LOCAL"], "$(no-execution)")

    def test_missing_optional_usage_is_preserved_as_null(self):
        summary = preflight.response_summary({"status": "completed", "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "OK"}]}]})
        self.assertTrue(summary["success"])
        self.assertIsNone(summary["usage"])
        self.assertFalse(preflight.response_summary({"status": "incomplete", "output_text": "OK"})["success"])

    def test_same_family_cannot_pass_readiness(self):
        config = self.ready_config()
        config["models"]["B"]["family"] = " FAMILY-A "
        with patch.dict(os.environ, {"ADAPTION_API_KEY": "fake-test-key"}):
            self.assertTrue(any("different families" in gap for gap in preflight.readiness_gaps(config)))

    def test_full_smoke_requires_catalogue_and_two_independent_successes(self):
        calls = []

        def fake_request(provider, path, payload=None):
            calls.append(payload)
            if payload is None:
                return {"data": [{"id": "test-A"}, {"id": "test-B"}]}, {}
            self.assertNotIn("previous_response_id", payload)
            self.assertFalse(payload["agentic_memory"])
            self.assertFalse(payload["store"])
            self.assertEqual(payload["tools"], [])
            self.assertEqual(payload["max_output_tokens"], 8192)
            return {"id": "test-response", "model": payload["model"], "status": "completed", "output_text": "SAFETYFRAME_OK"}, {}

        with patch.dict(os.environ, {"ADAPTION_API_KEY": "fake-test-key"}), patch.object(preflight, "request_json", side_effect=fake_request):
            report = preflight.run_checks(self.ready_config(), "smoke", ["A", "B"])
            single = preflight.run_checks(self.ready_config(), "smoke", ["A"])
        self.assertTrue(report["sprint_1_complete"])
        self.assertFalse(single["sprint_1_complete"])
        self.assertEqual(len(calls), 5)

    def test_inaccessible_model_does_not_send_generation_request(self):
        with patch.dict(os.environ, {"ADAPTION_API_KEY": "fake-test-key"}), patch.object(
                preflight, "request_json", return_value=({"data": []}, {})) as request:
            report = preflight.run_checks(self.ready_config(), "smoke", ["A", "B"])
        self.assertEqual(request.call_count, 1)
        self.assertFalse(report["sprint_1_complete"])

    def test_http_errors_do_not_disclose_key_or_provider_error_body(self):
        provider = self.config["providers"]["adaption"]
        error = HTTPError("https://example.com", 401, "fake-test-key", {}, None)
        with patch.dict(os.environ, {"ADAPTION_API_KEY": "fake-test-key"}), patch.object(preflight, "build_opener") as opener:
            opener.return_value.open.side_effect = error
            with self.assertRaises(ValueError) as caught:
                preflight.request_json(provider, provider["models_path"])
        self.assertNotIn("fake-test-key", str(caught.exception))
        self.assertIn("401", str(caught.exception))
        self.assertIsNone(preflight.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))


if __name__ == "__main__":
    unittest.main()
