from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "backlogs" / "post_h_prioritized_roadmap.md"
ROADMAP_JSON = ROOT / ".devpilot" / "evals" / "post_h_eval_001_prioritized_roadmap.json"


def test_onboarding_adjustment_adds_operator_and_production_ready_gates() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    for term in [
        "Informe de onboarding DevPilot",
        "POST-H-024 — Operator onboarding playbook y project bootstrap workflow",
        "POST-H-025 — DevPilot Local production-ready declaration gate",
        "production-ready-local",
        "DevPilot no debe declararse `production-ready` completo",
        "Backlogs ejecutables derivados del roadmap definitivo",
    ]:
        assert term in text


def test_roadmap_json_reflects_onboarding_adjustment() -> None:
    data = json.loads(ROADMAP_JSON.read_text(encoding="utf-8"))
    assert data["adjusted_after_onboarding"] is True
    assert any(w["id"] == "wave-7" for w in data["waves"])
    assert any("POST-H-024" in w["milestones"] for w in data["waves"])
    assert data["production_ready_declaration"]["milestone"] == "POST-H-025"
    assert "remote_execution" in data["production_ready_declaration"]["must_not_enable"]
    paths = {item["path"] for item in data["executable_backlogs_to_create"]}
    assert "docs/backlogs/POST-H-024_operator_onboarding_bootstrap.md" in paths
    assert "docs/backlogs/POST-H-025_production_ready_declaration_gate.md" in paths
