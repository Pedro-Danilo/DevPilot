from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_01_c_state_closes_and_authorizes_01_d() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["current_repo"].startswith("repo_DevPilot_Local_")
    # current_repo is a global mutable lifecycle pointer; later GSDLC baselines
    # are valid successors even when the historical POST-H-EVAL-002 marker is absent.
    assert int(state["current_repo"].split("_", 4)[3]) >= 321
    assert state["post_h_eval_002_current_micro_sprint"] in {"POST-H-EVAL-002-01-D", "POST-H-EVAL-002-02-A", "POST-H-EVAL-002-02-B"}
    assert state["post_h_eval_002_next_micro_sprint"] in {"POST-H-EVAL-002-02-A", "POST-H-EVAL-002-02-B", "POST-H-EVAL-002-02-C"}
    assert state["post_h_eval_002_01_c_closed"] is True
    assert state["post_h_eval_002_01_c_status"] == "closed/PASS-WITH-GAPS"
    assert state["post_h_eval_002_01_c_s0_open"] == 0
    assert state["post_h_eval_002_01_c_s1_open"] == 0
    assert state["post_h_eval_002_01_c_next_authorized"] == "POST-H-EVAL-002-01-D"


def test_01_c_evidence_hashes_and_results_are_frozen() -> None:
    manifest = _json("docs/post_h_eval_002_01_c_manifest.json")
    assert manifest["decision"] == "PASS-WITH-GAPS"
    assert manifest["evidence"]["final_package"]["sha256"] == "c962739b1c9f9045ea872be9b576f6045aa41268261b1aab5bc3ae629824d8a5"
    assert manifest["evidence"]["priority_package"]["sha256"] == "4c5596d09c4208ccd092f42f110e8b23609b1d4de98166140fc26ac9b95407c5"
    assert manifest["evidence"]["operator_log_sha256"] == "3b1678386b9b3f3c6605674df401f36b6b078966d1f25e6360e80c4fe9f990cc"
    assert manifest["results"]["checks_passed"] == manifest["results"]["checks_total"] == 41
    assert manifest["results"]["commands_passed"] == manifest["results"]["commands_total"] == 12
    assert manifest["results"]["secret_findings"] == 0
    assert manifest["results"]["ports_released"] is True


def test_01_c_security_and_process_lifecycle_are_recorded() -> None:
    state = _json(".devpilot/project_state.json")
    assert state["post_h_eval_002_01_c_api_started"] is True
    assert state["post_h_eval_002_01_c_ui_started"] is True
    assert state["post_h_eval_002_01_c_nonlocal_bind_allowed"] is False
    assert state["post_h_eval_002_01_c_token_generated"] is True
    assert state["post_h_eval_002_01_c_token_persisted"] is False
    assert state["post_h_eval_002_01_c_token_in_url"] is False
    assert state["post_h_eval_002_01_c_cors_wildcard_enabled"] is False
    assert state["post_h_eval_002_01_c_cors_local_origin_allowed"] is True
    assert state["post_h_eval_002_01_c_cors_untrusted_origin_rejected"] is True
    assert state["post_h_eval_002_01_c_cors_preflight_local_allowed"] is True
    assert state["post_h_eval_002_01_c_cors_preflight_untrusted_rejected"] is True
    assert state["post_h_eval_002_01_c_processes_stopped"] is True
    assert state["post_h_eval_002_01_c_ports_released"] is True


def test_01_c_preserves_freeze_and_scope_boundary() -> None:
    state = _json(".devpilot/project_state.json")
    manifest = _json("docs/post_h_eval_002_01_c_manifest.json")
    assert state["source_repo"] == "repo_DevPilot_Local_318_POST_H_EVAL_002_PILOT_READY.zip"
    assert state["post_h_eval_002_01_c_workspace_created"] is False
    assert state["post_h_eval_002_01_c_browser_acceptance_executed"] is False
    assert manifest["scope"]["platform_source_changed"] is False
    assert manifest["scope"]["browser_acceptance_executed"] is False
    for key in (
        "connector_write_enabled",
        "plugin_execution_enabled",
        "remote_execution_enabled",
        "production_multiuser_enabled",
        "enterprise_ready_claimed",
        "saas_ready_claimed",
        "external_api_allowed",
    ):
        assert state[key] is False


def test_01_c_governance_docs_are_synchronized() -> None:
    # 01-C owns immutable closure facts; it must not own the mutable current
    # roadmap status after the pilot is paused or successor programs advance.
    manifest = _json("docs/post_h_eval_002_01_c_manifest.json")
    backlog = _text("docs/backlogs/POST-H-EVAL-002-01_baseline_ui_acceptance.md")
    audit = _text("docs/audits/post_h_eval_002_01_c_api_ui_startup_security_posture_report.md")
    assert manifest["status"] == "closed"
    assert manifest["decision"] == "PASS-WITH-GAPS"
    assert manifest["evidence"]["final_package"]["sha256"] == "c962739b1c9f9045ea872be9b576f6045aa41268261b1aab5bc3ae629824d8a5"
    assert 'current_micro_sprint: "POST-H-EVAL-002-02-A"' in backlog
    assert 'next_micro_sprint: "POST-H-EVAL-002-02-B"' in backlog
    assert "`PASS-WITH-GAPS`" in audit
    assert "formal browser acceptance" in audit
    registry = _json(".devpilot/docs_governance/source_registry.json")
    snapshot = registry["project_state_snapshot"]
    assert snapshot["post_h_eval_002_01_c_evidence_package_sha256"] == "c962739b1c9f9045ea872be9b576f6045aa41268261b1aab5bc3ae629824d8a5"
    # Keep the frozen 01-C evidence SHA above, but bind the mutable registry
    # pointer to the latest UOC represented in Project State instead of an
    # allowlist that must be extended at every sprint.
    state = _json(".devpilot/project_state.json")
    realized = [
        int(key[4:7])
        for key, value in state.items()
        if key.startswith("uoc_")
        and key.endswith("_status")
        and key[4:7].isdigit()
        and str(value).strip().lower().startswith(("implemented", "closed"))
    ]
    if realized:
        latest = max(realized)
        status_key = f"uoc_{latest:03d}_status"
        assert str(state[status_key]).lower().startswith("closed")
        assert registry["project_state_snapshot"][status_key] == state[status_key]
        assert registry["last_registered_sprint"] == state["last_registered_sprint"]
