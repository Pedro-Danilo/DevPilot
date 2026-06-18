from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_agent_runs_in_dry_run_and_reports_evidence() -> None:
    from devpilot_core.agents import AgentRuntime
    from devpilot_core.cli_models import ExitCode

    result = AgentRuntime(ROOT).run("release-assistant", dry_run=True)

    assert result.ok is True
    assert result.exit_code == ExitCode.PASS
    data = result.data
    assert data["agent"]["agent_id"] == "release.assistant"
    assert data["agent"]["dry_run"] is True
    assert data["summary"]["tool_calls_total"] >= 7
    assert data["metadata"]["policy_engine_used"] is True
    assert data["metadata"]["miasi_runtime_required"] is True
    assert data["metadata"]["publishes_artifacts"] is False
    assert data["metadata"]["deploys_artifacts"] is False
    assert data["metadata"]["git_tagging_performed"] is False
    report = data["artifacts"]["release_assistant_report"]
    assert report["release_ready"] is True
    assert report["phase_g_closure_candidate"] is True
    assert all(item["status"] == "PASS" for item in report["checklist"])


def test_release_agent_blocks_execute_mode() -> None:
    from devpilot_core.agents import AgentRuntime
    from devpilot_core.cli_models import ExitCode

    result = AgentRuntime(ROOT).run("release-assistant", dry_run=False)

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert any(finding.id == "RELEASE_AGENT_EXECUTE_BLOCKED" for finding in result.findings)


def test_release_agent_cli_json_and_report_are_parseable() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devpilot_core", "agent", "run", "release-assistant", "--dry-run", "--json", "--write-report"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["command"] == "agent run"
    assert payload["ok"] is True
    assert payload["data"]["agent"]["agent_id"] == "release.assistant"
    assert payload["data"]["artifacts"]["release_assistant_report"]["release_ready"] is True
    reports = payload["data"].get("reports")
    assert reports["json"] == "outputs/reports/agent_run_release_assistant.json"
    assert reports["markdown"] == "outputs/reports/agent_run_release_assistant.md"
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()


def test_quality_gate_release_profile_passes() -> None:
    from devpilot_core.quality import QualityGate, QualityGateOptions

    result = QualityGate(ROOT, options=QualityGateOptions(profile="release")).run()

    assert result.ok is True
    summary = result.data["summary"]
    assert summary["profile"] == "release"
    assert summary["subgates_failed"] == 0
    subgate_ids = {item["id"] for item in result.data["subgates"]}
    for expected in [
        "release-manifest-static",
        "release-changelog-static",
        "release-package-dry-run",
        "release-sbom-static",
        "release-install-upgrade-static",
    ]:
        assert expected in subgate_ids
