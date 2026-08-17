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
    assert not (ROOT/".devpilot/auth/auth.db").exists()


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
