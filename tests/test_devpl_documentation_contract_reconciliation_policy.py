from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def j(rel: str): return json.loads((ROOT/rel).read_text(encoding="utf-8"))

def test_contract_reconciliation_policy_is_approved_and_registered():
    text=(ROOT/"docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md").read_text(encoding="utf-8")
    for marker in ["doc_id:", "status: \"approved\"", "frozen-snapshot", "current-active", "successor-aware", "Contract Reconciliation Sweep", "do not run a second full regression"]:
        assert marker in text
    docs={x["path"] for x in j(".devpilot/docs_governance/source_registry.json")["documents"]}
    assert "docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md" in docs

def test_current_registry_derived_counters_are_reconciled():
    api=j(".devpilot/interfaces/api_route_contract_registry.json")
    ui=j(".devpilot/interfaces/ui_route_contract_registry.json")
    cap=j(".devpilot/interfaces/ui_capability_registry.json")
    rbac=j(".devpilot/identity/server_rbac_policy_catalog.json")
    sensitive=j(".devpilot/approval/sensitive_action_catalog.json")
    assert api["summary"]["routes_total"]==len(api["routes"])
    assert ui["summary"]["routes_total"]==len(ui["routes"])
    assert ui["summary"]["current_routes_total"]==len(ui["routes"])
    assert cap["summary"]["api_routes_total"]==len(api["routes"])
    assert cap["summary"]["ui_routes_total"]==len(ui["routes"])
    assert cap["summary"]["ui_routes_mapped_total"]==len(cap["ui_routes"])
    assert rbac["summary"]["route_policies_total"]==len(rbac["route_policies"])
    assert rbac["summary"]["sensitive_action_policies_total"]==len(rbac["sensitive_action_policies"])
    assert sensitive["summary"]["actions_total"]==len(sensitive["actions"])

def test_sensitive_action_cross_registry_mapping_is_total():
    sensitive=j(".devpilot/approval/sensitive_action_catalog.json")
    rbac=j(".devpilot/identity/server_rbac_policy_catalog.json")
    rules={x["rule_id"] for x in j(".devpilot/miasi/policy_matrix.json")["rules"]}
    tools={x["tool_id"] for x in j(".devpilot/miasi/tool_registry.json")["tools"]}
    assert {x["action_id"] for x in sensitive["actions"]}=={x["action_id"] for x in rbac["sensitive_action_policies"]}
    for action in sensitive["actions"]:
        assert set(action.get("miasi_policy_rule_ids",[])) <= rules
        assert set(action.get("tool_ids",[])) <= tools

def test_documentation_global_and_gsdlc_pointers_have_distinct_authority():
    state=j(".devpilot/project_state.json"); reg=j(".devpilot/docs_governance/source_registry.json")
    assert reg["last_registered_sprint"]==state["last_registered_sprint"]
    assert reg["gsdlc_last_registered_micro_sprint"]==state["gsdlc_current_micro_sprint"]
    assert reg["gsdlc_program_status"]==state["gsdlc_program_status"]

def test_02a_historical_sources_use_frozen_snapshots():
    assert (ROOT/".devpilot/identity/identity_registry_gsdlc02a_at_close.json").is_file()
    assert (ROOT/".devpilot/approval/sensitive_action_catalog_gsdlc02a_at_close.json").is_file()


def test_runtime_ephemeral_sandbox_exclusions_are_executable_contract(tmp_path):
    from shutil import copytree, ignore_patterns

    from devpilot_core.interfaces.api.operator_flow_smoke import (
        OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS,
    )

    required = {"auth.db*", "devpilot.db*"}
    assert required <= set(OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS)

    source = tmp_path / "source"
    destination = tmp_path / "destination"
    auth = source / ".devpilot" / "auth"
    auth.mkdir(parents=True)
    (auth / "auth.db").write_bytes(b"runtime")
    (auth / "auth.db-wal").write_bytes(b"runtime")
    (source / ".devpilot" / "devpilot.db").write_bytes(b"runtime")
    (source / ".devpilot" / "devpilot.db-shm").write_bytes(b"runtime")
    (source / ".devpilot" / "keep.json").write_text("{}\n", encoding="utf-8")

    copytree(
        source,
        destination,
        ignore=ignore_patterns(*OPERATOR_FLOW_RUNTIME_SANDBOX_IGNORE_PATTERNS),
    )

    assert not list(destination.rglob("auth.db*"))
    assert not list(destination.rglob("devpilot.db*"))
    assert (destination / ".devpilot" / "keep.json").is_file()

    uoc_fixture = (ROOT / "tests/uoc006_fixtures.py").read_text(encoding="utf-8")
    assert '"auth.db*"' in uoc_fixture
    assert '"devpilot.db*"' in uoc_fixture
