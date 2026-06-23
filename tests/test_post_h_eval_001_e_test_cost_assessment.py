from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "04_quality" / "post_h_test_cost_assessment.md"
DATA = ROOT / ".devpilot" / "evals" / "post_h_eval_001_test_cost_assessment.json"
MANIFEST = ROOT / "docs" / "post_h_eval_001_manifest.json"


def _read_doc() -> str:
    assert DOC.exists(), "POST-H-EVAL-001-E test/cost assessment document is missing."
    return DOC.read_text(encoding="utf-8")


def _read_data() -> dict:
    assert DATA.exists(), "POST-H-EVAL-001-E machine-readable assessment is missing."
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_post_h_eval_001_e_required_sections_exist() -> None:
    text = _read_doc()
    required = [
        "## 1. Resumen ejecutivo",
        "## 2. Inventario de tests",
        "## 3. Test Contract Registry actual",
        "## 4. Tests históricos vs tests funcionales",
        "## 5. Quality gates existentes",
        "## 6. Impact analyzer actual",
        "## 7. Costos de regresión",
        "## 8. Brechas de cobertura por dominio",
        "## 9. Propuesta Test Contract Registry 2.0",
        "## 10. Matriz P0/P1/P2/P3",
        "## 11. Roadmap de testing",
        "## 12. Criterios de cierre",
    ]
    missing = [section for section in required if section not in text]
    assert not missing, f"Missing required sections: {missing}"


def test_post_h_eval_001_e_answers_mandatory_questions() -> None:
    text = _read_doc()
    questions = [
        "¿Qué pruebas son críticas para no romper seguridad?",
        "¿Qué pruebas son históricas y documentales?",
        "¿Qué pruebas son de producto?",
        "¿Qué pruebas pueden correr siempre?",
        "¿Qué pruebas deben correr por impacto?",
        "¿Qué pruebas deben ejecutarse solo antes de release?",
        "¿Qué dominios no están bien mapeados por impact analyzer?",
    ]
    missing = [q for q in questions if q not in text]
    assert not missing, f"Mandatory questions missing: {missing}"


def test_post_h_eval_001_e_machine_readable_assessment_is_complete() -> None:
    data = _read_data()
    assert data["id"] == "POST-H-EVAL-001-E"
    assert data["status"] == "implemented"
    inventory = data["inventory"]
    assert inventory["test_files_total"] >= 180
    assert inventory["pytest_collect_items_total"] >= 800
    assert inventory["test_contracts_total"] >= 80
    assert inventory["historical_documentation_test_files_total"] >= 70
    assert inventory["unmapped_test_files_total"] > 0
    proposal = data["test_contract_registry_2_proposal"]
    assert proposal["schema_candidate"] == "SCHEMA-DEVPL-TEST-CONTRACT-REGISTRY-V2"
    assert "priority" in proposal["new_fields"]
    assert "execution_tier" in proposal["new_fields"]
    assert "required_for_remote_enablement" in proposal["new_fields"]


def test_post_h_eval_001_e_pass_block_criteria_are_explicit() -> None:
    data = _read_data()
    pass_criteria = data["pass_criteria"]
    assert pass_criteria["test_contract_registry_2_proposed"] is True
    assert pass_criteria["tests_classified_by_criticality"] is True
    assert pass_criteria["pytest_cost_evaluated"] is True
    assert pass_criteria["impact_analyzer_gaps_identified"] is True
    assert pass_criteria["testing_roadmap_recommended"] is True
    block_criteria = data["block_criteria"]
    assert block_criteria["assumes_many_tests_equals_industrial_coverage"] is False
    assert block_criteria["mixes_historical_and_critical_tests"] is False
    assert block_criteria["omits_execution_cost"] is False


def test_post_h_eval_001_e_security_and_runtime_limits_hold() -> None:
    data = _read_data()
    policy = data["policy"]
    assert policy["no_runtime_features_added"] is True
    assert policy["no_remote_execution_enabled"] is True
    assert policy["no_write_connectors_enabled"] is True
    assert policy["no_external_apis_used"] is True
    text = _read_doc().lower()
    forbidden = [
        "remote execution enabled",
        "write connectors enabled",
        "plugin execution enabled",
        "external api used: true",
    ]
    assert not any(term in text for term in forbidden)


def test_post_h_eval_001_manifest_points_to_e_and_next_f() -> None:
    assert MANIFEST.exists(), "POST-H-EVAL-001 manifest is missing."
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["current_micro_sprint"] == "POST-H-EVAL-001-E"
    assert manifest["next_micro_sprint"] == "POST-H-EVAL-001-F"
    deliverables = manifest.get("deliverables", [])
    deliverable_paths = {
        item["path"] if isinstance(item, dict) else item
        for item in deliverables
    }
    assert "docs/04_quality/post_h_test_cost_assessment.md" in deliverable_paths
    assert ".devpilot/evals/post_h_eval_001_test_cost_assessment.json" in deliverable_paths
