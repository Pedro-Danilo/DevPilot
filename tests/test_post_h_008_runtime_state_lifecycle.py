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
