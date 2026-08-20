from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

def git_blob_sha(rel: str) -> str:
    cp = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.resolve()}", "show", f"HEAD:{rel.replace('\\\\', '/')}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert cp.returncode == 0, cp.stderr.decode("utf-8", errors="replace")
    return hashlib.sha256(cp.stdout).hexdigest()

EXPECTED_ROLES = {"owner","product-owner","architect","security-reviewer","developer","qa-reviewer","release-manager","operator","agent-supervisor"}

def test_schemas_validate_positive_instances_and_reject_negative():
    pairs=[
      ("docs/schemas/auth_threat_matrix.schema.json", ".devpilot/identity/auth_threat_matrix.json"),
      ("docs/schemas/role_authority_matrix.schema.json", ".devpilot/identity/role_authority_matrix.json"),
      ("docs/schemas/legacy_role_migration_map.schema.json", ".devpilot/identity/legacy_role_migration_map.json"),
    ]
    for schema_rel, instance_rel in pairs:
        schema=load(schema_rel); instance=load(instance_rel)
        Draft202012Validator(schema).validate(instance)
        bad=dict(instance); bad["micro_sprint"]="WRONG"
        assert list(Draft202012Validator(schema).iter_errors(bad))

def test_threat_coverage_is_complete_and_design_only():
    m=load(".devpilot/identity/auth_threat_matrix.json")
    assert len(m["threats"]) == 18
    assert len(m["controls"]) == 18
    assert m["coverage"]["coverage_percent"] == 100.0
    assert m["coverage"]["threats_without_control"] == 0
    control_ids={c["control_id"] for c in m["controls"]}
    for t in m["threats"]:
        assert t["controls"]
        assert set(t["controls"]) <= control_ids
        assert t["implementation_sprints"]
        assert t["test_evidence"]
        assert t["runtime_enforced_in_02_a"] is False
    assert m["runtime_auth_enabled"] is False
    assert m["remote_login_enabled"] is False
    assert m["public_api_enabled"] is False

def test_every_canonical_role_is_bounded_and_fail_closed():
    m=load(".devpilot/identity/role_authority_matrix.json")
    roles=m["roles"]
    assert {r["role_id"] for r in roles} == EXPECTED_ROLES
    assert len(roles) == 9
    assert m["runtime_enforced"] is False
    assert m["deny_by_default"] is True
    assert m["constraints"]["role_self_escalation_allowed"] is False
    assert m["constraints"]["unknown_role_effect"] == "DENY"
    assert m["constraints"]["unknown_action_effect"] == "DENY"
    assert m["constraints"]["legacy_token_human_authority"] is False
    assert m["constraints"]["client_actor_authoritative"] is False
    for r in roles:
        assert r["permissions"] and r["workspace_scope"]
        assert r["separation_of_duties"]
        assert r["self_modification"].startswith("deny")

def test_legacy_roles_are_explicitly_mapped_without_silent_rename():
    snap=load(".devpilot/identity/identity_registry_gsdlc02a_at_close.json")
    mig=load(".devpilot/identity/legacy_role_migration_map.json")
    source_roles={r["role_id"] for r in snap["roles"]}
    mapping={m["source_role"]:m for m in mig["mappings"]}
    assert source_roles == {"owner","architect","developer","reviewer","operator","agent-supervisor"}
    assert source_roles <= set(mapping)
    assert mapping["reviewer"]["decision"] == "PROPOSED_ALIAS_NOT_APPLIED"
    assert mapping["reviewer"]["target_roles"] == ["qa-reviewer"]
    assert "security-reviewer" not in mapping["reviewer"]["target_roles"]
    assert mig["safety"]["silent_rename_allowed"] is False
    assert mig["runtime_applied"] is False

def test_catalog_only_maintainer_is_fail_closed_until_02_c():
    cat=load(".devpilot/approval/sensitive_action_catalog_gsdlc02a_at_close.json")
    mig=load(".devpilot/identity/legacy_role_migration_map.json")
    mapping={m["source_role"]:m for m in mig["mappings"]}
    acts=[a for a in cat["actions"] if a.get("requires_rbac_role")=="maintainer"]
    assert {a["action_id"] for a in acts} == {"patch.apply","refactor.execute","filesystem.delete"}
    assert all(a["status"]=="blocked" and a["executable"] is False for a in acts)
    assert mapping["maintainer"]["decision"] == "NO_DIRECT_MAPPING_FAIL_CLOSED"
    assert mapping["maintainer"]["target_roles"] == []
    assert mig["safety"]["maintainer_actions_must_remain_blocked_until_02_c"] is True

