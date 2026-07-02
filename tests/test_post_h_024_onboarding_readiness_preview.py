from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from devpilot_core.onboarding.readiness_preview import (
    ONBOARDING_READINESS_PREVIEW_SCHEMA_ID,
    OnboardingReadinessPreviewOptions,
    OnboardingReadinessPreviewer,
)
from devpilot_core.schemas import SchemaValidator
from devpilot_core.workspace.bootstrap import ProjectBootstrapOptions, ProjectBootstrapPlanner

ROOT = Path(__file__).resolve().parents[1]
TARGET_BASE = ROOT / "outputs" / "test_post_h_024_d"
PROJECT_ID = "ventas-micro-local"
PROJECT_NAME = "Sistema agent-assisted de ventas e inventario para microemprendimientos locales"


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def clean_target() -> None:
    shutil.rmtree(TARGET_BASE, ignore_errors=True)


def bootstrap_target(target_rel: str) -> Path:
    result = ProjectBootstrapPlanner(ROOT).run(
        ProjectBootstrapOptions(
            project_id=PROJECT_ID,
            project_name=PROJECT_NAME,
            target_root=target_rel,
            execute=True,
            write_report=False,
        )
    )
    assert result.ok, result.to_dict()
    return ROOT / target_rel


def test_onboarding_readiness_preview_reports_pending_items_without_false_success() -> None:
    clean_target()
    target_rel = "outputs/test_post_h_024_d/preview-project"
    bootstrap_target(target_rel)

    result = OnboardingReadinessPreviewer(ROOT).run(
        OnboardingReadinessPreviewOptions(
            target_root=target_rel,
            project_id=PROJECT_ID,
            project_name=PROJECT_NAME,
            write_report=False,
        )
    )

    assert result.ok, result.to_dict()
    assert result.command == "workspace readiness-preview"
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["status"] == "warning"
    assert summary["target_exists"] is True
    assert summary["pending_total"] > 0
    assert summary["block_total"] == 0
    assert summary["miasi_required"] is True
    assert summary["miasi_missing_reported_as_pending"] is True
    assert summary["readiness_success_overclaimed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert report["schema_id"] == ONBOARDING_READINESS_PREVIEW_SCHEMA_ID
    assert report["safety"]["remote_execution_used"] is False
    assert report["safety"]["connector_write_used"] is False
    assert report["safety"]["plugin_execution_used"] is False
    assert {phase["phase_id"] for phase in report["phases"]} >= {"workspace", "checklist", "standards", "miasi", "readiness"}
    assert any(item["phase_id"] == "readiness" for item in report["pending_items"])
    assert any(item["phase_id"] == "miasi" for item in report["pending_items"])


def test_onboarding_readiness_preview_reports_missing_miasi_as_pending_not_success() -> None:
    clean_target()
    target_rel = "outputs/test_post_h_024_d/missing-miasi-project"
    target = bootstrap_target(target_rel)
    shutil.rmtree(target / ".devpilot" / "miasi")

    result = OnboardingReadinessPreviewer(ROOT).run(
        OnboardingReadinessPreviewOptions(target_root=target_rel, project_id=PROJECT_ID, project_name=PROJECT_NAME)
    )

    assert result.ok, result.to_dict()
    report = result.data["report"]
    miasi_phase = next(phase for phase in report["phases"] if phase["phase_id"] == "miasi")
    assert miasi_phase["status"] == "pending"
    assert result.data["summary"]["miasi_missing_reported_as_pending"] is True
    assert result.data["summary"]["readiness_success_overclaimed"] is False
    assert any(item["source_validator"] == "miasi-inventory" for item in report["pending_items"])
    assert not any(check["check_id"].startswith("miasi-file:") and check["status"] == "pass" for check in miasi_phase["checks"])


def test_workspace_readiness_preview_cli_writes_schema_valid_report() -> None:
    clean_target()
    target_rel = "outputs/test_post_h_024_d/cli-preview-project"
    output_json = "outputs/test_post_h_024_d/cli_onboarding_readiness_preview_report.json"
    output_md = "outputs/test_post_h_024_d/cli_onboarding_readiness_preview_report.md"
    bootstrap_target(target_rel)
    cmd = [
        sys.executable,
        "-m",
        "devpilot_core",
        "workspace",
        "readiness-preview",
        "--target-root",
        target_rel,
        "--project-id",
        PROJECT_ID,
        "--project-name",
        PROJECT_NAME,
        "--json",
        "--write-report",
        "--output-json",
        output_json,
        "--output-markdown",
        output_md,
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "workspace readiness-preview"
    assert payload["data"]["summary"]["status"] == "warning"
    assert payload["data"]["summary"]["report_written"] is True
    assert (ROOT / output_json).is_file()
    assert (ROOT / output_md).is_file()
    schema_result = SchemaValidator(ROOT).validate(schema="OnboardingReadinessPreviewReport", instance=output_json)
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_024_d_governance_artifacts_are_synchronized() -> None:
    manifest = read_json("docs/post_h_024_d_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    state = read_json(".devpilot/project_state.json")
    schema_catalog = read_json("docs/schemas/schema_catalog.json")
    backlog = read_text("docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md")
    implementation = read_text("docs/POST-H-024_operator_onboarding_bootstrap.md")
    report = read_text("docs/audits/post_h_024_d_onboarding_readiness_preview_report.md")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert manifest["post_h_id"] == "POST-H-024"
    assert manifest["micro_sprint"] == "POST-H-024-D"
    assert manifest["status"] == "implemented-initial"
    assert manifest["next_micro_sprint"] == "POST-H-024-E"
    assert "src/devpilot_core/onboarding/readiness_preview.py" in manifest["created_files"]
    assert "docs/schemas/onboarding_readiness_preview_report.schema.json" in manifest["created_files"]
    assert "tests/test_post_h_024_onboarding_readiness_preview.py" in manifest["created_files"]
    assert manifest["read_only"] is True
    assert manifest["no_remote_execution_enabled"] is True
    assert manifest["no_external_apis_used"] is True
    assert manifest["no_connector_write_enabled"] is True
    assert manifest["no_plugin_execution_enabled"] is True

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    expected = {
        "POST-H-024-D-ONBOARDING-READINESS-PREVIEW-SCHEMA",
        "POST-H-024-D-ONBOARDING-READINESS-PREVIEW-MODULE",
        "POST-H-024-D-ONBOARDING-READINESS-PREVIEW-REPORT",
        "POST-H-024-D-MANIFEST",
        "POST-H-024-D-ONBOARDING-READINESS-PREVIEW-TEST",
    }
    assert expected <= doc_ids
    assert source_registry["project_state_snapshot"]["current_micro_sprint"] == "POST-H-024-D"
    assert source_registry["project_state_snapshot"]["next_micro_sprint"] == "POST-H-024-E"
    assert source_registry["project_state_snapshot"]["post_h_024_readiness_preview_available"] is True
    assert source_registry["project_state_snapshot"]["post_h_024_onboarding_quality_gate_available"] is False

    assert "post-h-024-onboarding-readiness-preview" in {item["contract_id"] for item in tcr_v1["contracts"]}
    assert "post-h-024-onboarding-readiness-preview" in {item["contract_id"] for item in tcr_v2["contracts"]}
    schema_ids = {item["schema_id"] for item in schema_catalog["schemas"]}
    assert ONBOARDING_READINESS_PREVIEW_SCHEMA_ID in schema_ids

    assert state["current_micro_sprint"] == "POST-H-024-D"
    assert state["next_micro_sprint"] == "POST-H-024-E"
    assert state["post_h_024_current_micro_sprint"] == "POST-H-024-D"
    assert state["post_h_024_next_micro_sprint"] == "POST-H-024-E"
    assert state["post_h_024_operator_playbook_available"] is True
    assert state["post_h_024_templates_available"] is True
    assert state["post_h_024_bootstrap_workflow_available"] is True
    assert state["post_h_024_project_bootstrap_report_available"] is True
    assert state["post_h_024_readiness_preview_available"] is True
    assert state["post_h_024_onboarding_quality_gate_available"] is False
    assert state["post_h_024_network_used"] is False
    assert state["post_h_024_external_api_used"] is False
    assert state["post_h_024_remote_execution_enabled"] is False

    for text in (backlog, implementation):
        assert 'current_micro_sprint: "POST-H-024-D"' in text
        assert 'next_micro_sprint: "POST-H-024-E"' in text
        assert "POST-H-024-D" in text
        assert "implemented-initial" in text
        assert "readiness-preview-only" in text

    assert "workspace readiness-preview" in report
    assert "MIASI faltante" in report or "Missing MIASI" in report
    assert "POST-H-024-D — Onboarding validation y readiness preview" in readme
    assert "POST-H-024-D — Onboarding validation y readiness preview" in runbook
    assert "Siguiente micro-sprint: `POST-H-024-E — Quality gate y proyecto piloto fixture`" in readme
    assert "post-h-024-d" in changelog
