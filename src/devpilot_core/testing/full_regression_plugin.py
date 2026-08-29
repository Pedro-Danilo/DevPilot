from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _outcome_for_report(report: Any) -> str | None:
    if report.when == "setup":
        if report.skipped:
            return "SKIP_APPROVED"
        if report.failed:
            return "ERROR"
        return None
    if report.when == "call":
        if report.passed:
            return "PASS"
        if report.skipped:
            return "SKIP_APPROVED"
        if report.failed:
            return "FAIL"
    if report.when == "teardown" and report.failed:
        return "ERROR"
    return None


def pytest_runtest_logreport(report: Any) -> None:
    outcome = _outcome_for_report(report)
    if outcome is None:
        return
    target = os.environ.get("DEVPILOT_FULL_SESSION_OUTCOMES")
    if not target:
        return
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": outcome,
        "duration_seconds": float(getattr(report, "duration", 0.0) or 0.0),
    }
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
