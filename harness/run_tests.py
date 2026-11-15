"""Resource-limited Docker execution; local execution only for a reviewed fixture."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from uuid import uuid4
from .artifacts import read_json, tree_hash

WORKER = Path(__file__).with_name("test_worker.py").resolve()
FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "smoke_task"
MAX_CAPTURE = 256 * 1024


class RunnerError(RuntimeError):
    pass


def clean_environment():
    # No provider keys, PYTHONPATH, startup hooks, proxy credentials, or home directory.
    return {name: value for name, value in os.environ.items()
            if name.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC"}}


def docker_command(config_directory):
    command = ["docker", "--config", str(config_directory)]
    host = os.environ.get("SAFETYFRAME_DOCKER_HOST")
    if host is None and os.name == "nt":
        host = "npipe:////./pipe/dockerDesktopLinuxEngine"
    if host:
        command += ["--host", host]
    return command


def bounded_process(command, cwd, timeout, env):
    process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    captured = [bytearray(), bytearray()]
    over_limit = threading.Event()

    def read(stream, destination):
        while block := stream.read(4096):
            remaining = MAX_CAPTURE - len(destination)
            destination.extend(block[:max(0, remaining)])
            if len(block) > remaining:
                over_limit.set()
                process.kill()
        stream.close()

    readers = [threading.Thread(target=read, args=(stream, destination), daemon=True)
               for stream, destination in zip((process.stdout, process.stderr), captured)]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait(timeout=5)
    for reader in readers:
        reader.join(timeout=2)
    return process.returncode, bytes(captured[0]).decode("utf-8", "replace"), timed_out, over_limit.is_set()


class TestRunner:
    def __init__(self, backend="docker", image="python:3.13-slim", timeout=10):
        if backend not in {"docker", "trusted_fixture"} or not 0 < timeout <= 60:
            raise ValueError("Invalid runner backend/timeout")
        self.backend, self.image, self.timeout = backend, image, timeout
        self.image_id = None

    def verify(self):
        if self.backend == "trusted_fixture":
            return
        if not shutil.which("docker"):
            raise RunnerError("Docker is required to execute generated code")
        try:
            with tempfile.TemporaryDirectory(prefix="safetyframe-docker-config-") as directory:
                inspected = subprocess.run(docker_command(directory) + ["image", "inspect", self.image, "--format", "{{.Id}}"],
                                           env=clean_environment(), capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            raise RunnerError("Docker daemon/image is unavailable; no inference was started") from None
        if inspected.returncode or not inspected.stdout.strip().startswith("sha256:"):
            raise RunnerError("Start Docker and explicitly pull the test image first; no inference was started")
        self.image_id = inspected.stdout.strip()

    def check(self, workspace, tests, selectors, expected_count):
        workspace, tests = Path(workspace).resolve(), Path(tests).resolve()
        before = tree_hash(workspace)
        container_name = "safetyframe-test-" + uuid4().hex
        with tempfile.TemporaryDirectory(prefix="safetyframe-runner-") as temporary:
            if self.backend == "trusted_fixture":
                # Neither a CLI switch nor a metadata flag can bless arbitrary code.
                smoke_tests = tests in {(FIXTURE / "public_tests").resolve(), (FIXTURE / "hidden_tests").resolve()}
                allowed = smoke_tests and before in {tree_hash(FIXTURE / folder) for folder in ("starter", "turn1", "turn2")}
                registry = Path(__file__).with_name("trusted_references.json")
                if not allowed and registry.exists():
                    test_hash = tree_hash(tests)
                    allowed = any(before == case["workspace_hash"] and test_hash in
                                  {case["public_tests_hash"], case["hidden_tests_hash"]}
                                  for case in read_json(registry)["cases"])
                if not allowed:
                    raise RunnerError("Local runner refuses code outside reviewed fixture versions")
                command = [sys.executable, "-I", "-B", str(WORKER), str(workspace), str(tests), json.dumps(selectors)]
            else:
                if self.image_id is None:
                    self.verify()
                # Mount only the current code, one test suite, and trusted worker.
                command = docker_command(temporary) + ["run", "--pull", "never", "--rm",
                           "--name", container_name, "--network", "none", "--read-only", "--cap-drop", "ALL",
                           "--security-opt", "no-new-privileges", "--pids-limit", "64", "--memory", "256m",
                           "--memory-swap", "256m", "--cpus", "1", "--user", "65534:65534",
                           "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "--workdir", "/workspace"]
                for source, destination in ((workspace, "/workspace"), (tests, "/tests"), (WORKER, "/runner.py")):
                    if "," in str(source):
                        raise RunnerError("Docker mount paths cannot contain commas")
                    command += ["--mount", f"type=bind,source={source},target={destination},readonly"]
                command += [self.image_id, "python", "-I", "-B", "/runner.py", "/workspace", "/tests", json.dumps(selectors)]
            try:
                code, stdout, timeout, overflow = bounded_process(command, workspace, self.timeout, clean_environment())
            except OSError:
                raise RunnerError("Could not start test executor") from None
            finally:
                if self.backend == "docker":
                    # Only remove the uniquely named container created by this check.
                    try:
                        subprocess.run(docker_command(temporary) + ["rm", "-f", container_name],
                                       env=clean_environment(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                    except (OSError, subprocess.TimeoutExpired):
                        raise RunnerError("Could not confirm test-container cleanup; reconcile Docker before resuming") from None
        if tree_hash(workspace) != before:
            raise RunnerError("Test execution mutated the preserved workspace")
        if self.backend == "docker" and code in {125, 126, 127}:
            raise RunnerError("Container infrastructure failed; this is not a model score")
        failed = {"total": expected_count, "passed": 0, "successful": False, "skipped": 0,
                  "failures": [{"test": "execution", "message": "Test timeout" if timeout else "Output limit exceeded" if overflow else "Test execution failed"}]}
        if timeout or overflow or code:
            return failed
        try:
            result = json.loads(stdout)
        except (ValueError, TypeError):
            return failed
        if result.get("total") != expected_count:
            if result.get("collection_failed") is True:
                # Invalid candidate imports/syntax can collapse unittest discovery into one failed test.
                # The original task/ref suite has already been validated; do not call this infrastructure failure.
                failed["failures"] = result.get("failures") or failed["failures"]
                failed["collection_failure"] = True
                return failed
            raise RunnerError("Test collection count differs from the task manifest")
        if not isinstance(result.get("passed"), int) or not 0 <= result["passed"] <= expected_count or not isinstance(result.get("failures"), list):
            return failed
        return result

    def score(self, task, workspace):
        public = self.check(workspace, task.root / "public_tests", [], task.metadata["public_test_count"])
        hidden, details = {}, {}
        for requirement in task.metadata["requirements"]:
            result = self.check(workspace, task.root / "hidden_tests", requirement["checks"], len(requirement["checks"]))
            hidden[requirement["id"]] = result["successful"]
            details[requirement["id"]] = result
        return {"public": public, "requirements": hidden, "hidden_details": details,
                "requirements_passed": sum(hidden.values()), "tcs": sum(hidden.values()) / len(hidden)}
