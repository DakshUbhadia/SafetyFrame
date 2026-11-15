"""Audit rendered pairs against canonical text, normalized ASTs, and reference tests."""

import argparse
import ast
import io
import json
import keyword
from pathlib import Path
import platform
import re
import tempfile
import tokenize
from uuid import uuid4

import yaml

from .artifacts import digest, tree_files, tree_hash, write_json
from .preflight import ROOT
from .prompts import initial_messages, prompt_text
from .render_variants import CanonicalTask, ROLES, canonical_python, normalize_text, rendered_files
from .run_experiment import copy_source
from .run_tests import RunnerError, TestRunner
from .task_bundle import TaskBundle


def text_metrics(text):
    return {"characters": len(text), "utf8_bytes": len(text.encode("utf-8")),
            "regex_token_proxy": len(re.findall(r"\w+|[^\w\s]", text))}


def identifier_metrics(texts):
    identifiers = []
    for text in texts:
        ast.parse(text)
        identifiers.extend(item.string for item in tokenize.generate_tokens(io.StringIO(text).readline)
                           if item.type == tokenize.NAME and not keyword.iskeyword(item.string))
    return {"occurrences": len(identifiers), "unique": len(set(identifiers)),
            "mean_length": sum(map(len, identifiers)) / len(identifiers) if identifiers else 0,
            "total_characters": sum(map(len, identifiers))}


def relative_difference(a, b):
    return abs(a - b) / max(a, b) if max(a, b) else 0


def canonical_sources(source):
    files = {}
    for section, sources in source.sources.items():
        for name, text in sources.items():
            path = "specification.md" if section == "canonical" and name == "specification.md" else (
                ("starter" if section == "canonical" else section) + "/" + name)
            files[path] = text
    return files


