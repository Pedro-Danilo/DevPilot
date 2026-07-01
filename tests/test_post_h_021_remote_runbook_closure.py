from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_remote_runner_design_runbook_declares_design_only_closure() -> None:
    runbook = read_text("docs/05_operations/remote_runner_design_runbook.md")

    required_fragments = [
        'status: "approved"',
        'implementation_status: "implemented-initial"',
        "remote registry existe != remote runner habilitado",
        "remote quality gate PASS != autorización de ejecución remota",
        "remote_execution_allowed=false",
        "remote_runner_enabled=false",
        "remote_execution_used=false",
        "network_used=false",
        "external_api_used=false",
        "credentials_required=false",
        "secrets_read=false",
        "POST-H-022 enterprise deployment threat model aprobado",
        "POST-H-023 secure transport design aprobado",
        "ADR futura explícita",
        "quality gate remoto dedicado",
    ]

    for fragment in required_fragments:
        assert fragment in runbook


def test_post_h_021_backlog_and_implementation_are_closed_and_synchronized() -> None:
    backlog = read_text("docs/backlogs/POST-H-021_remote_runner_adr2.md")
    implementation = read_text("docs/POST-H-021_remote_runner_adr2.md")
    state = read_json(".devpilot/project_state.json")

    for text in (backlog, implementation):
        assert 'implementation_status: "closed"' in text
        assert 'current_micro_sprint: "POST-H-021-E"' in text
        assert 'next_micro_sprint: "POST-H-022"' in text
        assert "POST-H-021-E — Runbook y cierre" in text
        assert "POST-H-021 queda cerrado" in text

    assert state["last_completed_sprint"] == "POST-H-021"
    assert state["next_sprint"] == "POST-H-022"
    assert state["current_micro_sprint"] == "POST-H-021-E"
    assert state["next_micro_sprint"] == "POST-H-022"
    assert state["post_h_021_current_micro_sprint"] == "POST-H-021-E"
    assert state["post_h_021_next_micro_sprint"] == "POST-H-022"
    assert state["post_h_021_closed"] is True
    assert state["remote_runner_design_runbook_path"] == "docs/05_operations/remote_runner_design_runbook.md"
    assert state["remote_execution_enabled"] is False
    assert state["remote_runner_enabled"] is False
    assert state["remote_execution_allowed"] is False


def test_post_h_021_closure_manifest_and_reports_are_registered() -> None:
    manifest = read_json("docs/post_h_021_e_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert manifest["micro_sprint"] == "POST-H-021-E"
    assert manifest["closure"]["backlog_closed"] is True
    assert manifest["closure"]["next_sprint"] == "POST-H-022"
    assert manifest["remote_execution_enabled"] is False
    assert "docs/05_operations/remote_runner_design_runbook.md" in manifest["created_files"]
    assert "tests/test_post_h_021_remote_runbook_closure.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    assert "POST-H-021-REMOTE-RUNNER-DESIGN-RUNBOOK" in doc_ids
    assert "POST-H-021-E-REMOTE-RUNNER-CLOSURE-REPORT" in doc_ids
    assert "POST-H-021-E-MANIFEST" in doc_ids

    contract_ids = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-021-remote-runbook-closure" in contract_ids
    assert "post-h-021-remote-runbook-closure" in contract_ids_v2


def test_readme_runbook_and_changelog_track_post_h_021_e() -> None:
    readme = read_text("README.md")
    operations_runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    for text in (readme, operations_runbook):
        assert "POST-H-021-E — Runbook y cierre" in text
        assert "Último hito cerrado: `POST-H-021`" in text
        assert "Siguiente hito: `POST-H-022`" in text

    assert "post-h-021-e" in changelog
    assert "Remote Runner ADR-2" in changelog
    assert "remote_execution_allowed=false" in changelog

