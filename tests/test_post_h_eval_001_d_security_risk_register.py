from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/03_security/post_h_security_risk_register.md"
REGISTRY = ROOT / ".devpilot/evals/post_h_eval_001_security_risk_register.json"


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def _registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_post_h_eval_001_d_risk_register_exists():
    assert DOC.exists()
    assert REGISTRY.exists()


def test_post_h_eval_001_d_minimum_risks_and_required_ids():
    content = _doc()
    registry = _registry()
    required_ids = [f"SEC-{i:03d}" for i in range(1, 11)]
    assert registry["summary"]["risks_total"] >= 10
    assert len(registry["risks"]) >= 10
    for risk_id in required_ids:
        assert risk_id in content
        assert any(r["id"] == risk_id for r in registry["risks"])


def test_post_h_eval_001_d_required_fields_are_present_for_all_risks():
    required_fields = {
        "id",
        "title",
        "severity",
        "probability",
        "impact",
        "current_state",
        "evidence",
        "mitigation",
        "closure_criteria",
        "recommended_sprint",
        "priority",
        "status",
    }
    for risk in _registry()["risks"]:
        missing = required_fields - set(risk)
        assert not missing, f"{risk['id']} missing {missing}"
        assert risk["evidence"], risk["id"]
        assert risk["mitigation"], risk["id"]
        assert risk["closure_criteria"], risk["id"]


def test_post_h_eval_001_d_security_boundaries_are_explicit():
    content = _doc()
    registry = _registry()
    assert registry["summary"]["remote_execution_enabled"] is False
    assert registry["summary"]["write_connectors_enabled"] is False
    assert registry["summary"]["plugin_execution_enabled"] is False
    assert registry["summary"]["compliance_certification_claimed"] is False
    required_terms = [
        "Remote execution: no habilitada",
        "Connector write: bloqueado por defecto",
        "Plugin execution: bloqueado hasta sandbox",
        "Compliance: evidencia local, no certificación",
        "Runtime artifacts: riesgo explícito de distribución",
        "Secret leakage: riesgo explícito",
    ]
    for term in required_terms:
        assert term in content, term


def test_post_h_eval_001_d_remote_is_critical_and_write_paths_blocked():
    risks = {risk["id"]: risk for risk in _registry()["risks"]}
    assert risks["SEC-001"]["severity"] == "Crítica"
    assert risks["SEC-002"]["severity"] == "Alta"
    assert risks["SEC-003"]["severity"] == "Alta"
    assert "disabled" in risks["SEC-001"]["current_state"] or "False" in risks["SEC-001"]["current_state"]
    assert "deny" in risks["SEC-002"]["current_state"].lower()
    assert "metadata" in risks["SEC-003"]["mitigation"].lower()


def test_post_h_eval_001_d_forbidden_claims_absent():
    lowered = _doc().lower()
    forbidden = [
        "remote execution enabled",
        "write connectors enabled",
        "plugin execution enabled",
        "compliance certified",
        "devpilot is certified",
        "devpilot está certificado",
        "production-ready enterprise",
    ]
    for claim in forbidden:
        assert claim not in lowered, claim
