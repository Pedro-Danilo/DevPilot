from __future__ import annotations


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
