from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.multiagent.workflow import MultiAgentWorkflowRunner, MultiAgentWorkflowRunOptions

ROOT = Path(__file__).resolve().parents[1]


def test_sdlc_workflow_contract_runs_dry_run_and_consolidates_report() -> None:
    result = MultiAgentWorkflowRunner(ROOT).run(MultiAgentWorkflowRunOptions(workflow="sdlc_review", dry_run=True))

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    assert result.command == "multiagent workflow run"
    summary = result.data["summary"]
    assert summary["workflow_id"] == "sdlc-review"
    assert summary["workflow_definition_valid"] is True
    assert summary["workflow_definition_path"] == ".devpilot/workflows/sdlc_review.json"
    assert summary["workflow_report_consolidated"] is True
    assert summary["steps_total"] == 6
    assert summary["handoffs_total"] == 6
    assert summary["handoffs_traced_total"] == 6
    assert summary["policy_checks_total"] == 6
    assert summary["child_non_ok_total"] == 0
    assert summary["mutations_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert result.data["consolidated_report"]["automatic_remediation_enabled"] is False
    assert result.data["consolidated_report"]["recommendations"]


def test_sdlc_workflow_schema_contract_is_valid() -> None:
    schema = ROOT / "docs/schemas/multiagent_workflow.schema.json"
    workflow = ROOT / ".devpilot/workflows/sdlc_review.json"
    payload = json.loads(workflow.read_text(encoding="utf-8"))

    assert schema.exists()
    assert payload["workflow_id"] == "sdlc-review"
    assert payload["dry_run_required"] is True
    assert payload["report_only"] is True
    assert payload["autonomy_open"] is False
    assert payload["safety"]["mutations_allowed"] is False
    assert payload["safety"]["network_allowed"] is False
    assert len(payload["steps"]) == 6
    assert all(step["required_trace"] is True for step in payload["steps"])


def test_sdlc_workflow_without_dry_run_is_blocked() -> None:
    result = MultiAgentWorkflowRunner(ROOT).run(MultiAgentWorkflowRunOptions(workflow="sdlc_review", dry_run=False))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "MULTIAGENT_WORKFLOW_REQUIRES_DRY_RUN"
    assert result.data["summary"]["mutations_performed"] is False


def test_sdlc_workflow_unknown_definition_is_blocked() -> None:
    result = MultiAgentWorkflowRunner(ROOT).run(MultiAgentWorkflowRunOptions(workflow="autonomous_release", dry_run=True))

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.findings[0].id == "MULTIAGENT_WORKFLOW_DEFINITION_MISSING"


def test_sdlc_workflow_cli_json_and_report_are_parseable() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "devpilot_core",
            "multiagent",
            "workflow",
            "run",
            "--workflow",
            "sdlc_review",
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
    assert payload["command"] == "multiagent workflow run"
    assert payload["ok"] is True
    assert payload["data"]["summary"]["workflow_report_consolidated"] is True
    assert payload["data"]["summary"]["handoffs_traced_total"] == 6
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/multiagent_workflow_sdlc_review.json"
    assert reports["markdown"] == "outputs/reports/multiagent_workflow_sdlc_review.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()
