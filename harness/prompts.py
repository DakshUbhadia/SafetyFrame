"""Construct prompts from an explicit public-only allowlist."""

from pathlib import Path
import re
from .artifacts import tree_files

PROMPTS = Path(__file__).resolve().parents[1] / "prompts"


def prompt_text(name):
    return (PROMPTS / name).read_text(encoding="utf-8").strip()


def files_text(root, mapping=None):
    paths = tree_files(root)
    mapping = mapping or {}
    replacements = {label: mapping["canonical"][key] for key, label in mapping.get("labels", {}).items()}
    pattern = re.compile("|".join(re.escape(label) for label in sorted(replacements,key=len,reverse=True))) if replacements else None
    ordered = sorted(paths, key=lambda name: pattern.sub(lambda match: replacements[match[0]],name) if pattern else name)
    return "\n\n".join(f'<file path="{name}">\n{path.read_text(encoding="utf-8")}\n</file>'
                       for name in ordered for path in [paths[name]])


def initial_messages(task, condition):
    framing = "capability" if condition in {"C", "CD"} else "safety"
    if task.metadata["framing"] != framing:
        raise ValueError("Condition does not match the rendered task framing")
    text = (prompt_text(f"{framing}.txt") + "\n\nTechnical requirements:\n\n"
            + (task.root / "specification.md").read_text(encoding="utf-8")
            + "\n\nRepository files:\n\n" + files_text(task.root / "starter", task.metadata.get("mapping"))
            + "\n\nPublic tests:\n\n" + files_text(task.root / "public_tests", task.metadata.get("mapping"))
            + '\n\nOutput format:\n\nReturn complete replacement contents of every file you modify.\n'
              '<file path="relative/path.py">\n...complete file contents...\n</file>')
    if condition in {"CD", "SD"}:
        text += "\n\n" + accounting(task.requirement_ids)
    return [{"role": "system", "content": prompt_text("system.txt")}, {"role": "user", "content": text}]


def accounting(requirement_ids):
    return (prompt_text("requirement_accounting.txt") + "\n\nUse one row for each of "
            + ", ".join(requirement_ids) + ":\n<requirements_check>\nR1: implemented\n...\n</requirements_check>")


def feedback(public_result):
    # Never accept a combined public/hidden scoring object here.
    details = "\n".join(f"{item['test']}: {item['message']}" for item in public_result["failures"])
    return (f"Public-test feedback from your implementation:\n\nPassed: {public_result['passed']}\n"
            f"Failed: {public_result['total'] - public_result['passed']}\n\n{details}")


def repair_message(task, condition, public_result):
    text = prompt_text("turn2.txt") + "\n\n" + feedback(public_result)
    if condition in {"CD", "SD"}:
        text += "\n\n" + accounting(task.requirement_ids)
    return {"role": "user", "content": text}
