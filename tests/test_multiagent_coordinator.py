from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from devpilot_core.cli_models import ExitCode
from devpilot_core.multiagent import MultiAgentCoordinator, MultiAgentRunOptions
from devpilot_core.multiagent import coordinator as coordinator_module

ROOT = Path(__file__).resolve().parents[1]


def test_multiagent_repo_review_dry_run_has_explicit_traced_handoffs() -> None:
    result = MultiAgentCoordinator(ROOT).run(MultiAgentRunOptions(workflow="repo-review", dry_run=True))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["workflow_id"] == "repo-review"
    assert summary["dry_run"] is True
    assert summary["steps_total"] == 3
    assert summary["handoffs_total"] == 3
    assert summary["handoffs_explicit_total"] == 3
    assert summary["handoffs_traced_total"] == 3
    assert summary["policy_checks_total"] == 3
    assert summary["mutations_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert [step["agent_id"] for step in result.data["steps"]] == [
        "repo.analysis",
        "code.review",
        "security.agent",
    ]
    assert all(step["allowed_runtime_status"] is True for step in result.data["steps"])
    assert all(handoff["explicit"] is True for handoff in result.data["handoffs"])
    assert all(handoff["trace_event_emitted"] is True for handoff in result.data["handoffs"])


def test_multiagent_run_without_dry_run_is_blocked() -> None:
    result = MultiAgentCoordinator(ROOT).run(MultiAgentRunOptions(workflow="repo-review", dry_run=False))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "MULTIAGENT_REQUIRES_DRY_RUN"
    assert result.data["summary"]["mutations_performed"] is False


def test_multiagent_unknown_workflow_is_blocked() -> None:
    result = MultiAgentCoordinator(ROOT).run(MultiAgentRunOptions(workflow="free-form-autonomous", dry_run=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "MULTIAGENT_WORKFLOW_UNKNOWN"


def test_multiagent_blocks_planned_or_future_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        coordinator_module._WORKFLOWS,
        "unsafe-future-release",
        [
            {
                "step_id": "future-release",
                "agent_id": "release.agent",
                "reason": "Future release agent must not be used by Sprint 90 coordinator.",
            }
        ],
    )

    result = MultiAgentCoordinator(ROOT).run(MultiAgentRunOptions(workflow="unsafe-future-release", dry_run=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "MULTIAGENT_WORKFLOW_AGENT_STATUS_BLOCKED" for finding in result.findings)
    assert result.data["summary"]["mutations_performed"] is False


def test_multiagent_cli_json_and_report_are_parseable() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "multiagent",
            "run",
            "--workflow",
            "repo-review",
            "--dry-run",
            "--json",
            "--write-report",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "multiagent run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["handoffs_traced_total"] == 3
    assert payload["data"]["summary"]["destructive_actions_executed"] is False
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/multiagent_repo_review.json"
    assert reports["markdown"] == "outputs/reports/multiagent_repo_review.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()
