"""Account discovery and small smoke requests, never benchmark execution.

Run from the repository root: python -m harness.preflight --offline
Only --list-models and --smoke contact the configured provider.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path) -> None:
    """Read literal KEY=value entries without evaluating code or interpolation."""
    if not path.exists():
        return
    entries = []
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or not name.isidentifier():
            raise ValueError(f"Invalid environment entry at line {number}; use KEY=value")
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"Unclosed environment value at line {number}")
            value = value[1:-1]
        entries.append((name, value))
    for name, value in entries:
        os.environ.setdefault(name, value)


def validate_config(config: dict) -> None:
    study = config["study"]
    if config["schema_version"] != 1:
        raise ValueError("Unsupported configuration schema")
    for field in ("task_minimum", "task_target", "task_maximum"):
        if type(study[field]) is not int:
            raise ValueError(f"{field} must be an integer")
    if not 16 <= study["task_minimum"] <= study["task_target"] <= study["task_maximum"] <= 20:
        raise ValueError("Final task counts must be ordered within 16..20")
    if study["turns_per_trajectory"] != 2 or study["primary_endpoint"] != "tcs_turn2":
        raise ValueError("v4 requires two turns and the Turn-2 TCS endpoint")
    if study["analysis_unit"] != "task" or study["requirements_per_task"] != [4, 5]:
        raise ValueError("v4 requires task-level inference and 4..5 requirements")
    if study["pilot_task_range"] != [4, 6] or study["frozen"] is not False:
        raise ValueError("Sprint 1 requires 4..6 pilot tasks and an unfrozen design")
    for provider in config["providers"].values():
        url = urlsplit(provider["base_url"])
        if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError("Provider base URLs must use HTTPS without credentials or queries")
        for key in ("models_path", "responses_path"):
            path = provider[key]
            if not path.startswith("/") or path.startswith("//") or "#" in path:
                raise ValueError(f"Invalid provider {key}")
        if not provider["api_key_env"].isidentifier():
            raise ValueError("api_key_env must name an environment variable")
        if not 0 < provider["timeout_seconds"] <= 60:
            raise ValueError("Provider timeout must be within 0..60 seconds")
    for role, expected in (("A", ["C", "S", "CD", "SD"]), ("B", ["C", "S"])):
        model = config["models"][role]
        if model["provider"] not in config["providers"] or model["conditions"] != expected:
            raise ValueError(f"Model {role} must use a known provider and default conditions")
        generation = model["generation"]
        if set(generation) - {"temperature", "max_output_tokens"}:
            raise ValueError("Use only documented generation settings for this provider preflight")
        if type(generation["max_output_tokens"]) is not int or generation["max_output_tokens"] < 1:
            raise ValueError("max_output_tokens must be a positive integer")
        if "temperature" in generation and not 0 <= generation["temperature"] <= 2:
            raise ValueError("temperature must be within 0..2")


def nonnegative_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def budget_projection(config: dict) -> dict:
    budget = config["budget"]
    costs = {role: model["estimated_cost_per_trajectory"] for role, model in config["models"].items()}
    reserve = budget.get("protected_reserve", 0)
    complete = all(nonnegative_number(value) for value in [
        budget["available"], reserve, budget["pilot_allowance"], budget["retry_allowance"], *costs.values()
    ]) and bool(budget["unit"] and budget["source"])
    ceiling = budget["available"] - reserve if nonnegative_number(budget["available"]) and nonnegative_number(reserve) else None
    result = {"status": "unconfirmed", "unit": budget["unit"],
              "allocation": budget["available"], "protected_reserve": reserve,
              "planned_spend_ceiling": ceiling, "scenarios": []}
    for count in sorted(set(config["study"][key] for key in ("task_minimum", "task_target", "task_maximum"))):
        row = {"tasks": count, "trajectories_A": 4 * count, "trajectories_B": 2 * count, "responses": 12 * count}
        if complete:
            row["estimated_total"] = 4 * count * costs["A"] + 2 * count * costs["B"] + budget["pilot_allowance"] + budget["retry_allowance"]
            row["within_budget"] = row["estimated_total"] <= ceiling
        result["scenarios"].append(row)
    if complete:
        target = next(row for row in result["scenarios"] if row["tasks"] == config["study"]["task_target"])
        result["status"] = "estimated_fit" if target["within_budget"] else "over_budget"
    return result


def readiness_gaps(config: dict) -> list[str]:
    gaps = []
    for role, model in config["models"].items():
        for field in ("model_id", "family", "selection_rationale"):
            if not isinstance(model[field], str) or not model[field].strip():
                gaps.append(f"Model {role}: {field} is not recorded")
        if model["settings_verified"] is not True or not model["settings_evidence"]:
            gaps.append(f"Model {role}: study generation settings are not verified")
        provider = config["providers"][model["provider"]]
        if not os.environ.get(provider["api_key_env"], "").strip():
            gaps.append(f"{model['provider']}: {provider['api_key_env']} is not configured")
        if not nonnegative_number(provider["requests_per_minute"]) or provider["requests_per_minute"] == 0 or not provider["rate_limit_source"]:
            gaps.append(f"{model['provider']}: account rate limit is not confirmed")
    family_a, family_b = (config["models"][role]["family"] for role in ("A", "B"))
    if family_a and family_b and family_a.strip().casefold() == family_b.strip().casefold():
        gaps.append("Models A and B must belong to meaningfully different families")
    if budget_projection(config)["status"] != "estimated_fit":
        gaps.append("Inference budget is unconfirmed or insufficient for the task target")
    return list(dict.fromkeys(gaps))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a bearer credential to a redirected host.
        return None


def request_json(provider: dict, path: str, payload: dict | None = None) -> tuple[dict, dict]:
    key = os.environ.get(provider["api_key_env"], "").strip()
    if not key:
        raise ValueError(f"Missing environment variable {provider['api_key_env']}")
    request = Request(provider["base_url"].rstrip("/") + path,
                      data=None if payload is None else json.dumps(payload).encode("utf-8"),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    started = time.monotonic()
    try:
        with build_opener(NoRedirect()).open(request, timeout=provider["timeout_seconds"]) as response:
            data = json.load(response)
            headers = {name.lower(): value for name, value in response.headers.items()
                       if name.lower() in {"x-request-id", "request-id", "retry-after"}
                       or name.lower().startswith("x-ratelimit-")}
            metadata = {"http_status": response.status, "latency_seconds": round(time.monotonic() - started, 3), "headers": headers}
    except HTTPError as exc:
        # Do not expose response bodies, URLs, or credentials in error logs.
        raise ValueError(f"Provider returned HTTP {exc.code}; inspect account access/settings") from None
    except (URLError, TimeoutError, OSError):
        raise ValueError("Provider transport/timeout failure; no retry performed") from None
    if not isinstance(data, dict):
        raise ValueError("Provider returned a non-object JSON response")
    return data, metadata


def response_summary(data: dict) -> dict:
    text = data.get("output_text")
    if not isinstance(text, str):
        output = data.get("output")
        text = "".join(part["text"] for item in (output if isinstance(output, list) else [])
                       if isinstance(item, dict) and item.get("type") == "message" and isinstance(item.get("content"), list)
                       for part in item["content"] if isinstance(part, dict) and part.get("type") == "output_text"
                       and isinstance(part.get("text"), str))
    return {"response_id": data.get("id"), "returned_model_id": data.get("model"),
            "status": data.get("status"), "output_text": text,
            "incomplete_details": data.get("incomplete_details"),
            "usage": data.get("usage"), "system_fingerprint": data.get("system_fingerprint"),
            "success": data.get("status") == "completed" and bool(text.strip())}


def run_checks(config: dict, mode: str, roles: list[str]) -> dict:
    report = {"mode": mode, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "runtime": {"python": platform.python_version(), "platform": platform.platform(), "virtual_environment": sys.prefix != sys.base_prefix},
              "configuration_valid": True, "gaps": readiness_gaps(config),
              "budget": budget_projection(config), "catalogues": {}, "smoke": {},
              "sprint_1_complete": False}
    if mode == "offline":
        return report
    providers = sorted({config["models"][role]["provider"] for role in roles})
    for name in providers:
        provider = config["providers"][name]
        try:
            data, metadata = request_json(provider, provider["models_path"])
            models = data.get("data")
            if not isinstance(models, list) or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in models):
                raise ValueError("Model catalogue lacks valid data/model IDs")
            report["catalogues"][name] = {"models": [
                {key: item.get(key) for key in ("id", "display_name", "owned_by", "shutdown_date")}
                for item in models], "metadata": metadata}
        except (ValueError, KeyError, TypeError) as exc:
            report["catalogues"][name] = {"error": str(exc)}
    if mode != "smoke":
        return report
    for role in roles:
        model = config["models"][role]
        provider = config["providers"][model["provider"]]
        catalogue = report["catalogues"][model["provider"]]
        if report["budget"]["status"] != "estimated_fit":
            report["smoke"][role] = {"success": False, "error": "No paid request sent: enter cost estimates and fit the plan within the spend ceiling first"}
            continue
        if not model["model_id"] or "error" in catalogue:
            report["smoke"][role] = {"success": False, "error": "Select an exact model ID after successful account discovery"}
            continue
        if model["model_id"] not in {item["id"] for item in catalogue["models"]}:
            report["smoke"][role] = {"success": False, "error": "Selected model is not in the account's hosted catalogue"}
            continue
        payload = {"model": model["model_id"], "input": "Reply with SAFETYFRAME_OK.",
                   "max_output_tokens": model["generation"]["max_output_tokens"], "store": False, "agentic_memory": False,
                   "stream": False, "tools": [], "tool_choice": "none"}
        if "temperature" in model["generation"]:
            payload["temperature"] = model["generation"]["temperature"]
        try:
            data, metadata = request_json(provider, provider["responses_path"], payload)
            report["smoke"][role] = {**response_summary(data), "requested_model_id": model["model_id"],
                                     "request_settings": payload, "metadata": metadata}
        except (ValueError, KeyError, TypeError) as exc:
            report["smoke"][role] = {"success": False, "error": str(exc)}
    report["sprint_1_complete"] = (not report["gaps"] and set(roles) == {"A", "B"}
                                    and all(report["smoke"][role]["success"] for role in roles))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--offline", action="store_true", help="Validate setup without network calls")
    modes.add_argument("--list-models", action="store_true", help="Read the account-authorized hosted catalogue")
    modes.add_argument("--smoke", action="store_true", help="Send one small paid request per selected role; no retries")
    parser.add_argument("--role", choices=("A", "B", "all"), default="all")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "study.json")
    args = parser.parse_args()
    try:
        load_env(ROOT / ".env")
        config = json.loads(args.config.read_text(encoding="utf-8-sig"))
        validate_config(config)
        mode = "offline" if args.offline else "list_models" if args.list_models else "smoke"
        report = run_checks(config, mode, ["A", "B"] if args.role == "all" else [args.role])
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Preflight setup error: {type(exc).__name__}; check configuration and local environment file", file=sys.stderr)
        return 2
    output = ROOT / "data" / "setup"
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output / f"preflight-{stamp}-{uuid4().hex[:8]}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Preflight report: {path}")
    print(f"Mode: {mode}; configuration valid; Sprint 1 complete: {report['sprint_1_complete']}")
    for gap in report["gaps"]:
        print(f"Pending: {gap}")
    for name, catalogue in report["catalogues"].items():
        print(f"Catalogue {name}: {catalogue.get('error', str(len(catalogue.get('models', []))) + ' models saved')}")
    for role, smoke in report["smoke"].items():
        print(f"Model {role} smoke: {'passed' if smoke['success'] else smoke.get('error', 'no completed text response')}")
    if mode == "offline":
        return 0
    if mode == "list_models":
        return int(any("error" in catalogue for catalogue in report["catalogues"].values()))
    return 0 if report["sprint_1_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
