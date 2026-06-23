from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/audits/post_h_eval_001_baseline_assessment.md",
    "docs/02_architecture/post_h_current_architecture_map.md",
    "docs/03_security/post_h_security_risk_register.md",
    "docs/04_quality/post_h_test_cost_assessment.md",
    "docs/backlogs/post_h_prioritized_roadmap.md",
    "docs/audits/post_h_eval_001_closure_report.md",
    "docs/post_h_eval_001_manifest.json",
]

REQUIRED_ADRS = [
    "docs/adr/ADR-POSTH-001-local-first-before-remote.md",
    "docs/adr/ADR-POSTH-002-test-contract-registry-2.md",
    "docs/adr/ADR-POSTH-003-cli-modularization.md",
]


def read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.exists(), relative_path
    return path.read_text(encoding="utf-8")


def test_post_h_eval_001_required_docs_exist() -> None:
    for relative_path in REQUIRED_DOCS + REQUIRED_ADRS:
        assert (ROOT / relative_path).exists(), relative_path


def test_post_h_eval_001_manifest_contract_and_closure_state() -> None:
    manifest = json.loads(read("docs/post_h_eval_001_manifest.json"))
    assert manifest["id"] == "POST-H-EVAL-001"
    assert manifest["type"] == "diagnostic-executable-backlog"
    assert manifest["status"] == "closed"
    assert manifest["current_micro_sprint"] == "POST-H-EVAL-001-G"
    assert manifest["next_micro_sprint"] == "POST-H-002"
    assert manifest["no_runtime_features_added"] is True
    assert manifest["no_remote_execution_enabled"] is True
    assert manifest["no_external_apis_used"] is True
    assert manifest["no_connector_write_enabled"] is True
    assert manifest["no_plugin_execution_enabled"] is True
    assert manifest["post_h_002_entry_criteria"]["post_h_eval_001_closed"] is True
    assert manifest["post_h_002_entry_criteria"]["remote_execution_disabled"] is True


def test_post_h_eval_001_docs_have_required_sections() -> None:
    expectations = {
        "docs/audits/post_h_eval_001_baseline_assessment.md": [
            "Estado ejecutivo",
            "Snapshot cuantitativo",
            "Capacidades por dominio",
            "Riesgos",
            "Roadmap",
        ],
        "docs/02_architecture/post_h_current_architecture_map.md": [
            "Vista por capas",
            "Puntos de acoplamiento",
            "Riesgos arquitectónicos",
        ],
        "docs/03_security/post_h_security_risk_register.md": [
            "SEC-001",
            "remote execution",
            "Connector",
            "Plugin",
        ],
        "docs/04_quality/post_h_test_cost_assessment.md": [
            "Test Contract Registry",
            "Impact analyzer",
            "P0",
            "P1",
        ],
        "docs/backlogs/post_h_prioritized_roadmap.md": [
            "Oleada 0",
            "Oleada 1",
            "POST-H-002",
            "Remote",
        ],
        "docs/audits/post_h_eval_001_closure_report.md": [
            "Implementado",
            "Implementado inicial",
            "Parcial",
            "Contrato",
            "Definido/no implementado",
            "No iniciado",
            "Bloqueado por diseño",
            "Futuro",
            "Criterios PASS",
            "Criterios BLOCK",
        ],
    }

    for relative_path, required_terms in expectations.items():
        content = read(relative_path)
        for term in required_terms:
            assert term in content, f"{term} missing from {relative_path}"


def test_post_h_eval_001_manifest_deliverables_and_decisions_are_complete() -> None:
    manifest = json.loads(read("docs/post_h_eval_001_manifest.json"))
    deliverable_paths = {
        item["path"] if isinstance(item, dict) else item
        for item in manifest.get("deliverables", [])
    }
    expected = set(REQUIRED_DOCS + REQUIRED_ADRS + [
        ".devpilot/evals/post_h_eval_001_decision_matrix.json",
        ".devpilot/evals/post_h_eval_001_security_risk_register.json",
        ".devpilot/evals/post_h_eval_001_test_cost_assessment.json",
        ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json",
        "tests/test_post_h_eval_001_documentation.py",
    ])
    assert expected.issubset(deliverable_paths)

    decision_ids = {
        item.get("id") if isinstance(item, dict) else item
        for item in manifest.get("decisions", [])
    }
    for decision_id in [
        "DEC-POSTH-001",
        "DEC-POSTH-002",
        "DEC-POSTH-003",
        "DEC-POSTH-004",
        "DEC-POSTH-005",
        "DEC-POSTH-006",
        "DEC-POSTH-007",
    ]:
        assert decision_id in decision_ids


def test_post_h_eval_001_no_go_gates_remain_closed() -> None:
    manifest = json.loads(read("docs/post_h_eval_001_manifest.json"))
    no_go = manifest["no_go_gates"]
    assert no_go["remote_execution_enabled"] is False
    assert no_go["connector_write_enabled"] is False
    assert no_go["plugin_execution_enabled"] is False
    assert no_go["external_apis_enabled"] is False
    assert no_go["production_enterprise_claim"] is False
    assert no_go["compliance_certification_claim"] is False
