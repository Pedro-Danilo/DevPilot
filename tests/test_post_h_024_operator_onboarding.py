from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read_text(path))


def test_operator_onboarding_playbook_is_approved_and_self_contained() -> None:
    playbook = read_text("docs/05_operations/operator_onboarding_playbook.md")

    required_fragments = [
        'doc_id: "POST-H-024-A-OPERATOR-ONBOARDING-PLAYBOOK"',
        'status: "approved"',
        'implementation_status: "implemented-initial"',
        'preliminary: true',
        'local_first: true',
        'dry_run: true',
        'no_remote_execution_enabled: true',
        'no_external_apis_used: true',
        'no_connector_write_enabled: true',
        'no_plugin_execution_enabled: true',
        'idea → workspace → docs → readiness → backlog',
        'Sistema agent-assisted de ventas e inventario para microemprendimientos locales',
        'python -m devpilot_core workspace status --json',
        'python -m devpilot_core workspace init',
        'python -m devpilot_core readiness-check --strict --json',
        'python -m devpilot_core miasi-required --json',
        'python -m devpilot_core miasi validate --json',
        'python -m devpilot_core docs-governance validate --json',
        'POST-H-024-B: templates Markdown/JSON',
        'POST-H-024-C: workflow bootstrap dry-run/execute seguro',
        'BLOCK si el operador necesita instrucciones no documentadas',
    ]
    for fragment in required_fragments:
        assert fragment in playbook

    assert 'remote execution, connector write, plugin execution o remote execution' not in playbook.lower()
    assert 'no_remote_execution_enabled=true' in playbook
    assert 'no_external_apis_used=true' in playbook


def test_post_h_024_backlog_and_implementation_are_approved_for_a_only() -> None:
    backlog = read_text("docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md")
    implementation = read_text("docs/POST-H-024_operator_onboarding_bootstrap.md")
    report = read_text("docs/audits/post_h_024_a_operator_playbook_report.md")

    for text in (backlog, implementation):
        assert 'status: "approved"' in text
        assert 'approval: "approved_by_owner"' in text
        assert 'current_micro_sprint: "POST-H-024-A"' in text
        assert 'next_micro_sprint: "POST-H-024-B"' in text

    assert 'Estado: `implemented-initial`.' in backlog
    assert '[x] Crear docs/05_operations/operator_onboarding_playbook.md.' in backlog
    assert '[x] Incluir flujo idea → workspace → docs → readiness → backlog.' in backlog
    assert '[x] Playbook aprobado.' in backlog
    assert 'POST-H-024-A queda implementado como **implemented-initial / playbook-only**' in implementation
    assert 'No implementa todavía templates, bootstrap workflow' in implementation
    assert 'templates, bootstrap workflow, readiness preview y onboarding quality gate permanecen pendientes' in report or 'POST-H-024-B: templates' in report


def test_post_h_024_manifest_source_registry_and_tcr_are_registered() -> None:
    manifest = read_json("docs/post_h_024_a_manifest.json")
    source_registry = read_json(".devpilot/docs_governance/source_registry.json")
    tcr_v1 = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert manifest["post_h_id"] == "POST-H-024"
    assert manifest["micro_sprint"] == "POST-H-024-A"
    assert manifest["status"] == "implemented-initial"
    assert manifest["next_micro_sprint"] == "POST-H-024-B"
    assert manifest["no_remote_execution_enabled"] is True
    assert manifest["no_external_apis_used"] is True
    assert manifest["no_connector_write_enabled"] is True
    assert manifest["no_plugin_execution_enabled"] is True
    assert "docs/05_operations/operator_onboarding_playbook.md" in manifest["created_files"]
    assert "tests/test_post_h_024_operator_onboarding.py" in manifest["created_files"]

    doc_ids = {item["doc_id"] for item in source_registry["documents"]}
    expected_doc_ids = {
        "POST-H-024-BACKLOG",
        "POST-H-024-IMPLEMENTATION-DOC",
        "POST-H-024-A-OPERATOR-ONBOARDING-PLAYBOOK",
        "POST-H-024-A-OPERATOR-PLAYBOOK-REPORT",
        "POST-H-024-A-MANIFEST",
        "POST-H-024-A-OPERATOR-ONBOARDING-TEST",
    }
    assert expected_doc_ids <= doc_ids
    backlog_entry = next(item for item in source_registry["documents"] if item["doc_id"] == "POST-H-024-BACKLOG")
    assert backlog_entry["status_required"] == "approved"
    assert backlog_entry["lifecycle"] == "active"
    assert source_registry["project_state_snapshot"]["current_micro_sprint"] == "POST-H-024-A"
    assert source_registry["project_state_snapshot"]["next_micro_sprint"] == "POST-H-024-B"

    contract_ids_v1 = {item["contract_id"] for item in tcr_v1["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}
    assert "post-h-024-operator-onboarding-playbook" in contract_ids_v1
    assert "post-h-024-operator-onboarding-playbook" in contract_ids_v2
    contract = next(item for item in tcr_v1["contracts"] if item["contract_id"] == "post-h-024-operator-onboarding-playbook")
    assert contract["critical"] is True
    assert contract["mutable_global_state_allowed"] is False
    assert contract["network_allowed"] is False
    assert contract["external_api_allowed"] is False
    assert contract["mutations_allowed"] is False


def test_project_state_and_global_docs_point_to_post_h_024_a() -> None:
    state = read_json(".devpilot/project_state.json")
    readme = read_text("README.md")
    runbook = read_text("docs/05_operations/runbook.md")
    changelog = read_text("docs/release/CHANGELOG.md")

    assert state["last_completed_sprint"] == "POST-H-023"
    assert state["next_sprint"] == "POST-H-024"
    assert state["current_micro_sprint"] == "POST-H-024-A"
    assert state["next_micro_sprint"] == "POST-H-024-B"
    assert state["post_h_024_operator_playbook_available"] is True
    assert state["post_h_024_templates_available"] is False
    assert state["post_h_024_bootstrap_workflow_available"] is False
    assert state["post_h_024_onboarding_quality_gate_available"] is False
    assert state["post_h_024_network_used"] is False
    assert state["post_h_024_external_api_used"] is False
    assert state["post_h_024_remote_execution_enabled"] is False
    assert state["post_h_024_connector_write_enabled"] is False
    assert state["post_h_024_plugin_execution_enabled"] is False
    assert any("POST-H-024-A approves Operator onboarding bootstrap" in note for note in state["notes"])
    assert any("POST-H-024-B is the next micro-sprint" in note for note in state["notes"])

    for text in (readme, runbook):
        assert "POST-H-024-A — Playbook de operador" in text
        assert "Siguiente micro-sprint: `POST-H-024-B — Templates de proyecto nuevo`" in text
        assert "implemented-initial / playbook-only" in text or "Runbook dedicado" in text

    assert "post-h-024-a" in changelog
