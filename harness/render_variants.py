"""Deterministically render canonical YAML tasks into paired harness bundles."""

import argparse
import ast
from dataclasses import dataclass
import json
import keyword
from pathlib import Path
import re
import tempfile

import yaml

from .artifacts import confined, digest, read_json, relative_path, safe_name, tree_files, tree_hash
from .preflight import ROOT
from .task_bundle import TaskBundle

TOKEN = re.compile(r"<[A-Z][A-Z0-9_]*>|__SF_[A-Z0-9_]+?__")
ROLES = {"C": "capability", "S": "safety"}
SOURCE_SECTIONS = ("canonical", "public_tests", "hidden_tests", "reference_solution")


class StrictSafeLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise ValueError("YAML aliases are not supported in canonical task configuration")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise ValueError("YAML mapping keys must be distinct strings")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def read_yaml(path):
    path = Path(path)
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Task YAML exceeds 1 MiB")
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    if not isinstance(value, dict):
        raise ValueError("Task YAML must contain a mapping")
    return value


def substitute(text, replacements):
    # One pass: inserted labels are never recursively interpreted as placeholders.
    if not replacements:
        return text
    pattern = re.compile("|".join(re.escape(key) for key in sorted(replacements, key=len, reverse=True)))
    return pattern.sub(lambda match: replacements[match[0]], text)


def canonical_python(text, placeholders):
    return substitute(text, {value: f"__sf_canonical_{key}__" for key, value in placeholders.items()})


