from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str) -> dict:
    return json.loads(read(path))


def test_post_h_008_backlog_is_approved_and_taxonomy_is_documented() -> None:
    backlog = read("docs/POST-H-008_runtime_state_lifecycle.md")
    policy_doc = read("docs/05_operations/runtime_state_lifecycle_policy.md")
    audit = read("docs/audits/post_h_008_a_runtime_state_policy_schema_report.md")
    manifest = read_json("docs/post_h_008_a_manifest.json")

    assert 'status: "approved"' in backlog
    assert 'implementation_status: "in-progress"' in backlog
    assert "POST-H-008-A — Taxonomía y policy schema" in backlog
    assert "## 13. Avance de implementación — POST-H-008-A" in backlog

    for expected in [
        "source-code",
        "engineering-docs",
        "generated-reports",
        "trace-events",
        "local-db",
        "agent-sessions",
        "rag-index",
        "python-caches",
        "node-artifacts",
    ]:
        assert expected in policy_doc

    assert "implemented-initial" in audit
    assert manifest["sprint_id"] == "POST-H-008-A"
    assert manifest["status"] == "implemented-initial"


def test_post_h_008_b_inventory_is_documented_and_manifested() -> None:
    backlog = read("docs/POST-H-008_runtime_state_lifecycle.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    policy_doc = read("docs/05_operations/runtime_state_lifecycle_policy.md")
    audit = read("docs/audits/post_h_008_b_runtime_state_inventory_report.md")
    manifest = read_json("docs/post_h_008_b_manifest.json")
    changelog = read("docs/release/CHANGELOG.md")

    assert "## 14. Avance de implementación — POST-H-008-B" in backlog
    assert "runtime-state inventory" in readme
    assert "POST-H-008-B — Runtime state inventory read-only" in runbook
    assert "POST-H-008-B — Inventory read-only" in policy_doc
    assert "Runtime state inventory read-only" in audit
    assert manifest["id"] == "POST-H-008-B"
    assert manifest["status"] == "implemented-initial"
    assert manifest["read_only_inventory"] is True
    assert manifest["cleanup_execution_enabled"] is False
    assert manifest["export_execution_enabled"] is False
    assert "post-h-008-b" in changelog



def test_post_h_008_c_cleanup_plan_is_documented_manifested_and_guarded() -> None:
    backlog = read("docs/POST-H-008_runtime_state_lifecycle.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    policy_doc = read("docs/05_operations/runtime_state_lifecycle_policy.md")
    audit = read("docs/audits/post_h_008_c_cleanup_plan_report.md")
    manifest = read_json("docs/post_h_008_c_manifest.json")
    changelog = read("docs/release/CHANGELOG.md")

    assert "## 15. Avance de implementación — POST-H-008-C" in backlog
    assert "runtime-state cleanup-plan" in readme
    assert "POST-H-008-C — Cleanup plan dry-run" in runbook
    assert "POST-H-008-C — Cleanup plan dry-run" in policy_doc
    assert "Cleanup plan dry-run" in audit
    assert manifest["id"] == "POST-H-008-C"
    assert manifest["status"] == "implemented-initial"
    assert manifest["dry_run"] is True
    assert manifest["execute_requires_confirmation"] is True
    assert manifest["source_of_truth_never_delete"] is True
    assert manifest["export_execution_enabled"] is False
    assert "post-h-008-c" in changelog

def test_post_h_007_backlog_is_closed_before_post_h_008_starts() -> None:
    backlog_007 = read("docs/backlogs/POST-H-007_application_service_boundary.md")
    readme = read("README.md")
    changelog = read("docs/release/CHANGELOG.md")

    assert 'implementation_status: "closed"' in backlog_007
    assert "## 17. Cierre del backlog — POST-H-007" in backlog_007
    assert "POST-H-007 closed" in readme
    assert "post-h-008-a" in changelog


def test_post_h_008_a_artifacts_are_registered_in_tcr() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    contract_ids = {item["contract_id"] for item in tcr["contracts"]}
    contract_ids_v2 = {item["contract_id"] for item in tcr_v2["contracts"]}

    assert "post-h-008-runtime-state-policy-schema" in contract_ids
    assert "post-h-008-runtime-state-policy-schema" in contract_ids_v2
    assert "post-h-008-runtime-state-inventory" in contract_ids
    assert "post-h-008-runtime-state-inventory" in contract_ids_v2
    assert "post-h-008-runtime-state-cleanup-plan" in contract_ids
    assert "post-h-008-runtime-state-cleanup-plan" in contract_ids_v2
    assert "post-h-008-runtime-state-export" in contract_ids
    assert "post-h-008-runtime-state-export" in contract_ids_v2

    contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-008-runtime-state-policy-schema")
    assert "tests/test_runtime_state_policy_schema.py" in contract["test_files"]
    assert ".devpilot/runtime_state_policy.json" in contract["validates"]
    assert contract["mutable_global_state_allowed"] is False

    contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-008-runtime-state-policy-schema")
    assert contract_v2["capability"] == "RuntimeStatePolicySchema"
    assert contract_v2["required_for_release"] is True
    assert contract_v2["required_for_security_gate"] is True
    assert contract_v2["network_allowed"] is False
    assert contract_v2["external_api_allowed"] is False
    assert contract_v2["mutations_allowed"] is False

    inventory_contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-008-runtime-state-inventory")
    assert inventory_contract["owner"] == "POST-H-008-B"
    assert "tests/test_runtime_state_inventory.py" in inventory_contract["test_files"]
    assert "src/devpilot_core/runtime_state/" in inventory_contract["validates"]

    inventory_contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-008-runtime-state-inventory")
    assert inventory_contract_v2["capability"] == "RuntimeStateInventory"
    assert inventory_contract_v2["required_for_release"] is True
    assert inventory_contract_v2["required_for_security_gate"] is True
    assert inventory_contract_v2["network_allowed"] is False
    assert inventory_contract_v2["external_api_allowed"] is False
    assert inventory_contract_v2["mutations_allowed"] is False

    cleanup_contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-008-runtime-state-cleanup-plan")
    assert cleanup_contract["owner"] == "POST-H-008-C"
    assert "tests/test_runtime_state_cleanup_plan.py" in cleanup_contract["test_files"]
    assert "docs/schemas/runtime_state_cleanup_plan.schema.json" in cleanup_contract["validates"]

    cleanup_contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-008-runtime-state-cleanup-plan")
    assert cleanup_contract_v2["capability"] == "RuntimeStateCleanupPlan"
    assert cleanup_contract_v2["required_for_release"] is True
    assert cleanup_contract_v2["required_for_security_gate"] is True
    assert cleanup_contract_v2["network_allowed"] is False
    assert cleanup_contract_v2["external_api_allowed"] is False
    assert cleanup_contract_v2["mutations_allowed"] is False


def test_post_h_008_d_export_is_documented_manifested_and_guarded() -> None:
    backlog = read("docs/POST-H-008_runtime_state_lifecycle.md")
    readme = read("README.md")
    runbook = read("docs/05_operations/runbook.md")
    policy_doc = read("docs/05_operations/runtime_state_lifecycle_policy.md")
    audit = read("docs/audits/post_h_008_d_runtime_state_export_report.md")
    manifest = read_json("docs/post_h_008_d_manifest.json")
    changelog = read("docs/release/CHANGELOG.md")

    assert "## 16. Avance de implementación — POST-H-008-D" in backlog
    assert "runtime-state export" in readme
    assert "POST-H-008-D — Export y redacción de evidencia runtime" in runbook
    assert "POST-H-008-D — Export y redacción de evidencia runtime" in policy_doc
    assert "Runtime state export/redaction report" in audit
    assert manifest["id"] == "POST-H-008-D"
    assert manifest["status"] == "implemented-initial"
    assert manifest["dry_run"] is True
    assert manifest["execute_requires_explicit_output"] is True
    assert manifest["redaction_execution_enabled"] is True
    assert manifest["raw_prompts_exported"] is False
    assert manifest["raw_outputs_exported"] is False
    assert manifest["secrets_exported"] is False
    assert manifest["local_db_raw_exported"] is False
    assert "post-h-008-d" in changelog


def test_post_h_008_d_export_contract_is_registered_in_tcr() -> None:
    tcr = read_json(".devpilot/testing/test_contract_registry.json")
    tcr_v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")

    export_contract = next(item for item in tcr["contracts"] if item["contract_id"] == "post-h-008-runtime-state-export")
    assert export_contract["owner"] == "POST-H-008-D"
    assert "tests/test_runtime_state_export.py" in export_contract["test_files"]
    assert "docs/schemas/runtime_state_export_manifest.schema.json" in export_contract["validates"]
    assert export_contract["mutable_global_state_allowed"] is False

    export_contract_v2 = next(item for item in tcr_v2["contracts"] if item["contract_id"] == "post-h-008-runtime-state-export")
    assert export_contract_v2["capability"] == "RuntimeStateExportManifest"
    assert export_contract_v2["required_for_release"] is True
    assert export_contract_v2["required_for_security_gate"] is True
    assert export_contract_v2["network_allowed"] is False
    assert export_contract_v2["external_api_allowed"] is False
    assert export_contract_v2["mutations_allowed"] is False
    assert export_contract_v2["source_mutations_allowed"] is False
