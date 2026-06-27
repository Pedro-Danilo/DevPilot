from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# DevPilot tests must exercise the source tree under test, not a stale wheel or
# editable install that may exist in the active virtualenv.  POST-H-014-A compares
# the live FastAPI route tree against .devpilot/interfaces/api_route_contract_registry.json;
# importing an older installed devpilot_core produces a false route mismatch where
# only docs/openapi/health are visible.
if SRC.exists():
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    """Print a stable DevPilot pass-count summary even when pytest runs with -q.

    DevPilot uses `pytest -q` as a local quality gate. Some terminals or
    configurations may show only progress dots. This hook guarantees that the
    number of passed tests appears explicitly in the console output.
    """

    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    errors = len(terminalreporter.stats.get("error", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    terminalreporter.write_line(
        f"DEVPL TEST SUMMARY: {passed} passed, {failed} failed, {errors} errors, {skipped} skipped"
    )