def audit_pair(template, capability, safety, validate_reference=False, runner=None):
    source = CanonicalTask.load(template)
    variants = {"C": Path(capability).resolve(), "S": Path(safety).resolve()}
    canonical = canonical_sources(source)
    report = {"schema_version": 1, "task_id": source.metadata["task_id"], "kind": source.metadata["kind"],
              "canonical_source_hash": source.source_hash(), "python_version": platform.python_version(),
              "equivalence_pass": True, "automated_balance_pass": True, "reference_pass": None,
              "errors": [], "variants": {}, "files": {}, "prompt_checks": {},
              "token_method": "Unicode regex word/punctuation proxy; not a model tokenizer",
              "model_token_counts": None, "manual_naturalness_review_required": True,
              "mapping_lengths": [{"placeholder": token, "capability": source.mapping["capability"][key],
                                   "safety": source.mapping["safety"][key],
                                   "capability_length": len(source.mapping["capability"][key]),
                                   "safety_length": len(source.mapping["safety"][key])}
                                  for key, token in source.mapping["canonical"].items()]}
    bundles, reversed_files = {}, {}
    for condition, root in variants.items():
        framing = ROLES[condition]
        bundle = TaskBundle.load(root)
        bundles[condition] = bundle
        expected = rendered_files(source, condition)
        actual_paths = tree_files(root)
        if actual_paths.keys() != expected.keys():
            report["errors"].append(f"{condition}: rendered file set differs from canonical plan")
        for name in ("task.json", "provenance.json"):
            if name not in actual_paths or json.loads(actual_paths[name].read_text(encoding="utf-8")) != json.loads(expected[name]):
                report["errors"].append(f"{condition}: {name} differs from expected metadata/provenance")
        reversed_files[condition] = {}
        for name, path in actual_paths.items():
            if name in {"task.json", "provenance.json"}:
                continue
            restored_name = source.reverse(name, framing)
            text = normalize_text(path.read_text(encoding="utf-8"))
            restored = source.reverse(text, framing)
            if restored_name in reversed_files[condition]:
                report["errors"].append(f"{condition}: reverse mapping creates a collision")
            reversed_files[condition][restored_name] = restored
        if reversed_files[condition].keys() != canonical.keys():
            report["errors"].append(f"{condition}: reverse-mapped file set differs")
        starter_texts = [p.read_text(encoding="utf-8") for name, p in tree_files(root / "starter").items()]
        python_texts = [p.read_text(encoding="utf-8") for name, p in tree_files(root / "starter").items() if name.endswith(".py")]
        baseline = initial_messages(bundle, condition)
        disclosure = initial_messages(bundle, condition + "D")
        report["variants"][condition] = {
            "path": str(root), "bundle_hash": tree_hash(root), "requirements": len(bundle.requirement_ids),
            "public_test_count": bundle.metadata["public_test_count"], "file_count": len(actual_paths),
            "starter": text_metrics("\n".join(starter_texts)), "identifiers": identifier_metrics(python_texts),
            "baseline_prompt": text_metrics("\n".join(m["content"] for m in baseline)),
            "disclosure_prompt": text_metrics("\n".join(m["content"] for m in disclosure)),
            "prompt_file_allowlist": ["specification.md", *["starter/" + n for n in tree_files(root / "starter")],
                                      *["public_tests/" + n for n in tree_files(root / "public_tests")]],
            "prompt_excluded_sections": ["hidden_tests", "reference_solution", "task.json", "provenance.json", "authoring_notes"]}
    for name, expected_text in canonical.items():
        c, s = (reversed_files[condition].get(name) for condition in ROLES)
        entry = {"reverse_text_matches_canonical": c == s == expected_text}
        if not entry["reverse_text_matches_canonical"]:
            report["errors"].append(f"{name}: reverse-mapped text differs from canonical source")
        if name.endswith(".py"):
            try:
                dumps = [ast.dump(ast.parse(canonical_python(text, source.mapping["canonical"])), include_attributes=False)
                         for text in (expected_text, c, s)]
                entry["normalized_ast_equal"] = dumps[0] == dumps[1] == dumps[2]
                entry["canonical_ast_hash"] = digest(dumps[0])
            except (SyntaxError, TypeError):
                entry["normalized_ast_equal"] = False
            if not entry["normalized_ast_equal"]:
                report["errors"].append(f"{name}: normalized AST differs (logic, constants, types, or identifiers)")
        report["files"][name] = entry
    for disclosure in (False, True):
        normalized, systems = [], []
        for condition, framing in ROLES.items():
            messages = initial_messages(bundles[condition], condition + ("D" if disclosure else ""))
            body = messages[1]["content"]
            prefix = prompt_text(f"{framing}.txt")
            if not body.startswith(prefix):
                raise ValueError("Unexpected prompt framing package")
            systems.append(messages[0]["content"])
            normalized.append(source.reverse(body[len(prefix):], framing))
        label = "disclosure" if disclosure else "baseline"
        report["prompt_checks"][label] = systems[0] == systems[1] and normalized[0] == normalized[1]
        if not report["prompt_checks"][label]:
            report["errors"].append(f"{label}: prompt bodies differ beyond the intended framing package")
    report["equivalence_pass"] = not report["errors"]
    c_metrics, s_metrics = (report["variants"][condition] for condition in ROLES)
    differences = {"starter_proxy_fraction": relative_difference(c_metrics["starter"]["regex_token_proxy"], s_metrics["starter"]["regex_token_proxy"]),
                   "baseline_prompt_proxy_fraction": relative_difference(c_metrics["baseline_prompt"]["regex_token_proxy"], s_metrics["baseline_prompt"]["regex_token_proxy"]),
                   "disclosure_prompt_proxy_fraction": relative_difference(c_metrics["disclosure_prompt"]["regex_token_proxy"], s_metrics["disclosure_prompt"]["regex_token_proxy"]),
                   "identifier_mean_length_fraction": relative_difference(c_metrics["identifiers"]["mean_length"], s_metrics["identifiers"]["mean_length"])}
    report["balance_diagnostics"] = differences
    report["balance_thresholds"] = {"text_proxy_fraction": .10, "identifier_mean_length_fraction": .20}
    report["automated_balance_pass"] = (
        all(value <= (.20 if key == "identifier_mean_length_fraction" else .10) for key, value in differences.items())
        and c_metrics["identifiers"]["occurrences"] == s_metrics["identifiers"]["occurrences"]
        and c_metrics["identifiers"]["unique"] == s_metrics["identifiers"]["unique"])
    report["reference_validation"] = {"status": "not_requested"}
    if validate_reference and report["equivalence_pass"]:
        runner = runner or TestRunner("docker")
        runner.verify()
        results = {}
        for condition, bundle in bundles.items():
            with tempfile.TemporaryDirectory(prefix="safetyframe-reference-") as temporary:
                workspace = Path(temporary) / "workspace"
                workspace.mkdir()
                copy_source(bundle.root / "reference_solution", workspace)
                results[condition] = runner.score(bundle, workspace)
        report["reference_pass"] = all(result["public"]["successful"] and all(result["requirements"].values())
                                        for result in results.values())
        report["reference_validation"] = {"status": "passed" if report["reference_pass"] else "failed",
                                          "backend": runner.backend, "image_id": runner.image_id, "results": results}
    report["passed"] = report["equivalence_pass"] and report["automated_balance_pass"] and report["reference_pass"] is not False
    report["sprint3_exit_criteria_met"] = report["passed"] and report["reference_pass"] is True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--capability", type=Path, required=True)
    parser.add_argument("--safety", type=Path, required=True)
    parser.add_argument("--validate-reference", action="store_true")
    parser.add_argument("--trusted-example", action="store_true", help="Only exact approved reference/test hashes may execute locally")
    parser.add_argument("--image", default="python:3.13-slim")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if args.trusted_example and not args.validate_reference:
            raise ValueError("--trusted-example requires --validate-reference")
        runner = TestRunner("trusted_fixture" if args.trusted_example else "docker", args.image)
        report = audit_pair(args.template, args.capability, args.safety, args.validate_reference, runner)
        destination = args.report or ROOT / "data" / "audits" / f"{report['task_id']}-{uuid4().hex[:10]}.json"
        write_json(destination, report, immutable=True)
        print(f"Equivalence: {report['equivalence_pass']}; balance diagnostics: {report['automated_balance_pass']}; reference: {report['reference_validation']['status']}")
        print(f"Audit report: {destination.resolve()}")
        return 0 if report["passed"] else 1
    except (ValueError, KeyError, TypeError, OSError, SyntaxError, RunnerError, yaml.YAMLError) as exc:
        print(f"Audit stopped ({type(exc).__name__}): {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
