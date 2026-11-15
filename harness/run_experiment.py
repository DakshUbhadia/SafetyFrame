"""Resumable two-turn trajectories. Default smoke mode is offline and zero-credit."""

import argparse
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import shutil
import tempfile
import time
from uuid import uuid4

from .artifacts import confined, digest, read_json, safe_name, tree_files, tree_hash, write_json
from .budget import BudgetLedger, exclusive_lock
from .parse_files import FormatError, apply_files, parse_claims, parse_files
from .preflight import ROOT, budget_projection, load_env, validate_config
from .prompts import PROMPTS, initial_messages, repair_message
from .providers.adaption import AdaptionProvider, ProviderFailure
from .providers.scripted import ScriptedProvider
from .run_tests import FIXTURE, RunnerError, TestRunner
from .scoring import assess
from .task_bundle import TaskBundle

# Canonical names plus v4 compatibility aliases; per-requirement claims live in their own table.
FIELDS = """run_id task_id task_family model_id returned_model_id provider condition framing requirement_accounting
block_id within_block_order phase status timestamp_turn1 timestamp_turn2 provider_request_id_turn1
provider_request_id_turn2 response_id_turn1 response_id_turn2 model_version_metadata temperature top_p seed
max_output_tokens input_tokens_turn1 output_tokens_turn1 input_tokens_turn2 output_tokens_turn2
latency_turn1_sec latency_turn2_sec prompt_hash repo_hash test_hash public_test_hash hidden_test_hash mapping_hash
format_success_turn1 format_success_turn2 files_returned_turn1 files_returned_turn2 public_passed_turn1
public_passed_turn2 public_total public_tests_passed_turn1 public_tests_passed_turn2 public_tests_total
requirements_passed_turn1 requirements_passed_turn2 requirements_total artifact_tcs_turn1 artifact_tcs_turn2
tcs_turn1 tcs_turn2 repair_gain claimed_implemented claimed_unmet claimed_uncertain claimed_missing
actual_failed_requirements failed_claimed_implemented failed_acknowledged failed_acknowledged_lenient
claimed_unmet_total urdr urdr_strict urdr_lenient false_completion_rate completion_precision
unmet_disclosure_precision provider_failure_type retry_count primary_analysis_included end_to_end_utility_score
input_tokens output_tokens latency_seconds reported_cost estimated_cost cost_accounting_complete
turn1_raw_path turn2_raw_path turn1_workspace_path turn2_workspace_path""".split()


class ReconciliationRequired(RuntimeError):
    """A persisted request has no response; repeating it might duplicate paid work."""


def copy_source(source, target):
    for name, path in tree_files(source).items():
        destination = confined(target, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def request_turn(provider, model, messages, raw_dir, turn, run_id, ledger, context=None):
    for attempt in range(3):
        prefix = f"turn{turn}-attempt{attempt}"
        request_path, outcome_path = raw_dir / f"{prefix}-request.json", raw_dir / f"{prefix}-outcome.json"
        if outcome_path.exists():
            outcome = read_json(outcome_path)
            if ledger and "result" in outcome:
                ledger.settle(f"{run_id}-{prefix}", outcome["result"], model)
        else:
            if request_path.exists():
                raise ReconciliationRequired(f"{prefix} has no recorded outcome; inspect provider/account before any rerun")
            if ledger:
                ledger.reserve(f"{run_id}-{prefix}", messages, model)
            write_json(request_path, {"context": context or {}, "messages": messages, "model_id": model["model_id"],
                       "generation": model["generation"], "turn": turn, "attempt": attempt,
                       "timestamp": datetime.now(timezone.utc).isoformat()}, immutable=True)
            started = time.monotonic()
            try:
                result = provider.generate(messages, model)
                outcome = {"result": result, "attempt": attempt}
            except ProviderFailure as exc:
                outcome = {"failure": exc.kind, "retryable": exc.retryable, "http_status": exc.http_status,
                           "attempt": attempt, "latency_seconds": time.monotonic() - started,
                           "timestamp": datetime.now(timezone.utc).isoformat()}
                if exc.raw is not None:
                    outcome["raw"] = exc.raw
            outcome["context"] = context or {}
            outcome["turn"] = turn
            write_json(outcome_path, outcome, immutable=True)
            if ledger and "result" in outcome:
                ledger.settle(f"{run_id}-{prefix}", result, model)
        if "result" in outcome:
            return outcome["result"], outcome_path
        if not outcome["retryable"] or attempt == 2:
            return None, outcome_path
        time.sleep(min(2 ** attempt, 4))
    raise AssertionError("Unreachable retry state")


def evaluate_turn(task, runner, response, raw_path, snapshot, source, disclosure):
    try:
        files = parse_files(response["text"], task.metadata["editable_files"])
        format_success, format_error = True, None
    except FormatError as exc:
        files, format_success, format_error = {}, False, str(exc)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="safetyframe-stage-", dir=snapshot.parent) as staging:
        copy_source(source, staging)
        apply_files(staging, files)
        expected = tree_hash(staging)
        if snapshot.exists():
            if tree_hash(snapshot) != expected:
                raise RunnerError("Existing snapshot disagrees with the saved response")
        else:
            shutil.copytree(staging, snapshot)
    scored = runner.score(task, snapshot)
    claims, claim_issues = parse_claims(response["text"], task.requirement_ids) if disclosure else (None, [])
    return {"format_success": format_success, "format_error": format_error, "files_returned": len(files),
            "response_hash": digest(response),
            "executor": {"backend": runner.backend, "image_id": runner.image_id, "timeout_seconds": runner.timeout},
            "raw_path": str(raw_path), "workspace_path": str(snapshot), "workspace_hash": expected,
            **scored, "artifact_tcs": scored["tcs"], "tcs": scored["tcs"] if format_success else 0,
            "claims": claims, "claim_issues": claim_issues, "assessment": assess(scored["requirements"], claims)}


