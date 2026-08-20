from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]


def read(rel: str):
    return json.loads((ROOT/rel).read_text(encoding="utf-8"))


def test_auth_contract_schemas_are_valid_and_reject_secret_source_shape() -> None:
    for rel in [
        "docs/schemas/local_identity.schema.json",
        "docs/schemas/credential_record.schema.json",
        "docs/schemas/session_record.schema.json",
        "docs/schemas/authenticated_principal.schema.json",
    ]:
        Draft202012Validator.check_schema(read(rel))
    credential=read("docs/schemas/credential_record.schema.json")
    assert "password" not in credential["properties"]
    assert "plaintext" not in json.dumps(credential).lower()
    session=read("docs/schemas/session_record.schema.json")
    assert "token_hash" not in session["properties"] and "csrf_hash" not in session["properties"]


def test_runtime_auth_store_is_source_and_evidence_excluded() -> None:
    gitignore=(ROOT/".gitignore").read_text(encoding="utf-8")
    proof=read("docs/audits/DEVPL_GSDLC_02_B_RUNTIME_STORE_EXCLUSION.json")
    assert ".devpilot/auth/" in gitignore
    assert proof["source_zip_allowed"] is False
    assert proof["evidence_zip_allowed"] is False
    # Runtime auth state may legitimately exist during a browser/full-regression session.
    # The invariant is exclusion from source/evidence, not physical non-existence at runtime.
    assert ".devpilot/auth/" in gitignore
    assert proof["source_zip_allowed"] is False and proof["evidence_zip_allowed"] is False


def test_02_a_closure_authority_and_historical_boundaries_are_preserved() -> None:
    adj=read("DEVPL_GSDLC_02_A_FINAL_OWNER_ADJUDICATION_v1_0_0.json")
    assert adj["decision"]=="CLOSED/PASS"
    assert adj["successor_commit"]=="6f338a25b5463742576c82aa7dbee958fbca8587"
    post=(ROOT/"docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md").read_text(encoding="utf-8")
    assert "continue-blocked" in post
    assert "production_multiuser_enabled: false" in post


def test_b_docs_are_explicitly_initial_and_defer_rbac_approval_ui() -> None:
    contract=(ROOT/"docs/03_security/local_identity_session_contract.md").read_text(encoding="utf-8")
    assert "preliminary/initial" in contract
    assert "GSDLC-02-C" in contract and "GSDLC-02-D" in contract
    assert "GSDLC-02-E" in (ROOT/"docs/05_operations/local_auth_session_runbook.md").read_text(encoding="utf-8")

def test_02_b_api_route_registry_is_current_active_successor() -> None:
    registry=read(".devpilot/interfaces/api_route_contract_registry_gsdlc02d_at_close.json")
    assert registry["summary"]["routes_total"] == 97
    successor_03a=read(".devpilot/interfaces/api_route_contract_registry_gsdlc03a_at_close.json")
    assert successor_03a["summary"]["routes_total"] == 98
    current=read(".devpilot/interfaces/api_route_contract_registry.json")
    frozen_03b=read(".devpilot/interfaces/api_route_contract_registry_gsdlc03b_at_close.json")
    assert frozen_03b["summary"]["routes_total"] == 100
    assert current["summary"]["routes_total"] >= 100
    assert current["summary"]["gsdlc_03_b_project_entry_routes_total"] == 2
    assert registry["summary"]["gsdlc_02_b_auth_routes_total"] == 7
    auth_routes={(r["method"],r["path"]) for r in registry["routes"] if r["path"].startswith("/api/v1/auth/")}
    assert {
        ("GET","/api/v1/auth/bootstrap/status"),
        ("POST","/api/v1/auth/bootstrap/owner"),
        ("POST","/api/v1/auth/login"),
        ("GET","/api/v1/auth/session"),
        ("POST","/api/v1/auth/session/rotate"),
        ("POST","/api/v1/auth/logout"),
        ("POST","/api/v1/auth/session/revoke"),
    }.issubset(auth_routes)

    assert registry["summary"]["remote_execution_allowed_total"] == 0
    assert registry["summary"]["external_api_routes_total"] == 0


def test_02_c_capability_route_is_current_active_successor() -> None:
    registry=read(".devpilot/interfaces/api_route_contract_registry.json")
    rows=[r for r in registry["routes"] if r["operation"]=="auth.capabilities"]
    assert len(rows)==1 and rows[0]["path"]=="/api/v1/auth/capabilities"
