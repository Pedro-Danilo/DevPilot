from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.docs_governance import DocumentationGovernanceValidator, load_documentation_source_registry

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_post_h_010_backlog_is_approved_and_synced_with_mirror() -> None:
    backlog = read("docs/backlogs/POST-H-010_observability_retention.md")
    mirror = read("docs/POST-H-010_observability_retention.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert backlog == mirror
    assert 'status: "approved"' in backlog
    assert 'approval: "approved_by_owner"' in backlog
    assert 'implementation_status: "active"' in backlog
    assert 'current_micro_sprint: "POST-H-010-C"' in backlog
    assert 'next_micro_sprint: "POST-H-010-D"' in backlog
    assert "## 14. Avance de implementación — POST-H-010-A" in backlog
    assert "## 15. Avance de implementación — POST-H-010-B" in backlog
    assert "## 16. Avance de implementación — POST-H-010-C" in backlog
    assert "docs/schemas/observability_retention_policy.schema.json" in backlog
    assert "docs/schemas/observability_inventory.schema.json" in backlog
    assert "docs/schemas/observability_cleanup_plan.schema.json" in backlog
    assert ".devpilot/observability/retention_policy.json" in backlog
    assert "src/devpilot_core/observability/inventory.py" in backlog
    assert "src/devpilot_core/observability/cleanup.py" in backlog
    assert "POST-H-010-A — Observability retention" in readme
    assert "POST-H-010-B — Observability retention" in readme
    assert "POST-H-010-C — Observability retention" in readme
    assert "POST-H-010-A — Retention policy schema y defaults locales" in runbook
    assert "POST-H-010-B — Observability inventory read-only" in runbook
    assert "POST-H-010-C — Cleanup plan dry-run" in runbook
    assert "post-h-010-a" in changelog
    assert "post-h-010-b" in changelog
    assert "post-h-010-c" in changelog


def test_post_h_010_source_registry_and_docs_governance_pass() -> None:
    registry = load_documentation_source_registry(ROOT)
    by_path = registry.by_path()
    doc = by_path["docs/backlogs/POST-H-010_observability_retention.md"]

    assert doc.doc_id == "POST-H-010-BACKLOG"
    assert doc.status_required == "approved"
    assert doc.lifecycle == "active"
    assert "docs/POST-H-010_observability_retention.md" in doc.derived_documents
    assert "tests/test_observability_retention_schema.py" in doc.required_tests
    assert "tests/test_observability_inventory.py" in doc.required_tests
    assert "tests/test_observability_cleanup_plan.py" in doc.required_tests
    assert "tests/test_post_h_010_observability_retention.py" in doc.required_tests

    result = DocumentationGovernanceValidator(ROOT).run()
    assert result.ok, result.to_dict()
    summary = result.data["summary"]
    assert summary["docs_governance_passed"] is True
    assert summary["backlog_governance_passed"] is True
    assert summary["blocking_findings_total"] == 0


def test_post_h_010_tcr_contracts_are_registered() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-010-observability-retention-policy")
    assert contract["owner"] == "POST-H-010-A"
    assert "tests/test_observability_retention_schema.py" in contract["test_files"]
    assert ".devpilot/observability/retention_policy.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-010-observability-retention-policy")
    assert contract_v2["capability"] == "ObservabilityRetentionPolicy"
    assert contract_v2["criticality"] == "P1"
    assert contract_v2["risk_level"] == "high"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False


def test_post_h_010_b_inventory_contracts_are_registered() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-010-observability-inventory")
    assert contract["owner"] == "POST-H-010-B"
    assert "tests/test_observability_inventory.py" in contract["test_files"]
    assert "src/devpilot_core/observability/inventory.py" in contract["validates"]
    assert "docs/schemas/observability_inventory.schema.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-010-observability-inventory")
    assert contract_v2["capability"] == "ObservabilityInventory"
    assert contract_v2["criticality"] == "P1"
    assert contract_v2["risk_level"] == "high"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False


def test_post_h_010_c_cleanup_plan_contracts_are_registered() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-010-observability-cleanup-plan")
    assert contract["owner"] == "POST-H-010-C"
    assert "tests/test_observability_cleanup_plan.py" in contract["test_files"]
    assert "src/devpilot_core/observability/cleanup.py" in contract["validates"]
    assert "docs/schemas/observability_cleanup_plan.schema.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-010-observability-cleanup-plan")
    assert contract_v2["capability"] == "ObservabilityCleanupPlan"
    assert contract_v2["criticality"] == "P1"
    assert contract_v2["risk_level"] == "high"
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False
    assert contract_v2["source_mutations_allowed"] is False