def call_statistics(raw_dir, model):
    outcomes = [read_json(path) for path in sorted(raw_dir.glob("*-outcome.json"))]
    counts = {name: [] for name in ("input_tokens", "output_tokens", "reported_cost", "estimated_cost")}
    latency = 0
    for outcome in outcomes:
        result = outcome.get("result", {})
        usage = result.get("summary", {}).get("usage") or {}
        latency += result.get("latency_seconds", outcome.get("latency_seconds", 0))
        counts["input_tokens"].append(usage.get("input_tokens"))
        counts["output_tokens"].append(usage.get("output_tokens"))
        counts["reported_cost"].append(usage.get("cost"))
        if all(isinstance(usage.get(name), (float, int)) for name in ("input_tokens", "output_tokens")):
            pricing = model.get("pricing", {})
            estimate = (usage["input_tokens"] * pricing.get("input_credits_per_million", 0)
                        + usage["output_tokens"] * pricing.get("output_credits_per_million", 0)) / 1e6
        else:
            estimate = None
        counts["estimated_cost"].append(estimate)
    return {**{name: sum(values) if values and all(value is not None for value in values) else None
               for name, values in counts.items()}, "latency_seconds": latency,
            "retry_count": sum(outcome["attempt"] > 0 for outcome in outcomes),
            "cost_accounting_complete": bool(outcomes) and all(value is not None for value in counts["estimated_cost"])}


def build_record(run_id, task, model, provider, condition, block_id, order, hashes, turns, responses, status, failure, raw_dir):
    row = dict.fromkeys(FIELDS)
    row.update(run_id=run_id, task_id=task.metadata["task_id"], task_family=task.metadata["family"],
               model_id=model["model_id"] if provider.name != "scripted" else "scripted-smoke",
               provider=provider.name, condition=condition, framing=task.metadata["framing"],
               requirement_accounting=condition in {"CD", "SD"}, block_id=block_id, within_block_order=order,
               phase=task.metadata["kind"], status=status, temperature=model["generation"].get("temperature"),
               max_output_tokens=model["generation"]["max_output_tokens"], requirements_total=len(task.requirement_ids),
               public_total=task.metadata["public_test_count"], public_tests_total=task.metadata["public_test_count"],
               provider_failure_type=failure or "none",
               primary_analysis_included=status == "completed" and task.metadata["kind"] == "final")
    row.update({key: value for key, value in hashes.items() if key in row})
    row["test_hash"] = digest([hashes["public_test_hash"], hashes["hidden_test_hash"]])
    for index, turn in enumerate(turns, 1):
        for key in ("format_success", "files_returned", "requirements_passed", "artifact_tcs", "tcs"):
            row[f"{key}_turn{index}"] = turn[key]
        row[f"public_passed_turn{index}"] = row[f"public_tests_passed_turn{index}"] = turn["public"]["passed"]
        row[f"turn{index}_raw_path"], row[f"turn{index}_workspace_path"] = turn["raw_path"], turn["workspace_path"]
    for index, response in enumerate(responses, 1):
        summary = response["summary"]
        usage = summary.get("usage") or {}
        row[f"timestamp_turn{index}"] = response["timestamp"]
        row[f"provider_request_id_turn{index}"] = response.get("request_id")
        row[f"response_id_turn{index}"] = summary.get("response_id")
        row[f"input_tokens_turn{index}"], row[f"output_tokens_turn{index}"] = usage.get("input_tokens"), usage.get("output_tokens")
        row[f"latency_turn{index}_sec"] = response["latency_seconds"]
        row["returned_model_id"] = summary.get("returned_model_id")
        row["model_version_metadata"] = summary.get("system_fingerprint")
    if len(turns) == 2 and status == "completed":
        row.update(turns[1]["assessment"])
        row["repair_gain"] = row["tcs_turn2"] - row["tcs_turn1"]
        row["end_to_end_utility_score"] = row["tcs_turn2"]
    elif failure:
        row["end_to_end_utility_score"] = 0
    row.update(call_statistics(raw_dir, model))
    return {"trajectory": row, "turns": turns}


