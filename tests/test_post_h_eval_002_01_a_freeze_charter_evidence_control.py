from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_01_a_state_advances_without_installing_platform_or_workspace() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["source_repo"] == "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
    assert state["post_h_eval_002_governance_repo"] in {
        "repo_DevPilot_Local_319_POST_H_EVAL_002_01_A.zip",
        "repo_DevPilot_Local_320_POST_H_EVAL_002_01_B.zip",
        "repo_DevPilot_Local_321_POST_H_EVAL_002_01_C.zip",
        "repo_DevPilot_Local_322_POST_H_EVAL_002_01_D_ACCEPTANCE_READY.zip",
        "repo_DevPilot_Local_323_POST_H_EVAL_002_01_D_UI_ACCEPTANCE_FIX.zip",
    }
    assert state["current_micro_sprint"].startswith("POST-H-EVAL-002-01-")
    assert state["post_h_eval_002_01_a_closed"] is True
    assert state["post_h_eval_002_01_a_platform_frozen"] is True
    assert state["post_h_eval_002_01_a_platform_installed"] is False
    assert state["post_h_eval_002_01_a_workspace_created"] is False
    assert state["post_h_eval_002_01_a_s0_open"] == 0
    assert state["post_h_eval_002_01_a_s1_open"] == 0
    assert state["post_h_eval_002_01_a_evidence_package_sha256"] == "f6385f047db79f0b02ae01d7c73b1d2d784f1a1acfc6361863e79917935618dc"
    registry = _json(".devpilot/docs_governance/source_registry.json")
    assert registry["project_state_snapshot"]["post_h_eval_002_01_a_evidence_package_sha256"] == state["post_h_eval_002_01_a_evidence_package_sha256"]
    assert registry["project_state_snapshot"]["post_h_eval_002_01_a_status"] == state["post_h_eval_002_01_a_status"] == "closed/PASS"


def test_01_a_manifest_and_audit_reference_external_evidence_package() -> None:
    manifest = _json("docs/post_h_eval_002_01_a_manifest.json")
    audit = _text("docs/audits/post_h_eval_002_01_a_freeze_charter_evidence_control_report.md")
    assert manifest["run_id"] == "PILOT-E2E-001-RUN-01"
    assert manifest["evidence_package"]["sha256"] == "f6385f047db79f0b02ae01d7c73b1d2d784f1a1acfc6361863e79917935618dc"
    assert manifest["evidence_package"]["baseline_sha256"] == "bf5c10df92a104a9c212c19db28d518eff0d5e5a671b4b35ec71bfd79c7df308"
    assert manifest["incidents"] == {"s0_open": 0, "s1_open": 0}
    assert "`PASS`" in audit


def test_01_a_provenance_distinguishes_functional_and_packaging_commits() -> None:
    manifest = _json("docs/post_h_eval_002_01_a_manifest.json")
    evidence = manifest["evidence_package"]
    assert evidence["functional_anchor_commit_short"] == "0c7741f"
    assert evidence["packaged_r1_commit_short"] == "2c5f209"
    assert evidence["functional_anchor_commit_short"] != evidence["packaged_r1_commit_short"]


def test_01_a_no_active_baseline_315_instruction_remains() -> None:
    roadmap = _text("docs/00_product/POST-H-EVAL-002_end_to_end_product_pilot_roadmap.md")
    backlog = _text("docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md")
    assert "baseline 315 instalado y verificado" not in roadmap
    assert "baseline 318 instalado y verificado" in roadmap
    assert "instalar DevPilot desde el ZIP 315" not in backlog


def test_01_a_sensitive_capabilities_remain_disabled() -> None:
    state = _json(".devpilot/project_state.json")
    for key in ("connector_write_enabled", "plugin_execution_enabled", "remote_execution_enabled", "production_multiuser_enabled", "enterprise_ready_claimed", "saas_ready_claimed", "external_api_allowed"):
        assert state[key] is False
