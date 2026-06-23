from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "backlogs" / "post_h_prioritized_roadmap.md"
ROADMAP_JSON = ROOT / ".devpilot" / "evals" / "post_h_eval_001_prioritized_roadmap.json"
MANIFEST = ROOT / "docs" / "post_h_eval_001_manifest.json"
ADRS = [
    ROOT / "docs" / "adr" / "ADR-POSTH-001-local-first-before-remote.md",
    ROOT / "docs" / "adr" / "ADR-POSTH-002-test-contract-registry-2.md",
    ROOT / "docs" / "adr" / "ADR-POSTH-003-cli-modularization.md",
]


def read(path: Path) -> str:
    assert path.exists(), f"Missing expected file: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_post_h_eval_001_f_roadmap_required_content() -> None:
    text = read(ROADMAP)
    required_terms = [
        "POST-H-EVAL-001-F",
        "Oleada 0",
        "Oleada 1",
        "Oleada 2",
        "Oleada 3",
        "Oleada 4",
        "Oleada 5",
        "Oleada 6",
        "P0",
        "P1",
        "P2",
        "P3",
        "POST-H-002 — Maturity dashboard local basado en assessment post-H",
        "Test Contract Registry 2.0",
        "CLI command registry",
        "remote execution",
        "Criterios PASS",
        "Criterios BLOCK",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing roadmap terms: {missing}"


def test_post_h_eval_001_f_decisions_and_post_h_002_entry_criteria() -> None:
    text = read(ROADMAP)
    for decision_id in [
        "DEC-POSTH-001",
        "DEC-POSTH-002",
        "DEC-POSTH-003",
        "DEC-POSTH-004",
        "DEC-POSTH-005",
        "DEC-POSTH-006",
    ]:
        assert decision_id in text
    assert "cerrado con micro-sprint G" in text
    assert "Remote execution sigue disabled" in text
    assert "Connector write sigue denied-by-default" in text


def test_post_h_eval_001_f_adrs_exist_and_have_required_structure() -> None:
    for adr in ADRS:
        text = read(adr)
        assert "doc_id:" in text
        assert 'status: "approved"' in text
        assert "## Contexto" in text
        assert "## Decisión" in text
        assert "## Alternativas consideradas" in text
        assert "## Consecuencias" in text
        assert "## Criterios PASS" in text
        assert "## Criterios BLOCK" in text
        assert "## Comandos de verificación" in text


def test_post_h_eval_001_f_machine_readable_roadmap_contract() -> None:
    data = json.loads(read(ROADMAP_JSON))
    assert data["id"] == "POST-H-EVAL-001-F"
    assert data["status"] == "implemented"
    assert data["policy"]["no_runtime_features_added"] is True
    assert data["policy"]["no_remote_execution_enabled"] is True
    assert data["policy"]["no_write_connectors_enabled"] is True
    assert data["policy"]["no_external_apis_used"] is True
    assert set(data["priorities"]) == {"P0", "P1", "P2", "P3"}
    assert len(data["waves"]) >= 7
    assert any("POST-H-002" in milestone for wave in data["waves"] for milestone in wave["milestones"])
    # Roadmap v1.1 can include later onboarding/production-readiness waves while preserving F baseline.
    if data.get("adjusted_after_onboarding"):
        assert any("POST-H-024" in milestone for wave in data["waves"] for milestone in wave["milestones"])
        assert any("POST-H-025" in milestone for wave in data["waves"] for milestone in wave["milestones"])
    assert data["entry_criteria_for_post_h_002"]["post_h_eval_001_closed_with_g"] is True
    assert data["entry_criteria_for_post_h_002"]["remote_execution_disabled"] is True


def test_post_h_eval_001_manifest_preserves_f_deliverables_after_progression() -> None:
    manifest = json.loads(read(MANIFEST))

    # This is a historical contract for micro-sprint F. Once G closes the hito,
    # the manifest legitimately advances to G/POST-H-002. The F contract must
    # verify preservation of F evidence, not freeze the global pointer at F/G.
    allowed_transitions = {
        ("POST-H-EVAL-001-F", "POST-H-EVAL-001-G"),
        ("POST-H-EVAL-001-G", "POST-H-002"),
    }
    assert (manifest["current_micro_sprint"], manifest["next_micro_sprint"]) in allowed_transitions
    deliverable_paths = {
        item["path"] if isinstance(item, dict) else item
        for item in manifest.get("deliverables", [])
    }
    expected = {
        "docs/backlogs/post_h_prioritized_roadmap.md",
        "docs/adr/ADR-POSTH-001-local-first-before-remote.md",
        "docs/adr/ADR-POSTH-002-test-contract-registry-2.md",
        "docs/adr/ADR-POSTH-003-cli-modularization.md",
        ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json",
        "tests/test_post_h_eval_001_f_prioritized_roadmap.py",
    }
    assert expected.issubset(deliverable_paths)
