from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from devpilot_core.onboarding import (
    DEFAULT_ONBOARDING_PILOT_FIXTURE,
    ONBOARDING_BOOTSTRAP_READY_SUBGATE,
    OnboardingBootstrapReadyGate,
)
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID = "ventas-micro-local"
PROJECT_NAME = "Sistema agent-assisted de ventas e inventario para microemprendimientos locales"


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def clean_target() -> None:
    shutil.rmtree(ROOT / "outputs" / "test_post_h_024_e_gate", ignore_errors=True)


def test_onboarding_bootstrap_ready_gate_uses_fixture_and_dry_run_without_runtime_artifacts() -> None:
    clean_target()

    result = OnboardingBootstrapReadyGate(ROOT).run()

    assert result.ok, result.to_dict()
    assert result.command == f"quality {ONBOARDING_BOOTSTRAP_READY_SUBGATE}"
    summary = result.data["summary"]
    assert summary["quality_gate_subgate"] == ONBOARDING_BOOTSTRAP_READY_SUBGATE
    assert summary["onboarding_bootstrap_ready"] is True
    assert summary["fixture_path"] == DEFAULT_ONBOARDING_PILOT_FIXTURE
    assert summary["fixture_loaded"] is True
    assert summary["templates_ok"] is True
    assert summary["bootstrap_dry_run_ok"] is True
    assert summary["bootstrap_mode"] == "dry-run"
    assert summary["planned_files_total"] >= 10
    assert summary["files_would_write_total"] >= 10
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["remote_execution_used"] is False
    assert summary["connector_write_used"] is False
    assert summary["plugin_execution_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["runtime_artifacts_versionable"] is False
    assert not (ROOT / "outputs" / "test_post_h_024_e_gate" / "pilot-project" / ".devpilot" / "project.yaml").exists()


def test_onboarding_bootstrap_ready_gate_blocks_when_templates_are_missing(tmp_path: Path) -> None:
    fake_root = tmp_path / "fake-devpilot"
    shutil.copytree(ROOT / "docs" / "templates" / "new_project", fake_root / "docs" / "templates" / "new_project")
    shutil.copytree(ROOT / "docs" / "schemas", fake_root / "docs" / "schemas")
    fixture_path = fake_root / DEFAULT_ONBOARDING_PILOT_FIXTURE
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text((ROOT / DEFAULT_ONBOARDING_PILOT_FIXTURE).read_text(encoding="utf-8"), encoding="utf-8")
    missing_template = fake_root / "docs" / "templates" / "new_project" / "product_vision.template.md"
    missing_template.unlink()

    result = OnboardingBootstrapReadyGate(fake_root).run()

    assert not result.ok
    assert result.data["summary"]["templates_ok"] is False
    assert result.data["summary"]["template_errors_total"] >= 1
    assert any(finding.id == "ONBOARDING_BOOTSTRAP_READY_TEMPLATES_INVALID" for finding in result.findings)


def test_quality_gate_hardening_includes_onboarding_bootstrap_ready_subgate() -> None:
    gate = QualityGate(ROOT, options=QualityGateOptions(profile="hardening"))

    subgate_ids = [subgate.id for subgate in gate._subgates()]

    assert ONBOARDING_BOOTSTRAP_READY_SUBGATE in subgate_ids


def test_post_h_024_e_governance_artifacts_are_synchronized() -> None:
    manifest = read_json("docs/post_h_024_e_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    state = read_json(".devpilot/project_state.json")
    backlog = read_text("docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md")
    implementation = read_text("docs/POST-H-024_operator_onboarding_bootstrap.md")
    report = read_text("docs/audits/post_h_024_e_onboarding_quality_gate_report.md")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert manifest["post_h_id"] == "POST-H-024"
    assert manifest["micro_sprint"] == "POST-H-024-E"
    assert manifest["status"] == "implemented-initial"
    assert manifest["next_sprint"] == "POST-H-025"
    assert "src/devpilot_core/onboarding/quality_gate.py" in manifest["created_files"]
    assert DEFAULT_ONBOARDING_PILOT_FIXTURE in manifest["created_files"]
    assert "tests/test_post_h_024_onboarding_quality_gate.py" in manifest["created_files"]
    assert manifest["read_only"] is True
    assert manifest["dry_run"] is True
    assert manifest["no_external_apis_used"] is True
    assert manifest["no_remote_execution_enabled"] is True

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    expected = {
        "POST-H-024-E-ONBOARDING-QUALITY-GATE-MODULE",
        "POST-H-024-E-PILOT-FIXTURE",
        "POST-H-024-E-ONBOARDING-QUALITY-GATE-REPORT",
        "POST-H-024-E-MANIFEST",
        "POST-H-024-E-ONBOARDING-QUALITY-GATE-TEST",
    }
    assert expected <= doc_ids
    assert source_registry["project_state_snapshot"]["current_micro_sprint"] == "POST-H-024-E"
    assert source_registry["project_state_snapshot"]["next_micro_sprint"] == "POST-H-025"
    assert source_registry["project_state_snapshot"]["post_h_024_onboarding_quality_gate_available"] is True

    assert "post-h-024-onboarding-bootstrap-ready" in {item["contract_id"] for item in tcr_v1["contracts"]}
    assert "post-h-024-onboarding-bootstrap-ready" in {item["contract_id"] for item in tcr_v2["contracts"]}

    assert state["current_micro_sprint"] == "POST-H-024-E"
    assert state["next_micro_sprint"] == "POST-H-025"
    assert state["post_h_024_current_micro_sprint"] == "POST-H-024-E"
    assert state["post_h_024_next_micro_sprint"] == "POST-H-025"
    assert state["post_h_024_onboarding_quality_gate_available"] is True
    assert state["post_h_024_onboarding_quality_gate_subgate"] == ONBOARDING_BOOTSTRAP_READY_SUBGATE
    assert state["post_h_024_pilot_fixture_path"] == DEFAULT_ONBOARDING_PILOT_FIXTURE
    assert state["post_h_024_closed"] is True
    assert state["post_h_024_network_used"] is False
    assert state["post_h_024_external_api_used"] is False
    assert state["post_h_024_remote_execution_enabled"] is False

    for text in (backlog, implementation):
        assert 'current_micro_sprint: "POST-H-024-E"' in text
        assert 'next_micro_sprint: "POST-H-025"' in text
        assert "POST-H-024-E" in text
        assert "implemented-initial" in text
        assert "quality-gate-fixture-only" in text
        assert "onboarding-bootstrap-ready" in text

    assert "onboarding-bootstrap-ready" in report
    assert "Quality gate y proyecto piloto fixture" in readme
    assert "Quality gate y proyecto piloto fixture" in runbook
    assert "POST-H-024 queda cerrado" in readme
    assert "post-h-024-e" in changelog