def test_historical_auth_boundaries_match_canonical_git_blobs():
    assert git_blob_sha("docs/backlogs/POST-H-012_approval_rbac_hardening.md") == "e20b2d3eecd5d75071c3f04e7371605a6178a12ecd7343347f183f5e6d74cfca"
    assert git_blob_sha("docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md") == "eca822d29e3c024c1cd894fa14797971a6bdeebb4f090714a95b3f48588281af"
    assert git_blob_sha("docs/02_architecture/adrs/ADR-GSDLC-003-local-authenticated-operator-boundary.md") == "2c30534da5ee04f9e0eb36033202fa29b07d311bea196ab059b91d9acfb0bb8d"
    adr=load_json_frontmatter(ROOT / "docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md")
    assert adr["decision_status"] == "continue-blocked"
    assert adr["multiuser_auth_enabled"] is False
    assert adr["production_multiuser_enabled"] is False
    assert adr["public_api_enabled"] is False

def load_json_frontmatter(path: Path):
    text=path.read_text(encoding="utf-8")
    lines=text.splitlines()
    assert lines[0]=="---"
    out={}
    for line in lines[1:]:
        if line=="---": break
        if ":" not in line: continue
        k,v=line.split(":",1); v=v.strip().strip('"')
        if v.lower() in {"true","false"}: out[k.strip()]=v.lower()=="true"
        else: out[k.strip()]=v
    return out

def test_successor_adr_is_design_only_and_enterprise_no_go():
    fm=load_json_frontmatter(ROOT / "docs/02_architecture/adrs/ADR-GSDLC-005-local-operator-auth-enablement.md")
    assert fm["runtime_implemented"] is False
    assert fm["runtime_enabled"] is False
    assert fm["remote_login_enabled"] is False
    assert fm["public_api_enabled"] is False
    assert fm["enterprise_iam_enabled"] is False
    assert fm["tenancy_enabled"] is False

def test_no_login_session_routes_were_introduced_in_02_a():
    snap=load(".devpilot/interfaces/api_route_contract_registry_gsdlc02a_at_close.json")
    assert len(snap["routes"]) == 89
    forbidden=("login","session","logout","bootstrap-owner","first-run")
    for route in snap["routes"]:
        material=(str(route.get("route_id",""))+" "+str(route.get("path",""))).lower()
        assert not any(token in material for token in forbidden)

def test_02_a_frozen_runtime_sources_match_repo353_canonical_git_blobs():
    # 02-A intentionally froze the identity registry and sensitive-action catalog:
    # their runtime migration/enforcement belongs to successor micro-sprints.
    # The API route registry is NOT historical-freeze: 02-B correctly evolves it
    # with seven current-active local-auth routes, so freezing its repo353 blob
    # here would make the 02-A test contradict the approved successor contract.
    def frozen_sha(rel: str) -> str:
        raw=(ROOT/rel).read_bytes().replace(b"\r\n", b"\n")
        return hashlib.sha256(raw).hexdigest()
    assert frozen_sha(".devpilot/identity/identity_registry_gsdlc02a_at_close.json") == "cea4055e1c7ed23fd7e6057e62a7747a9c64e2e4e6f325b2620803bf9f269799"
    assert frozen_sha(".devpilot/approval/sensitive_action_catalog_gsdlc02a_at_close.json") == "df93533193c1bc143c019f5a2dec79644599f11fa30d3bde03eeb8468c239585"

def test_project_state_keeps_auth_runtime_disabled_and_defers_full_regression():
    state=load(".devpilot/project_state.json")
    assert state["multiuser_auth_enabled"] is False
    assert state["production_multiuser_enabled"] is False
    assert state["public_api_enabled"] is False
    assert state["gsdlc_02_a_runtime_auth_enabled"] is False
    assert state["gsdlc_02_a_login_routes_added"] == 0
    assert state["gsdlc_02_a_session_runtime_enabled"] is False
    assert state["gsdlc_02_a_full_regression_enforced"] is False
    assert state["gsdlc_02_a_full_regression_deferred_to"] == "DEVPL-GSDLC-02-E"
    assert state["gsdlc_02_b_authorized"] is False
