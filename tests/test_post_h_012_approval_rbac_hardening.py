from __future__ import annotations

import json
from pathlib import Path

from devpilot_core import cli
from devpilot_core.docs_governance import DocumentationGovernanceValidator, load_documentation_source_registry
from devpilot_core.policy.sensitive_actions import (
    REQUIRED_SENSITIVE_ACTION_DOMAINS,
    SensitiveActionCatalogValidator,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / ".devpilot/approval/sensitive_action_catalog.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_post_h_012_backlog_is_approved_and_synced() -> None:
    backlog = read("docs/backlogs/POST-H-012_approval_rbac_hardening.md")
    mirror = read("docs/POST-H-012_approval_rbac_hardening.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert backlog == mirror
    assert 'status: "approved"' in backlog
    assert 'approval: "approved_by_owner"' in backlog
    assert 'implementation_status: "active"' in backlog
    assert 'current_micro_sprint: "POST-H-012-C"' in backlog
    assert 'next_micro_sprint: "POST-H-012-D"' in backlog
    assert "## 14. Avance de implementación — POST-H-012-A" in backlog
    assert "## 15. Avance de implementación — POST-H-012-B" in backlog
    assert "## 16. Avance de implementación — POST-H-012-C" in backlog
    assert "docs/schemas/sensitive_action_catalog.schema.json" in backlog
    assert ".devpilot/approval/sensitive_action_catalog.json" in backlog
    assert "src/devpilot_core/policy/sensitive_actions.py" in backlog
    assert "tests/test_post_h_012_approval_rbac_hardening.py" in backlog
    assert "src/devpilot_core/approval/binding.py" in backlog
    assert "tests/test_approval_binding.py" in backlog
    assert "src/devpilot_core/identity/exposure.py" in backlog
    assert "tests/test_rbac_exposure.py" in backlog
    assert "docs/schemas/rbac_exposure_report.schema.json" in backlog
    assert "POST-H-012-C — RBAC exposure report" in readme
    assert "POST-H-012-C — RBAC exposure report" in runbook
    assert "post-h-012-b" in changelog
    assert "post-h-012-c" in changelog


def test_sensitive_action_catalog_schema_and_validator_pass(monkeypatch, capsys) -> None:
    monkeypatch.chdir(ROOT)

    exit_code = cli.main([
        "schema",
        "validate",
        "--schema-id",
        "SensitiveActionCatalog",
        "--instance",
        ".devpilot/approval/sensitive_action_catalog.json",
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["summary"]["valid"] is True

    result = SensitiveActionCatalogValidator(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["actions_total"] >= 11
    assert summary["required_domains_covered_total"] == len(REQUIRED_SENSITIVE_ACTION_DOMAINS)
    assert summary["critical_actions_total"] >= 7
    assert summary["actions_requiring_approval_total"] == summary["actions_total"]
    assert summary["actions_requiring_rbac_total"] == summary["actions_total"]
    assert summary["remote_actions_blocked_total"] >= 1
    assert summary["connector_write_actions_blocked_total"] >= 1
    assert summary["plugin_execution_actions_blocked_total"] >= 1
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False


def test_sensitive_action_catalog_blocks_dangerous_surfaces() -> None:
    catalog = read_json(".devpilot/approval/sensitive_action_catalog.json")
    actions = {item["action_id"]: item for item in catalog["actions"]}

    for action_id in ["remote.execute", "connector.write_execute", "plugin.execute_code"]:
        action = actions[action_id]
        assert action["status"] == "blocked"
        assert action["default_effect"] in {"block", "deny"}
        assert action["executable"] is False
        assert action["source_mutation_allowed"] is False
        assert action["requires_approval"] is True
        assert action["requires_rbac_role"]
        assert action["requires_tool_call_binding"] is True
        assert action["requires_command_binding"] is True

    critical_actions = [item for item in catalog["actions"] if item["risk_level"] == "critical"]
    assert critical_actions
    assert all(item["requires_approval"] is True for item in critical_actions)
    assert all(item["requires_rbac_role"] for item in critical_actions)
    assert all(item["requires_tool_call_binding"] is True for item in critical_actions)
    assert all(item["requires_command_binding"] is True for item in critical_actions)

    assert catalog["safety"]["remote_execution_enabled"] is False
    assert catalog["safety"]["connector_write_enabled"] is False
    assert catalog["safety"]["plugin_execution_enabled"] is False
    assert catalog["safety"]["deny_by_default"] is True


def test_sensitive_action_catalog_cross_checks_miasi_policy_matrix() -> None:
    catalog = read_json(".devpilot/approval/sensitive_action_catalog.json")
    policy = read_json(".devpilot/miasi/policy_matrix.json")
    tool_registry = read_json(".devpilot/miasi/tool_registry.json")
    policy_rule_ids = {item["rule_id"] for item in policy["rules"]}
    tool_ids = {item["tool_id"] for item in tool_registry["tools"]}

    assert {action["domain"] for action in catalog["actions"]} >= REQUIRED_SENSITIVE_ACTION_DOMAINS
    for action in catalog["actions"]:
        assert action["miasi_policy_rule_ids"]
        assert set(action["miasi_policy_rule_ids"]).issubset(policy_rule_ids)
        assert set(action.get("tool_ids", [])).issubset(tool_ids)


def test_post_h_012_source_registry_and_contracts_are_registered() -> None:
    registry = load_documentation_source_registry(ROOT)
    by_path = registry.by_path()
    doc = by_path["docs/backlogs/POST-H-012_approval_rbac_hardening.md"]

    assert doc.doc_id == "POST-H-012-BACKLOG"
    assert doc.status_required == "approved"
    assert doc.lifecycle == "active"
    assert "docs/POST-H-012_approval_rbac_hardening.md" in doc.derived_documents
    assert "docs/schemas/sensitive_action_catalog.schema.json" in doc.derived_documents
    assert ".devpilot/approval/sensitive_action_catalog.json" in doc.derived_documents
    assert "docs/audits/post_h_012_a_sensitive_action_catalog_report.md" in doc.derived_documents
    assert "docs/post_h_012_a_manifest.json" in doc.derived_documents
    assert "src/devpilot_core/approval/binding.py" in doc.derived_documents
    assert "docs/audits/post_h_012_b_approval_binding_report.md" in doc.derived_documents
    assert "docs/post_h_012_b_manifest.json" in doc.derived_documents
    assert "src/devpilot_core/identity/exposure.py" in doc.derived_documents
    assert "docs/schemas/rbac_exposure_report.schema.json" in doc.derived_documents
    assert "docs/audits/post_h_012_c_rbac_exposure_report.md" in doc.derived_documents
    assert "docs/post_h_012_c_manifest.json" in doc.derived_documents
    assert "tests/test_post_h_012_approval_rbac_hardening.py" in doc.required_tests
    assert "tests/test_approval_binding.py" in doc.required_tests
    assert "tests/test_rbac_exposure.py" in doc.required_tests

    result = DocumentationGovernanceValidator(ROOT).run()
    assert result.ok, result.to_dict()
    assert result.data["summary"]["blocking_findings_total"] == 0

    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-012-sensitive-action-catalog")
    assert contract["owner"] == "POST-H-012-A"
    assert "tests/test_post_h_012_approval_rbac_hardening.py" in contract["test_files"]
    assert "docs/schemas/sensitive_action_catalog.schema.json" in contract["validates"]
    assert ".devpilot/approval/sensitive_action_catalog.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-012-sensitive-action-catalog")
    assert contract_v2["domain"] == "security.approval"
    assert contract_v2["capability"] == "SensitiveActionCatalog"
    assert contract_v2["criticality"] == "P1"
    assert contract_v2["risk_level"] == "critical"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False

    binding_contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-012-approval-binding")
    assert binding_contract["owner"] == "POST-H-012-B"
    assert "tests/test_approval_binding.py" in binding_contract["test_files"]
    assert "src/devpilot_core/approval/binding.py" in binding_contract["validates"]
    binding_contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-012-approval-binding")
    assert binding_contract_v2["capability"] == "StrongApprovalBinding"
    assert binding_contract_v2["network_allowed"] is False
    assert binding_contract_v2["source_mutations_allowed"] is False

    exposure_contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-012-rbac-exposure-report")
    assert exposure_contract["owner"] == "POST-H-012-C"
    assert "tests/test_rbac_exposure.py" in exposure_contract["test_files"]
    assert "src/devpilot_core/identity/exposure.py" in exposure_contract["validates"]
    assert "docs/schemas/rbac_exposure_report.schema.json" in exposure_contract["validates"]
    exposure_contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-012-rbac-exposure-report")
    assert exposure_contract_v2["capability"] == "RbacExposureReport"
    assert exposure_contract_v2["network_allowed"] is False
    assert exposure_contract_v2["source_mutations_allowed"] is False


def test_post_h_012_project_state_is_synchronized() -> None:
    state = read_json(".devpilot/project_state.json")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")

    assert state["last_completed_sprint"] == "POST-H-011"
    assert state["next_sprint"] == "POST-H-012"
    assert state["current_repo"] == "repo_DevPilot_Local_193_POST_H_012_C.zip"
    assert any("POST-H-012-C adds RBAC exposure reporting" in note for note in state["notes"])
    assert "Último micro-sprint implementado: `POST-H-012-C" in readme
    assert "Siguiente micro-sprint recomendado: `POST-H-012-D" in readme
    assert "POST-H-012-C — RBAC exposure report" in runbook
