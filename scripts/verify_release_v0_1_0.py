#!/usr/bin/env python
"""Smoke verification helper for DevPilot Local internal release v0.1.0.

This script intentionally does not implement a new DevPilot core command. It is a
local operator helper for FUNC-SPRINT-19 and runs the same smoke commands
published in the release notes and runbook.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SMOKE_COMMANDS: list[list[str]] = [
    [sys.executable, "-m", "pytest", "-q"],
    [sys.executable, "-m", "devpilot_core", "--version"],
    [sys.executable, "-m", "devpilot_core", "workspace", "status", "--json"],
    [sys.executable, "-m", "devpilot_core", "standards", "status", "--json"],
    [sys.executable, "-m", "devpilot_core", "readiness-check", "--strict", "--json"],
    [sys.executable, "-m", "devpilot_core", "miasi", "validate", "--json"],
    [sys.executable, "-m", "devpilot_core", "eval", "run", "--json"],
    [sys.executable, "-m", "devpilot_core", "app", "contract", "--json"],
]


def _display_command(command: list[str]) -> str:
    return " ".join("python" if part == sys.executable else part for part in command)


def run_smoke_commands() -> dict[str, Any]:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    current_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not current_pythonpath else src_path + os.pathsep + current_pythonpath

    results: list[dict[str, Any]] = []
    for command in SMOKE_COMMANDS:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        results.append(
            {
                "command": _display_command(command),
                "returncode": completed.returncode,
                "ok": completed.returncode == 0,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
            }
        )

    ok = all(item["ok"] for item in results)
    return {
        "release": "v0.1.0",
        "sprint": "FUNC-SPRINT-19",
        "ok": ok,
        "commands_total": len(results),
        "commands_passed": sum(1 for item in results if item["ok"]),
        "commands_failed": sum(1 for item in results if not item["ok"]),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify DevPilot Local internal release v0.1.0.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args(argv)

    payload = run_smoke_commands()
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if payload["ok"] else "BLOCK"
        print(f"DevPilot Local release v0.1.0 smoke verification: {status}")
        for item in payload["results"]:
            marker = "PASS" if item["ok"] else "FAIL"
            print(f"[{marker}] {item['command']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