def export_tables(output):
    with exclusive_lock(output / ".tables.lock"):
        records = [read_json(path) for path in sorted((output / "scored").glob("*.json"))]
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(record["trajectory"] for record in records)
        target = output / "scored" / "trajectories.csv"
        target.with_suffix(".tmp").write_text(stream.getvalue(), encoding="utf-8")
        target.with_suffix(".tmp").replace(target)
        requirement_stream = io.StringIO(newline="")
        rw = csv.DictWriter(requirement_stream, fieldnames=["run_id", "task_id", "condition", "model_id", "turn", "requirement_id", "passed", "claim"])
        rw.writeheader()
        for record in records:
            row = record["trajectory"]
            for number, turn in enumerate(record["turns"], 1):
                for rid, passed in turn["requirements"].items():
                    rw.writerow({**{key: row[key] for key in ("run_id", "task_id", "condition", "model_id")},
                                 "turn": number, "requirement_id": rid, "passed": passed,
                                 "claim": None if turn["claims"] is None else turn["claims"][rid]})
        (output / "scored" / "requirements.csv").write_text(requirement_stream.getvalue(), encoding="utf-8")
        manifest = io.StringIO(newline="")
        mw = csv.DictWriter(manifest, fieldnames=["run_id", "task_id", "model_id", "condition", "block_id", "within_block_order", "status"])
        mw.writeheader()
        for path in sorted((output / "runs").glob("*/state.json")):
            state = read_json(path)
            mw.writerow({key: state.get(key) for key in mw.fieldnames})
        (output / "run_manifest.csv").write_text(manifest.getvalue(), encoding="utf-8")


