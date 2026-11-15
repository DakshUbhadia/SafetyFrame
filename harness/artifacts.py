"""Deterministic artifacts and portable, confined task paths."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat


def safe_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
        raise ValueError("IDs must contain only letters, digits, underscores, or hyphens")
    return value


def relative_path(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        raise ValueError("Only portable relative POSIX file paths are accepted")
    if value.startswith("/") or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError("Absolute, empty, or traversal path components are forbidden")
    for part in value.split("/"):
        stem = part.split(".")[0].upper()
        if part.endswith(".") or stem in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(10)), *(f"LPT{i}" for i in range(10))}:
            raise ValueError("Windows device names and trailing dots are forbidden")
    return PurePosixPath(value).as_posix()


def confined(root, name):
    root = Path(root).resolve()
    name = relative_path(name)
    current = root
    for part in name.split("/"):
        current /= part
        if current.exists() or current.is_symlink():
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise ValueError("Links/reparse points are forbidden in task paths")
    current.resolve().relative_to(root)
    return current


def tree_files(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Task source must be a real directory")
    paths = {}
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.relative_to(root).parts or path.suffix == ".pyc":
            continue
        name = path.relative_to(root).as_posix()
        checked = confined(root, name)
        if checked.is_file():
            paths[name] = checked
        elif not checked.is_dir():
            raise ValueError("Special task files are forbidden")
    folded = [name.casefold() for name in paths]
    if len(folded) != len(set(folded)):
        raise ValueError("Case-colliding task paths are forbidden")
    return paths


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def tree_hash(root):
    return digest({name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in tree_files(root).items()})


def write_json(path, value, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if immutable:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    else:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
