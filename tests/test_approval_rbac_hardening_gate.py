from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.approval import ApprovalRbacHardeningGate
from devpilot_core.cli_models import ExitCode
from devpilot_core.quality import QualityGate, QualityGateOptions

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_approval_rbac_hardening_gate_passes_read_only() -> None:
    result = ApprovalRbacHardeningGate(ROOT).run()

    assert result.ok is True, result.to_dict()
    assert result.exit_code == ExitCode.PASS
    summary = result.data["summary"]
    assert summary["created_by"] == "POST-H-012-E"
    assert summary["quality_gate_ready"] is True
    assert summary["catalog_ok"] is True
    assert summary["rbac_exposure_ok"] is True
    assert summary["policy_scenarios_total"] == 3
    assert summary["policy_scenarios_blocked_total"] == 3
    assert "APPROVAL_REQUIRED" in summary["policy_expected_findings_covered"]
    assert "RBAC_DENIED" in summary["policy_expected_findings_covered"]
    assert summary["approval_binding_scope_mismatch_blocked"] is True
    assert summary["docs_lifecycle_documented"] is True
    assert summary["docs_revocation_documented"] is True
    assert summary["docs_actor_role_interface_documented"] is True
    assert summary["test_contract_registered"] is True
    assert summary["test_contract_v2_registered"] is True
    assert summary["read_only"] is True
    assert summary["dry_run"] is True
    assert summary["network_used"] is False
    assert summary["external_api_used"] is False
    assert summary["mutations_performed"] is False
    assert summary["source_mutations_performed"] is False
    assert summary["remote_execution_enabled"] is False
    assert summary["connector_write_enabled"] is False
    assert summary["plugin_execution_enabled"] is False


def test_quality_gate_hardening_includes_approval_rbac_subgate() -> None:
    result = QualityGate(ROOT, options=QualityGateOptions(profile="hardening", include_pytest=False)).run()

    assert result.ok is True, result.to_dict()
    subgates = {item["id"]: item for item in result.data["subgates"]}
    assert "approval-rbac-hardening" in subgates
    subgate = subgates["approval-rbac-hardening"]
    assert subgate["ok"] is True
    assert subgate["summary"]["quality_gate_ready"] is True
    assert subgate["summary"]["blocking_findings_total"] == 0
    assert subgate["summary"]["network_used"] is False
    assert subgate["summary"]["external_api_used"] is False


def test_post_h_012_e_docs_and_contracts_are_synchronized() -> None:
    security_doc = read("docs/03_security/approval_rbac_hardening.md")
    runbook = read("docs/05_operations/runbook.md")
    human_card = read("docs/06_miasi/human_approval_card.md")
    backlog = read("docs/backlogs/POST-H-012_approval_rbac_hardening.md")
    mirror = read("docs/POST-H-012_approval_rbac_hardening.md")
    manifest = read_json("docs/post_h_012_e_manifest.json")
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    assert backlog == mirror
    assert 'implementation_status: "closed"' in backlog
    assert 'current_micro_sprint: "POST-H-012-E"' in backlog
    assert 'next_micro_sprint: "POST-H-013"' in backlog
    assert "## 18. Avance de implementación — POST-H-012-E" in backlog
    for required in ["approval request", "approval approve", "approval deny", "approval revoke", "role_at_decision", "interface", "dry-run"]:
        assert required in security_doc
        assert required in runbook or required in human_card
    assert "NO approvals globales permanentes" in security_doc
    assert manifest["micro_sprint"] == "POST-H-012-E"
    assert manifest["current_repo"] == "repo_DevPilot_Local_195_POST_H_012_E.zip"

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-012-approval-rbac-hardening-gate")
    assert contract["scope"] == "quality-gate"
    assert contract["owner"] == "POST-H-012-E"
    assert "tests/test_approval_rbac_hardening_gate.py" in contract["test_files"]
    assert "src/devpilot_core/approval/hardening.py" in contract["validates"]

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-012-approval-rbac-hardening-gate")
    assert contract_v2["domain"] == "security.approval"
    assert contract_v2["capability"] == "ApprovalRbacHardeningGate"
    assert contract_v2["test_type"] == "quality-gate"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False
