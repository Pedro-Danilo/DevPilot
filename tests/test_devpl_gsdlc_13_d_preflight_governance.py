from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def j(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_pre13d_authority_override_resolves_legacy_pointer_ambiguity() -> None:
    ps = j(".devpilot/project_state.json")
    sr = j(".devpilot/docs_governance/source_registry.json")
    auth = j(".devpilot/gsdlc/gsdlc13_d_preflight_authority.json")

    assert ps["gsdlc_13_d_preflight_status"].startswith("PASS/")
    assert sr["gsdlc_13_d_preflight_status"].startswith("PASS/")
    assert auth["finding_resolved"] == "GOV-13D-PREFLIGHT-001"
    assert auth["resolution_mode"] == "authority-override/non-functional"
    assert auth["execution_authority"]["functional_baseline_repo"] == "repo451_C04_BR_108_WINDOWS_VALIDATED_CANDIDATE.zip"
    assert auth["execution_authority"]["functional_baseline_commit"] == "bb06260ce94298bf1e9dbb798e057d7ad07ea459"
    assert auth["execution_authority"]["functional_baseline_sha256"] == "7bc2e7c5185d28c195161e6eaaece4c4258e084f3805766f70586b381b9bcc4c"
    assert auth["legacy_pointer_policy"]["historical_snapshots_mutated"] is False
    assert auth["execution_authority"]["head_validation_policy"]["runtime_api_ui_source_delta_allowed"] is False
    assert ps["gsdlc_13_d_legacy_current_pointer_policy"].startswith("NON-AUTHORITATIVE-FOR-13D")
    assert sr["gsdlc_13_d_legacy_current_pointer_policy"].startswith("NON-AUTHORITATIVE-FOR-13D")


def test_pilot_a_is_frozen_as_deterministic_pre_multiprovider_lineage() -> None:
    lineage = j(".devpilot/gsdlc/gsdlc13_pilot_a_deterministic_lineage.json")
    assert lineage["status"] == "FROZEN/DETERMINISTIC/PRE-MULTIPROVIDER"
    assert lineage["devpilot_engine_baseline"]["functional_commit"] == "bb06260ce94298bf1e9dbb798e057d7ad07ea459"
    assert lineage["model_posture"]["multiprovider_e1_e2_e3_adopted"] is False
    assert lineage["model_posture"]["external_api_required"] is False
    assert lineage["branching_policy"]["pilot_a_must_not_receive_e1_e2_e3_features"] is True
    assert lineage["project_content_policy"]["operator_project_writes_allowed"] is False
    assert lineage["release_policy"]["full_regression_runs_in_13d"] == 0


def test_audit_aligned_successors_are_approved_and_active() -> None:
    required = [
        "SPRINT_DEVPL_GSDLC_13_D_v1_2_0_APPROVED.md",
        "04_PROMPT_DEVPL_GSDLC_13_D_v1_2_0_APPROVED.md",
        "docs/05_operations/DEVPL_GSDLC_13_GREENFIELD_USER_JOURNEY_RUNBOOK_v1_1_0_APPROVED.md",
        "docs/validation/DEVPL_GSDLC_13_ACCEPTANCE_CHECKPOINT_PROTOCOL_v1_1_0_APPROVED.md",
        "docs/validation/RUN_CARD_13_D_01_v1_0_3_APPROVED.md",
    ]
    for rel in required:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert 'status: "approved"' in text

    sr = j(".devpilot/docs_governance/source_registry.json")
    by_id = {item["doc_id"]: item for item in sr["documents"]}
    assert by_id["DEVPL-GSDLC-13-GREENFIELD-USER-JOURNEY-RUNBOOK"]["path"].endswith("v1_1_0_APPROVED.md")
    assert by_id["DEVPL-GSDLC-13-ACCEPTANCE-CHECKPOINT-PROTOCOL"]["path"].endswith("v1_1_0_APPROVED.md")
    assert by_id["DEVPL-GSDLC-13-D-01-RUN-CARD"]["path"].endswith("RUN_CARD_13_D_01_v1_0_3_APPROVED.md")


def test_pre13d_changes_are_governance_only_and_d01_policy_is_zero_full() -> None:
    ps = j(".devpilot/project_state.json")
    auth = j(".devpilot/gsdlc/gsdlc13_d_preflight_authority.json")
    assert ps["gsdlc_13_d_full_regression_runs_allowed"] == 0
    assert ps["gsdlc_13_d_operator_project_writes_allowed"] is False
    assert ps["gsdlc_13_d_multiprovider_adopted"] is False
    assert ps["gsdlc_13_d_next_checkpoint"] == "13-D-01"
    assert auth["safety"]["functional_runtime_changed"] is False
    assert auth["safety"]["ui_runtime_changed"] is False
    assert auth["safety"]["api_runtime_changed"] is False
    assert auth["safety"]["full_regression_runs_allowed"] == 0


def test_d01_run_card_v103_windows_environment_and_evidence_contract() -> None:
    text = (
        ROOT / "docs/validation/RUN_CARD_13_D_01_v1_0_3_APPROVED.md"
    ).read_text(encoding="utf-8")

    assert 'version: "1.0.3"' in text
    assert '.venv\\Scripts\\python.exe' in text
    assert 'import fastapi,uvicorn' in text
    assert '& $Py -m devpilot_core api serve' in text
    assert 'pip install' not in text
    assert 'operator_project_writes=0' in text
    assert 'normal_user_terminal_escapes=0' in text
    assert 'no Full Regression' in text

    for required in [
        "audit_13_D_01_RUN_02.txt",
        "api_13_D_01_RUN_02.txt",
        "ui_13_D_01_RUN_02.txt",
        "START_STATE_13_D_01_RUN_02.json",
        "MANUAL_OBSERVATIONS_13_D_01_RUN_02.md",
        "01_project_status_initial.png",
        "02_planning_frozen_implementing_ready.png",
        "03_story_code_activation_panel_ready.png",
        "04_ready_story_before_prepare.png",
        "05_dor_context_pack_planned.png",
        "07_context_reviewability.png",
        "08_implementation_route_provenance.png",
        "09_stop_before_d02.png",
        "99_block_state.png",
        "RUN_PACKET_13_D_01_RUN_02.zip",
    ]:
        assert required in text