def normalize_text(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def validate_mapping(mapping):
    canonical = mapping["canonical"]
    if not isinstance(canonical, dict) or "domain" not in canonical or not canonical:
        raise ValueError("Mapping requires canonical placeholders including domain")
    for key, token in canonical.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not isinstance(token, str) or not TOKEN.fullmatch(token):
            raise ValueError("Mapping keys/placeholders have invalid syntax")
    if len(set(canonical.values())) != len(canonical):
        raise ValueError("Canonical placeholders must be unique")
    if any(a != b and a in b for a in canonical.values() for b in canonical.values()):
        raise ValueError("Canonical placeholders must not overlap")
    for framing in ROLES.values():
        labels = mapping[framing]
        if not isinstance(labels, dict) or labels.keys() != canonical.keys():
            raise ValueError("Both renderings must define exactly the canonical mapping keys")
        values = list(labels.values())
        for key, value in labels.items():
            if not isinstance(value, str) or not value or value != value.strip() or "\n" in value or TOKEN.search(value):
                raise ValueError("Rendered labels must be nonempty single-line literal strings")
            if key != "domain" and (not value.isidentifier() or not value.isascii() or keyword.iskeyword(value)):
                raise ValueError("Code-domain labels must be ASCII Python identifiers")
        if len(set(values)) != len(values) or any(a != b and a in b for a in values for b in values):
            raise ValueError("Rendered labels must be injective and non-overlapping for reversible mapping")
    if mapping["capability"]["domain"] == mapping["safety"]["domain"]:
        raise ValueError("Capability and safety domain contexts must differ")


@dataclass
class CanonicalTask:
    root: Path
    metadata: dict
    mapping: dict
    requirements: list
    sources: dict

    @classmethod
    def load(cls, root):
        root = Path(root).resolve()
        metadata = read_json(confined(root, "task_metadata.json"))
        mapping = read_yaml(confined(root, "mapping.yaml"))
        requirement_file = read_yaml(confined(root, "requirements.yaml"))
        task_id = safe_name(metadata["task_id"])
        if mapping["task_id"] != task_id or requirement_file["task_id"] != task_id:
            raise ValueError("Metadata, mapping, and requirement task IDs must match")
        validate_mapping(mapping)
        if metadata["kind"] not in {"synthetic", "pilot", "final"}:
            raise ValueError("Canonical task kind is invalid")
        if type(metadata["public_test_count"]) is not int or metadata["public_test_count"] < 1:
            raise ValueError("Record a positive public_test_count")
        if not isinstance(metadata["family"], str) or not metadata["family"].strip():
            raise ValueError("Task family is required")
        for field in ("capability", "safety"):
            if not metadata["dual_plausibility"][field].strip():
                raise ValueError("Both domain plausibility notes are required")
        sections = {}
        for section in SOURCE_SECTIONS:
            paths = tree_files(confined(root, section))
            if not paths:
                raise ValueError(f"Canonical task section is empty: {section}")
            sections[section] = {}
            for name, path in paths.items():
                if path.stat().st_size > 512 * 1024:
                    raise ValueError("Canonical task file exceeds 512 KiB")
                text = normalize_text(path.read_text(encoding="utf-8"))
                if set(TOKEN.findall(name + "\n" + text)) - set(mapping["canonical"].values()):
                    raise ValueError("Source contains an undeclared canonical placeholder")
                # A label already in the canonical source could be reverse-mapped incorrectly.
                for framing in ROLES.values():
                    if any(value in name + "\n" + text for value in mapping[framing].values()):
                        raise ValueError("Canonical source contains a rendered label; reverse mapping would be ambiguous")
                if name.endswith(".py"):
                    ast.parse(canonical_python(text, mapping["canonical"]))
                sections[section][name] = text
        if "specification.md" not in sections["canonical"]:
            raise ValueError("canonical/specification.md is required")
        starter = {name for name in sections["canonical"] if name != "specification.md"}
        if starter != set(sections["reference_solution"]):
            raise ValueError("Reference solution must provide the complete starter file set")
        editable = metadata["editable_files"]
        if not editable or any(relative_path(name) not in starter for name in editable):
            raise ValueError("Every editable file must be present in the canonical starter")
        if len({name.casefold() for name in editable}) != len(editable):
            raise ValueError("Editable files must not collide")
        requirements = requirement_file["requirements"]
        if not 4 <= len(requirements) <= 5 or len({r["id"] for r in requirements}) != len(requirements):
            raise ValueError("Canonical tasks require 4–5 distinct requirements")
        if metadata["requirements_total"] != len(requirements):
            raise ValueError("requirements_total differs from the requirement list")
        used_checks = []
        for requirement in requirements:
            if not re.fullmatch(r"R[1-9][0-9]*", requirement["id"]) or requirement["scoring_rule"] != "all_core_checks_pass":
                raise ValueError("Use stable requirement IDs and binary all-core-check scoring")
            if not requirement["text"] or requirement["text"] not in sections["canonical"]["specification.md"]:
                raise ValueError("Requirement text must quote an explicit specification sentence")
            checks = requirement["hidden_checks"]
            if not checks or any(not re.fullmatch(r"test_[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.test_[A-Za-z0-9_]+", check) for check in checks):
                raise ValueError("Hidden checks must name explicit unittest methods")
            used_checks.extend(checks)
        if len(used_checks) != len(set(used_checks)):
            raise ValueError("A hidden check cannot score multiple requirements")
        found_hidden = test_methods(sections["hidden_tests"], mapping["canonical"])
        if set(used_checks) != found_hidden:
            raise ValueError("Hidden check selectors and test methods must match exactly")
        if len(test_methods(sections["public_tests"], mapping["canonical"])) != metadata["public_test_count"]:
            raise ValueError("public_test_count differs from static unittest methods")
        return cls(root, metadata, mapping, requirements, sections)

    def replacements(self, framing):
        return {token: self.mapping[framing][key] for key, token in self.mapping["canonical"].items()}

    def reverse(self, text, framing):
        return substitute(text, {label: self.mapping["canonical"][key] for key, label in self.mapping[framing].items()})

    def source_hash(self):
        return tree_hash(self.root)


def test_methods(sources, placeholders):
    found = set()
    for name, text in sources.items():
        if not re.fullmatch(r"test_[A-Za-z0-9_]+\.py", name):
            raise ValueError("Test suites currently require flat test_*.py modules")
        tree = ast.parse(canonical_python(text, placeholders))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name.startswith("test_"):
                        restore = {f"__sf_canonical_{key}__": token for key, token in placeholders.items()}
                        found.add(f"{name[:-3]}.{substitute(node.name, restore)}.{substitute(method.name, restore)}")
    return found


def rendered_files(source, condition):
    framing = ROLES[condition]
    replacements = source.replacements(framing)
    files = {}
    for section, sources in source.sources.items():
        for name, text in sources.items():
            destination = "specification.md" if section == "canonical" and name == "specification.md" else (
                ("starter" if section == "canonical" else section) + "/" + substitute(name, replacements))
            relative_path(destination)
            if destination.casefold() in {path.casefold() for path in files}:
                raise ValueError("Rendering creates a file collision")
            rendered = substitute(text, replacements)
            if TOKEN.search(destination + rendered):
                raise ValueError("Rendering left an unresolved placeholder")
            if destination.endswith(".py"):
                ast.parse(rendered)
            files[destination] = rendered
    metadata = {"task_id": source.metadata["task_id"], "kind": source.metadata["kind"],
                "family": source.metadata["family"], "framing": framing,
                "editable_files": [substitute(name, replacements) for name in source.metadata["editable_files"]],
                "public_test_count": source.metadata["public_test_count"],
                "requirements": [{"id": r["id"], "text": substitute(r["text"], replacements),
                                  "checks": [substitute(check, replacements) for check in r["hidden_checks"]]}
                                 for r in source.requirements],
                "mapping": {"canonical": source.mapping["canonical"], "labels": source.mapping[framing]}}
    files["task.json"] = json.dumps(metadata, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    files["provenance.json"] = json.dumps({"renderer_schema": 1, "condition": condition,
        "canonical_source_hash": source.source_hash(), "mapping_hash": digest(source.mapping),
        "requirements_hash": digest(source.requirements)}, sort_keys=True, indent=2) + "\n"
    return files


def write_files(root, files):
    for name, text in sorted(files.items()):
        path = confined(root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def existing_matches(root, expected):
    paths = tree_files(root)
    return paths.keys() == expected.keys() and all(path.read_bytes() == expected[name].encode("utf-8") for name, path in paths.items())


def render_pair(template, output=ROOT / "rendered_tasks"):
    source = CanonicalTask.load(template)
    output = Path(output).resolve()
    if output == source.root or output.is_relative_to(source.root) or source.root.is_relative_to(output):
        raise ValueError("Source/output directories must not contain one another")
    plans = {condition: rendered_files(source, condition) for condition in ROLES}
    output.mkdir(parents=True, exist_ok=True)
    targets = {condition: confined(output, f"{source.metadata['task_id']}_{condition}") for condition in ROLES}
    # Validate both existing destinations before publishing either variant. Never overwrite.
    for condition, target in targets.items():
        if target.exists() and not existing_matches(target, plans[condition]):
            raise ValueError("Existing rendering differs; choose a new output directory and preserve old evidence")
    with tempfile.TemporaryDirectory(prefix="safetyframe-render-", dir=output) as staging:
        for condition, files in plans.items():
            staged = Path(staging) / condition
            staged.mkdir()
            write_files(staged, files)
            TaskBundle.load(staged)
        for condition, target in targets.items():
            if not target.exists():
                (Path(staging) / condition).rename(target)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "rendered_tasks")
    args = parser.parse_args()
    try:
        for condition, path in render_pair(args.template, args.output).items():
            print(f"{condition}: {path}")
        return 0
    except (ValueError, KeyError, TypeError, OSError, SyntaxError, yaml.YAMLError) as exc:
        print(f"Rendering stopped ({type(exc).__name__}): {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
