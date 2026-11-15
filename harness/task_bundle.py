"""Rendered-task input contract used by the canonical renderer and trajectory harness."""

from dataclasses import dataclass
from pathlib import Path
import re
from .artifacts import confined, digest, read_json, safe_name, tree_files, tree_hash


@dataclass
class TaskBundle:
    root: Path
    metadata: dict

    @classmethod
    def load(cls, root):
        root = Path(root).resolve()
        metadata = read_json(confined(root, "task.json"))
        safe_name(metadata["task_id"])
        if metadata["kind"] not in {"synthetic", "pilot", "final"} or metadata["framing"] not in {"capability", "safety"}:
            raise ValueError("Task kind/framing is invalid")
        for folder in ("starter", "public_tests", "hidden_tests"):
            if not tree_files(confined(root, folder)):
                raise ValueError(f"Empty task directory: {folder}")
        editable = metadata["editable_files"]
        if not editable or len(set(path.casefold() for path in editable)) != len(editable):
            raise ValueError("Editable file list is empty or ambiguous")
        for name in editable:
            if not confined(root / "starter", name).is_file():
                raise ValueError("Editable files must exist in the starter")
        if not confined(root, "specification.md").is_file():
            raise ValueError("Task specification is missing")
        requirements = metadata["requirements"]
        if not 4 <= len(requirements) <= 5 or len({r["id"] for r in requirements}) != len(requirements):
            raise ValueError("A task needs 4–5 distinct requirements")
        for requirement in requirements:
            if not re.fullmatch(r"R[1-9][0-9]*", requirement["id"]) or not requirement["text"].strip() or not requirement["checks"]:
                raise ValueError("Invalid requirement definition")
            for check in requirement["checks"]:
                if not re.fullmatch(r"test_[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.test_[A-Za-z0-9_]+", check):
                    raise ValueError("Hidden checks must be explicit unittest method selectors")
                if not confined(root / "hidden_tests", check.split(".")[0] + ".py").is_file():
                    raise ValueError("Hidden test module does not exist")
        if not isinstance(metadata.get("public_test_count"), int) or metadata["public_test_count"] < 1:
            raise ValueError("Record the expected positive public test count")
        return cls(root, metadata)

    @property
    def requirement_ids(self):
        return [r["id"] for r in self.metadata["requirements"]]

    def hashes(self):
        return {"repo_hash": tree_hash(self.root / "starter"),
                "public_test_hash": tree_hash(self.root / "public_tests"),
                "hidden_test_hash": tree_hash(self.root / "hidden_tests"),
                "mapping_hash": digest(self.metadata.get("mapping", {})),
                "task_hash": tree_hash(self.root)}
