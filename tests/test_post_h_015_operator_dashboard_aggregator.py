from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.cli_models import ExitCode
from devpilot_core.portfolio import OperatorDashboardAggregator, OperatorDashboardAggregatorOptions
from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def test_post_h_015_b_operator_dashboard_aggregates_local_sources_read_only() -> None:
    result = OperatorDashboardAggregator(
        ROOT,
        OperatorDashboardAggregatorOptions(generated_at_utc="2026-06-28T00:00:00Z"),
    ).build()

    assert result.ok, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    snapshot = result.data["snapshot"]
    assert summary["created_by"] == "POST-H-015-B"
    assert summary["required_sources_missing_total"] == 0
    assert summary["read_only"] is True
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert snapshot["schema_id"] == "SCHEMA-DEVPL-OPERATOR-DASHBOARD-SNAPSHOT-V1"
    assert snapshot["snapshot_id"] == "operator-dashboard-20260628T000000Z"
    assert snapshot["created_by"] == "POST-H-015-B"
    assert snapshot["status"] in {"pass", "warn"}
    assert set(snapshot["sections"]) == set(json.loads((ROOT / ".devpilot/operator/dashboard_config.json").read_text(encoding="utf-8"))["required_sections"])
    project_state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert snapshot["sections"]["roadmap"]["metrics"]["current_micro_sprint"] == project_state["current_micro_sprint"]
    assert all(section["source_refs"] for section in snapshot["sections"].values())
    assert all(action["dry_run"] is True for action in snapshot["recommended_next_actions"])


def test_post_h_015_b_operator_dashboard_write_report_validates_schema() -> None:
    result = OperatorDashboardAggregator(
        ROOT,
        OperatorDashboardAggregatorOptions(generated_at_utc="2026-06-28T00:00:00Z", write_report=True),
    ).build()

    assert result.ok, result.to_dict()
    reports = result.data["reports"]
    assert reports == {
        "json": "outputs/reports/operator_dashboard_snapshot.json",
        "markdown": "outputs/reports/operator_dashboard_snapshot.md",
    }
    assert (ROOT / reports["json"]).exists()
    assert (ROOT / reports["markdown"]).exists()

    schema_result = SchemaValidator(ROOT).validate(
        schema="OperatorDashboardSnapshot",
        instance=reports["json"],
    )
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_015_b_operator_dashboard_blocks_missing_required_source(tmp_path: Path) -> None:
    scratch = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        scratch,
        ignore=shutil.ignore_patterns(".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "outputs"),
    )
    (scratch / ".devpilot/project_state.json").unlink()

    result = OperatorDashboardAggregator(
        scratch,
        OperatorDashboardAggregatorOptions(generated_at_utc="2026-06-28T00:00:00Z"),
    ).build()

    assert result.ok is False
    assert result.exit_code == ExitCode.BLOCK
    assert result.data["summary"]["required_sources_missing_total"] >= 1
    assert any(finding.id == "OPERATOR_DASHBOARD_REQUIRED_SOURCE_MISSING" for finding in result.findings)