def run_trajectory(task, condition, config, role, provider, runner, output, run_id, block_id="smoke-block", order=1, ledger=None):
    safe_name(run_id)
    safe_name(block_id)
    if role not in config["models"] or condition not in config["models"][role]["conditions"]:
        raise ValueError("Condition is not part of the configured model design")
    if task.metadata["kind"] == "final":
        raise ValueError("Final-study execution is gated until Sprint 6 implements freeze-manifest verification")
    if provider.name != "scripted" and runner.backend != "docker":
        raise ValueError("Model-produced code requires the Docker backend")
    if task.metadata["kind"] == "synthetic" and provider.name != "scripted":
        raise ValueError("Synthetic smoke tasks use the scripted provider only")
    messages = initial_messages(task, condition)
    hashes = {**task.hashes(), "prompt_hash": digest([tree_hash(PROMPTS), messages])}
    model = config["models"][role]
    implementation = tree_hash(ROOT / "harness")
    identity = {"run_id": run_id, "hashes": hashes, "configuration_hash": digest(config), "implementation_hash": implementation,
                "role": role, "condition": condition, "provider": provider.name, "backend": runner.backend,
                "test_timeout": runner.timeout, "image": runner.image, "block_id": block_id, "order": order}
    output = Path(output).resolve()
    run_dir = confined(output, f"runs/{run_id}")
    raw_dir = confined(output, f"raw/{run_id}")
    result_path = confined(output, f"scored/{run_id}.json")
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    confined(output, "scored").mkdir(parents=True, exist_ok=True)
    with exclusive_lock(output / f".{run_id}.lock"):
        identity_path = run_dir / "identity.json"
        if identity_path.exists():
            if read_json(identity_path) != identity:
                raise ValueError("Run identity changed; use a new run ID or reconcile artifacts")
        else:
            write_json(identity_path, identity, immutable=True)
        state_path = run_dir / "state.json"
        if result_path.exists():
            existing = read_json(result_path)
            if read_json(state_path).get("result_hash") != digest(existing):
                raise ValueError("Completed result checksum changed")
            for turn in existing["turns"]:
                if (tree_hash(turn["workspace_path"]) != turn["workspace_hash"]
                        or digest(read_json(turn["raw_path"])["result"]) != turn["response_hash"]):
                    raise ValueError("Completed workspace or raw response checksum changed")
            export_tables(output)
            return existing
        state = {"run_id": run_id, "task_id": task.metadata["task_id"], "model_id": model["model_id"],
                 "condition": condition, "block_id": block_id, "within_block_order": order, "status": "running"}
        write_json(state_path, state)
        turns, responses, failure = [], [], None
        try:
            # Check infrastructure before any paid call, including resumed trajectories.
            runner.verify()
            executor = {"backend": runner.backend, "image_id": runner.image_id, "timeout_seconds": runner.timeout}
            executor_path = run_dir / "executor.json"
            if executor_path.exists():
                if read_json(executor_path) != executor:
                    raise RunnerError("Executor/image changed during an interrupted trajectory")
            else:
                write_json(executor_path, executor, immutable=True)
            for number in (1, 2):
                turn_path = run_dir / f"turn{number}.json"
                response, raw_path = request_turn(provider, model, messages, raw_dir, number,
                                                  f"{digest(str(output))[:12]}-{run_id}", ledger,
                                                  {"run_id": run_id, "task_id": task.metadata["task_id"],
                                                   "condition": condition, "provider": provider.name,
                                                   "block_id": block_id, "within_block_order": order, "role": role})
                if response is None:
                    failure = read_json(raw_path)["failure"]
                    state["status"] = "provider_failed"
                    break
                responses.append(response)
                snapshot = confined(output, f"{'turn1_snapshots' if number == 1 else 'final_snapshots'}/{run_id}")
                source = task.root / "starter" if number == 1 else Path(turns[0]["workspace_path"])
                if turn_path.exists():
                    turn = read_json(turn_path)
                    if tree_hash(snapshot) != turn["workspace_hash"] or turn["response_hash"] != digest(response):
                        raise RunnerError("Saved response or workspace checksum changed")
                else:
                    turn = evaluate_turn(task, runner, response, raw_path, snapshot, source, condition in {"CD", "SD"})
                    write_json(turn_path, turn, immutable=True)
                turns.append(turn)
                if number == 1:
                    messages = messages + [{"role": "assistant", "content": response["text"]},
                                           repair_message(task, condition, turn["public"])]
            else:
                state["status"] = "completed"
        except (ReconciliationRequired, RunnerError) as exc:
            state.update(status="awaiting_reconciliation" if isinstance(exc, ReconciliationRequired) else "harness_failed", error=str(exc))
            write_json(state_path, state)
            export_tables(output)
            raise
        record = build_record(run_id, task, model, provider, condition, block_id, order, hashes,
                              turns, responses, state["status"], failure, raw_dir)
        write_json(result_path, record, immutable=True)
        state["result_hash"] = digest(record)
        write_json(state_path, state)
        export_tables(output)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--smoke", action="store_true", help="Bundled synthetic task; no network or credits")
    modes.add_argument("--live", action="store_true", help="Adaption pilot trajectory; requires Docker and pricing")
    parser.add_argument("--task", type=Path)
    parser.add_argument("--role", choices=("A", "B"), default="A")
    parser.add_argument("--condition", choices=("C", "S", "CD", "SD"), default="CD")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--block-id", default="setup-block")
    parser.add_argument("--within-block-order", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--image", default="python:3.13-slim")
    args = parser.parse_args()
    try:
        config = read_json(ROOT / "config" / "study.json")
        validate_config(config)
        if args.within_block_order < 1:
            raise ValueError("Block order must be positive")
        if args.smoke:
            if args.task:
                raise ValueError("Smoke mode only accepts the bundled fixture")
            task = TaskBundle.load(FIXTURE)
            provider, runner = ScriptedProvider(FIXTURE), TestRunner("trusted_fixture")
            output = args.output or ROOT / "data" / "smoke"
            ledger = None
        else:
            if not args.task:
                raise ValueError("Live pilot mode requires --task")
            load_env(ROOT / ".env")
            if budget_projection(config)["status"] != "estimated_fit":
                raise ValueError("A costed study must fit the credit ceiling before live calls")
            task = TaskBundle.load(args.task)
            if task.metadata["kind"] != "pilot":
                raise ValueError("Only excluded pilot tasks can run before freeze")
            provider_config = config["providers"][config["models"][args.role]["provider"]]
            provider = AdaptionProvider(provider_config)
            runner = TestRunner("docker", args.image)
            output = args.output or ROOT / "data" / "pilot"
            ledger = BudgetLedger(ROOT / "data" / "usage_ledger.json", config)
        run_id = args.run_id or ("smoke-" if args.smoke else "pilot-") + uuid4().hex[:12]
        record = run_trajectory(task, args.condition, config, args.role, provider, runner, output,
                                run_id, args.block_id, args.within_block_order, ledger)
        row = record["trajectory"]
        print(f"Run: {run_id}; status: {row['status']}; TCS: {row['tcs_turn1']} -> {row['tcs_turn2']}")
        print(f"Artifacts: {output.resolve()}; provider: {row['provider']}; study phase: {row['phase']}")
        return 0 if row["status"] == "completed" else 1
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        print(f"Run stopped ({type(exc).__name__}): {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
