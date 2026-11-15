"""Container-side unittest worker. Only public results may enter model feedback."""

import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import unittest


def main():
    workspace, test_directory, selection = sys.argv[1:4]
    sys.path[:0] = [workspace, test_directory]
    selectors = json.loads(selection)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    result = unittest.TestResult()
    # Suppress candidate/test prints; the parent separately bounds captured OS output.
    with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        if selectors:
            for name in selectors:
                suite.addTests(loader.loadTestsFromName(name))
        else:
            suite = loader.discover(test_directory, pattern="test_*.py")
        count = suite.countTestCases()
        suite.run(result)
    failures = [{"test": test.id(), "message": message[-1500:]}
                for test, message in result.failures + result.errors]
    failures.extend({"test": test.id(), "message": "Unexpected success"} for test in result.unexpectedSuccesses)
    skipped = len(result.skipped) + len(result.expectedFailures)
    failed = len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses) + skipped
    output = {"total": count, "passed": max(0, count - failed), "failures": failures,
              "skipped": skipped, "successful": count > 0 and failed == 0,
              "collection_failed": bool(loader.errors)}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
