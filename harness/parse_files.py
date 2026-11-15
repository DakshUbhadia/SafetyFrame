"""Strict full-file parsing: reject the whole response on an invalid file block."""

import re
from .artifacts import confined, relative_path

BLOCK = re.compile(r'<file path="([^"\r\n]+)">\r?\n(.*?)</file>', re.DOTALL)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024


class FormatError(ValueError):
    pass


def parse_files(text, editable_files):
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise FormatError("Response must be text within the 2 MiB limit")
    allowed = {relative_path(path) for path in editable_files}
    if len({path.casefold() for path in allowed}) != len(allowed):
        raise FormatError("Editable paths collide")
    matches = list(BLOCK.finditer(text))
    if not matches or re.search(r"</?file\b", BLOCK.sub("", text)):
        raise FormatError("Missing or malformed full-file blocks")
    files, seen = {}, set()
    for match in matches:
        try:
            name = relative_path(match[1])
        except ValueError as exc:
            raise FormatError(str(exc)) from None
        body = match[2]
        if name not in allowed or name.casefold() in seen:
            raise FormatError("Returned path is uneditable or duplicated")
        if "\x00" in body or re.search(r"</?file\b", body) or len(body.encode("utf-8")) > MAX_FILE_BYTES:
            raise FormatError("Invalid or oversized file body")
        seen.add(name.casefold())
        files[name] = body
    return files


def apply_files(workspace, files):
    # Validate every destination before applying any replacement.
    targets = {name: confined(workspace, name) for name in files}
    for name, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(files[name], encoding="utf-8", newline="\n")


def parse_claims(text, requirement_ids):
    claims = {rid: "missing" for rid in requirement_ids}
    blocks = re.findall(r"<requirements_check>(.*?)</requirements_check>", BLOCK.sub("", text), re.DOTALL)
    issues = []
    if len(blocks) != 1:
        return claims, ["Expected exactly one requirement checklist"]
    seen = set()
    for line in blocks[0].splitlines():
        if not line.strip():
            continue
        row = re.fullmatch(r"\s*(R[1-9][0-9]*):\s*(implemented|not fully implemented|uncertain)(?:\s*[—–:-]\s*.+)?\s*", line)
        if row is None or row[1] not in claims:
            issues.append("Unknown or malformed checklist row")
            continue
        rid, claim = row[1], row[2].replace(" ", "_")
        if rid in seen:
            claims[rid] = "missing"
            issues.append(f"Duplicate claim for {rid}")
        else:
            claims[rid] = claim
        seen.add(rid)
    return claims, issues
