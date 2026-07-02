from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from devpilot_core.schemas import SchemaValidator
from devpilot_core.workspace.bootstrap import (
    DEFAULT_BOOTSTRAP_OUTPUT_JSON,
    ProjectBootstrapOptions,
    ProjectBootstrapPlanner,
)

ROOT = Path(__file__).resolve().parents[1]
TARGET_BASE = ROOT / "outputs" / "test_post_h_024_c"
PROJECT_ID = "ventas-micro-local"
PROJECT_NAME = "Sistema agent-assisted de ventas e inventario para microemprendimientos locales"


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def clean_target() -> None:
    shutil.rmtree(TARGET_BASE, ignore_errors=True)


def test_bootstrap_dry_run_builds_bounded_plan_without_workspace_mutation() -> None:
    clean_target()
    target_rel = "outputs/test_post_h_024_c/dry-run-project"
    result = ProjectBootstrapPlanner(ROOT).run(
        ProjectBootstrapOptions(
            project_id=PROJECT_ID,
            project_name=PROJECT_NAME,
            target_root=target_rel,
            execute=False,
            write_report=False,
        )
    )

    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    report = result.data["report"]
    assert summary["mode"] == "dry-run"
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["files_total"] == 10
    assert summary["files_existing_total"] == 0
    assert not (ROOT / target_rel).exists()
    assert report["schema_id"] == "SCHEMA-DEVPL-PROJECT-BOOTSTRAP-REPORT-V1"
    assert report["safety"]["overwrite_allowed"] is False
    assert {item["kind"] for item in report["planned_files"]} == {"workspace-project-yaml", "markdown-artifact", "miasi-json"}
    assert all(item["path"].startswith(target_rel) for item in report["planned_files"])


def test_bootstrap_write_report_generates_schema_valid_project_bootstrap_report() -> None:
    clean_target()
    output_json = "outputs/test_post_h_024_c/project_bootstrap_report.json"
    output_md = "outputs/test_post_h_024_c/project_bootstrap_report.md"
    result = ProjectBootstrapPlanner(ROOT).run(
        ProjectBootstrapOptions(
            project_id=PROJECT_ID,
            project_name=PROJECT_NAME,
            target_root="outputs/test_post_h_024_c/report-project",
            execute=False,
            write_report=True,
            output_json=output_json,
            output_markdown=output_md,
        )
    )

    assert result.ok, result.to_dict()
    assert result.data["summary"]["report_written"] is True
    assert (ROOT / output_json).is_file()
    assert (ROOT / output_md).is_file()
    report = read_json(output_json)
    assert report["mode"] == "dry-run"
    assert report["safety"]["mutations_performed"] is False
    assert report["safety"]["network_used"] is False
    schema_result = SchemaValidator(ROOT).validate(schema="ProjectBootstrapReport", instance=output_json)
    assert schema_result.ok, schema_result.to_dict()


def test_bootstrap_execute_materializes_files_but_refuses_overwrite_by_default() -> None:
    clean_target()
    target_rel = "outputs/test_post_h_024_c/execute-project"
    planner = ProjectBootstrapPlanner(ROOT)
    first = planner.run(
        ProjectBootstrapOptions(
            project_id=PROJECT_ID,
            project_name=PROJECT_NAME,
            target_root=target_rel,
            execute=True,
            write_report=False,
        )
    )
    assert first.ok, first.to_dict()
    target = ROOT / target_rel
    assert (target / ".devpilot" / "project.yaml").is_file()
    assert (target / "docs" / "00_product" / "product_vision.md").is_file()
    assert (target / ".devpilot" / "miasi" / "agent_registry.json").is_file()
    assert first.data["summary"]["mode"] == "execute"
    assert first.data["summary"]["mutations_performed"] is True
    assert first.data["summary"]["source_mutations_performed"] is False

    product_doc = (target / "docs" / "00_product" / "product_vision.md").read_text(encoding="utf-8")
    assert 'status: "draft"' in product_doc
    assert 'created_by: "POST-H-024-C"' in product_doc
    assert PROJECT_NAME in product_doc
    assert "{{" not in product_doc

    second = planner.run(
        ProjectBootstrapOptions(
            project_id=PROJECT_ID,
            project_name=PROJECT_NAME,
            target_root=target_rel,
            execute=True,
            write_report=False,
        )
    )
    assert not second.ok
    assert second.exit_code.value == 2
    assert any(finding.id == "PROJECT_BOOTSTRAP_OVERWRITE_BLOCKED" for finding in second.findings)


def test_workspace_bootstrap_cli_dry_run_and_report_contract() -> None:
    clean_target()
    output_json = "outputs/test_post_h_024_c/cli_project_bootstrap_report.json"
    cmd = [
        sys.executable,
        "-m",
        "devpilot_core",
        "workspace",
        "bootstrap",
        "--project-id",
        PROJECT_ID,
        "--project-name",
        PROJECT_NAME,
        "--target-root",
        "outputs/test_post_h_024_c/cli-project",
        "--dry-run",
        "--json",
        "--write-report",
        "--output-json",
        output_json,
        "--output-markdown",
        "outputs/test_post_h_024_c/cli_project_bootstrap_report.md",
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    assert completed.returncode == 0, completed.stderr + completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["ok"] is True
    assert payload["command"] == "workspace bootstrap"
    assert payload["data"]["summary"]["mode"] == "dry-run"
    assert payload["data"]["summary"]["report_written"] is True
    assert (ROOT / output_json).is_file()
    schema_result = SchemaValidator(ROOT).validate(schema="ProjectBootstrapReport", instance=output_json)
    assert schema_result.ok, schema_result.to_dict()


def test_post_h_024_c_governance_artifacts_are_synchronized() -> None:
    manifest = read_json("docs/post_h_024_c_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    state = read_json(".devpilot/project_state.json")
    backlog = read_text("docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md")
    implementation = read_text("docs/POST-H-024_operator_onboarding_bootstrap.md")
    report = read_text("docs/audits/post_h_024_c_project_bootstrap_report.md")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert manifest["post_h_id"] == "POST-H-024"
    assert manifest["micro_sprint"] == "POST-H-024-C"
    assert manifest["status"] == "implemented-initial"
    assert manifest["next_micro_sprint"] == "POST-H-024-D"
    assert "src/devpilot_core/workspace/bootstrap.py" in manifest["created_files"]
    assert "docs/schemas/project_bootstrap_report.schema.json" in manifest["created_files"]
    assert "tests/test_post_h_024_project_bootstrap.py" in manifest["created_files"]
    assert manifest["no_remote_execution_enabled"] is True
    assert manifest["no_external_apis_used"] is True
    assert manifest["no_connector_write_enabled"] is True
    assert manifest["no_plugin_execution_enabled"] is True

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    expected = {
        "POST-H-024-C-PROJECT-BOOTSTRAP-SCHEMA",
        "POST-H-024-C-WORKSPACE-BOOTSTRAP-MODULE",
        "POST-H-024-C-PROJECT-BOOTSTRAP-TEST",
        "POST-H-024-C-PROJECT-BOOTSTRAP-REPORT",
        "POST-H-024-C-MANIFEST",
    }
    assert expected <= doc_ids
    assert source_registry["project_state_snapshot"]["current_micro_sprint"] == "POST-H-024-D"
    assert source_registry["project_state_snapshot"]["next_micro_sprint"] == "POST-H-024-E"
    assert source_registry["project_state_snapshot"]["post_h_024_bootstrap_workflow_available"] is True

    assert "post-h-024-project-bootstrap" in {item["contract_id"] for item in tcr_v1["contracts"]}
    assert "post-h-024-project-bootstrap" in {item["contract_id"] for item in tcr_v2["contracts"]}

    assert state["current_micro_sprint"] == "POST-H-024-D"
    assert state["next_micro_sprint"] == "POST-H-024-E"
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
        assert "POST-H-024-C" in text
        assert "implemented-initial" in text
        assert "dry-run" in text

    assert "workspace bootstrap" in report
    assert "POST-H-024-C — Bootstrap workflow dry-run" in readme
    assert "POST-H-024-C — Bootstrap workflow dry-run" in runbook
    assert "Siguiente micro-sprint: `POST-H-024-E — Quality gate y proyecto piloto fixture`" in readme
    assert "post-h-024-c" in changelog
