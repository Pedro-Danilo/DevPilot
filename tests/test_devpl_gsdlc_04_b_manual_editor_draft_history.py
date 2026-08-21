from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application.artifact_draft_service import ArtifactDraftApplicationService
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.application import AuthApplicationService
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / f"gsdlc04b-{tmp_path.name}"
    docs = root / "docs"
    docs.mkdir(parents=True)
    md = docs / "requirements.md"
    md.write_text("# Requirements\n\nInitial source.\n", encoding="utf-8")
    js = docs / "architecture.json"
    js.write_text('{"version": 1}\n', encoding="utf-8")
    yaml = docs / "legacy.yaml"
    yaml.write_text("version: 1\n", encoding="utf-8")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    yield root
    token = hashlib.sha256(root.name.encode("utf-8")).hexdigest()[:20]
    shutil.rmtree(ROOT / "outputs" / "drafts" / "gsdlc_04_b" / token, ignore_errors=True)


def _service() -> tuple[WorkspaceDocumentsApplicationService, ArtifactDraftApplicationService]:
    documents = WorkspaceDocumentsApplicationService(ROOT)
    return documents, ArtifactDraftApplicationService(ROOT, documents=documents)


def _document(documents: WorkspaceDocumentsApplicationService, relative_path: str) -> dict:
    listed = documents.list_documents(limit=100)
    assert listed.ok, listed.to_dict()
    node = next(item for item in listed.data["nodes"] if item.get("relative_path") == relative_path)
    read = documents.read_document(node["document_id"])
    assert read.ok, read.to_dict()
    return read.data["document"]


def _save(service: ArtifactDraftApplicationService, document: dict, content: str, expected_revision: str | None = None, event: str = "SAVE"):
    return service.save(
        document_id=document["document_id"],
        content=content,
        expected_source_sha256=document["sha256"],
        expected_revision_sha256=expected_revision,
        actor="local-owner",
        actor_role="owner",
        session_principal="local-owner",
        event=event,
    )


def test_manual_draft_save_is_runtime_only_and_schema_backed(workspace: Path) -> None:
    documents, service = _service(); document = _document(documents, "docs/requirements.md")
    before = (workspace / "docs" / "requirements.md").read_bytes()
    result = _save(service, document, "# Requirements\n\nDraft only.\n")
    assert result.ok, result.to_dict()
    draft = result.data["draft"]
    assert draft["source_type"] == "MANUAL" and draft["lifecycle_state"] == "DRAFT"
    assert draft["approved_evidence"] is False and draft["source_mutations_performed"] is False
    assert len(draft["revisions"]) == 1 and draft["revisions"][0]["event"] == "SAVE"
    assert (workspace / "docs" / "requirements.md").read_bytes() == before
    persisted = service.get(document_id=document["document_id"])
    assert persisted.ok and persisted.data["draft"]["current_revision_sha256"] == draft["current_revision_sha256"]


def test_autosave_is_idempotent_and_restart_recovers_draft(workspace: Path) -> None:
    documents, service = _service(); document = _document(documents, "docs/requirements.md")
    first = _save(service, document, "# Requirements\n\nAutosaved.\n", event="AUTOSAVE")
    sha = first.data["draft"]["current_revision_sha256"]
    duplicate = _save(service, document, "# Requirements\n\nAutosaved.\n", expected_revision=sha, event="AUTOSAVE")
    assert duplicate.ok and duplicate.data["summary"]["idempotent"] is True
    restarted = ArtifactDraftApplicationService(ROOT, documents=WorkspaceDocumentsApplicationService(ROOT))
    loaded = restarted.get(document_id=document["document_id"])
    assert loaded.ok and len(loaded.data["draft"]["revisions"]) == 1
    assert loaded.data["draft"]["revisions"][0]["content"].endswith("Autosaved.\n")


def test_optimistic_concurrency_blocks_stale_revision(workspace: Path) -> None:
    documents, service = _service(); document = _document(documents, "docs/requirements.md")
    first = _save(service, document, "draft one")
    current = first.data["draft"]["current_revision_sha256"]
    second = _save(service, document, "draft two", expected_revision=current)
    assert second.ok
    stale = _save(service, document, "lost update", expected_revision=current)
    assert stale.ok is False and stale.exit_code.value == 2
    assert any(f.id == "GSDLC04B_OPTIMISTIC_CONCURRENCY_CONFLICT_BLOCK" for f in stale.findings)


def test_source_preimage_drift_blocks_save_and_does_not_overwrite(workspace: Path) -> None:
    documents, service = _service(); document = _document(documents, "docs/requirements.md")
    first = _save(service, document, "draft before external edit")
    revision = first.data["draft"]["current_revision_sha256"]
    (workspace / "docs" / "requirements.md").write_text("# External edit\n", encoding="utf-8")
    fresh_document = _document(documents, "docs/requirements.md")
    assert fresh_document["sha256"] != document["sha256"]
    blocked = service.save(document_id=document["document_id"], content="should not win", expected_source_sha256=fresh_document["sha256"], expected_revision_sha256=revision, actor="local-owner", actor_role="owner", session_principal="local-owner")
    assert blocked.ok is False and "source" in blocked.message.lower()
    assert (workspace / "docs" / "requirements.md").read_text(encoding="utf-8") == "# External edit\n"


def test_discard_retains_history_and_recover_creates_new_revision(workspace: Path) -> None:
    documents, service = _service(); document = _document(documents, "docs/requirements.md")
    first = _save(service, document, "revision one")
    r1 = first.data["draft"]["current_revision_sha256"]
    second = _save(service, document, "revision two", expected_revision=r1)
    r2 = second.data["draft"]["current_revision_sha256"]
    discarded = service.discard(document_id=document["document_id"], expected_source_sha256=document["sha256"], expected_revision_sha256=r2, actor="local-owner", actor_role="owner", session_principal="local-owner")
    assert discarded.ok and discarded.data["draft"]["active"] is False
    recovered = service.recover(document_id=document["document_id"], revision_sha256=r1, expected_source_sha256=document["sha256"], expected_revision_sha256=None, actor="local-owner", actor_role="owner", session_principal="local-owner")
    assert recovered.ok
    latest = recovered.data["draft"]["revisions"][-1]
    assert latest["event"] == "RECOVER" and latest["recovered_from_sha256"] == r1 and latest["revision_sha256"] != r1
    assert len(recovered.data["draft"]["revisions"]) == 3


def test_unsupported_type_and_secret_like_content_fail_closed(workspace: Path) -> None:
    documents, service = _service(); yaml = _document(documents, "docs/legacy.yaml")
    blocked_type = _save(service, yaml, "version: 2")
    assert blocked_type.ok is False and any(f.id == "GSDLC04B_DRAFT_TYPE_BLOCK" for f in blocked_type.findings)
    md = _document(documents, "docs/requirements.md")
    secret = _save(service, md, "api_key=sk-proj-abcdefghijklmnop")
    assert secret.ok is False and any(f.id == "GSDLC04B_SECRET_DRAFT_BLOCK" for f in secret.findings)


def test_corrupt_runtime_store_fails_closed(workspace: Path) -> None:
    documents, service = _service(); document = _document(documents, "docs/requirements.md")
    saved = _save(service, document, "valid draft")
    assert saved.ok
    store_path = service._store_path(workspace.name, document["document_id"])
    store_path.write_text("{not-json", encoding="utf-8")
    loaded = service.get(document_id=document["document_id"])
    assert loaded.ok is False and any(f.id == "GSDLC04B_DRAFT_STORE_CORRUPT_BLOCK" for f in loaded.findings)


def _human_client(tmp_path: Path) -> TestClient:
    store = LocalAuthStore(tmp_path / "auth")
    auth = AuthApplicationService(tmp_path / "auth", store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-gsdlc04b", auth_service=auth))
    boot = client.post("/api/v1/auth/bootstrap/owner", json={"username":"owner.local","display_name":"Local Owner","password":PASSWORD}, headers=ORIGIN)
    assert boot.status_code == 201, boot.text
    return client


def _csrf_headers(client: TestClient) -> dict[str, str]:
    return {"Origin": ORIGIN["Origin"], CSRF_HEADER_NAME: str(client.cookies.get(CSRF_COOKIE_NAME))}


def test_api_draft_routes_require_human_session_and_bind_server_actor(workspace: Path, tmp_path: Path) -> None:
    unauthenticated = TestClient(create_app(ROOT, api_token="legacy-gsdlc04b"))
    doc_response = unauthenticated.get("/api/v1/workspace/documents?limit=100", headers={"X-DevPilot-Token":"legacy-gsdlc04b"})
    assert doc_response.status_code == 200
    document_id = next(x["document_id"] for x in doc_response.json()["data"]["nodes"] if x.get("relative_path") == "docs/requirements.md")
    legacy = unauthenticated.get(f"/api/v1/workspace/artifact-drafts/{document_id}", headers={"X-DevPilot-Token":"legacy-gsdlc04b"})
    assert legacy.status_code in {401, 403}

    client = _human_client(tmp_path)
    read = client.get(f"/api/v1/workspace/documents/{document_id}", headers={"X-DevPilot-Token":"legacy-gsdlc04b"})
    source_sha = read.json()["data"]["document"]["sha256"]
    saved = client.post(f"/api/v1/workspace/artifact-drafts/{document_id}/save", headers=_csrf_headers(client), json={"content":"# API draft\n","expected_source_sha256":source_sha,"expected_revision_sha256":None,"event":"SAVE"})
    assert saved.status_code == 200, saved.text
    draft = saved.json()["data"]["draft"]
    assert draft["author_actor"] == "local-owner" and draft["session_principal"] == "local-owner"
    assert draft["source_mutations_performed"] is False


def test_api_route_security_and_rbac_contracts_are_explicit() -> None:
    expected = {
        ("GET", "/api/v1/workspace/artifact-drafts/{document_id}"),
        ("GET", "/api/v1/workspace/artifact-drafts/{document_id}/history"),
        ("POST", "/api/v1/workspace/artifact-drafts/{document_id}/save"),
        ("POST", "/api/v1/workspace/artifact-drafts/{document_id}/discard"),
        ("POST", "/api/v1/workspace/artifact-drafts/{document_id}/recover"),
    }
    assert expected <= set(API_ROUTE_POLICIES)
    assert resolve_route_policy("POST", "/api/v1/workspace/artifact-drafts/doc_abc/save").operation == "workspace.artifact_drafts.save"
    catalog = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    policies = {x["route_id"]: x for x in catalog["route_policies"]}
    for route_id in ["api.workspace.artifact-drafts.get","api.workspace.artifact-drafts.history","api.workspace.artifact-drafts.save","api.workspace.artifact-drafts.discard","api.workspace.artifact-drafts.recover"]:
        assert policies[route_id]["human_session_required"] is True
        assert policies[route_id]["legacy_token_allowed"] is False
        assert policies[route_id]["workspace_scope_required"] is True


def test_ui_manual_editor_is_safe_and_planner_consumes_governed_draft() -> None:
    editor = (ROOT / "ui/web/src/components/ArtifactManualEditor.ts").read_text(encoding="utf-8")
    planner = (ROOT / "ui/web/src/components/DocumentEditPlanner.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/WorkspaceDocumentsView.ts").read_text(encoding="utf-8")
    assert "AUTOSAVE_DELAY_MS = 1100" in editor and "Version history" in editor and "optimistic" in editor.lower()
    assert ".innerHTML =" not in editor and ".innerHTML=" not in editor and "textContent" in editor and "JSON inválido" in editor
    assert "setDraftContent" in planner and "sessionStorage no es autoridad para Markdown/JSON" in planner
    assert "createArtifactManualEditor" in view and "manualEditor, editPlanner" in view


def test_schema_openapi_and_ui_contracts_register_04_b() -> None:
    catalog = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    assert catalog["schemas_total"] == len(catalog["schemas"])
    assert any(x["schema_id"] == "SCHEMA-DEVPL-GSDLC-04-B-ARTIFACT-DRAFT-STORE-RECORD-V1" for x in catalog["schemas"])
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    ids = {x["route_id"] for x in api["routes"]}
    assert len({x for x in ids if x.startswith("api.workspace.artifact-drafts.")}) == 5
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    route = next(x for x in ui["routes"] if x["route_id"] == "ui.workspace-documents")
    assert {x for x in ids if x.startswith("api.workspace.artifact-drafts.")} <= set(route["allowed_api_routes"])
    openapi = json.loads((ROOT / "docs/07_interfaces/openapi_v1.json").read_text(encoding="utf-8"))
    assert "/api/v1/workspace/artifact-drafts/{document_id}/save" in openapi["paths"]
    assert openapi["x-devpilot-gsdlc-04-b"]["source_write_enabled"] is False


def test_windows_runtime_console_binds_only_disposable_fixture_before_browser() -> None:
    runtime_console = (ROOT / "scripts/devpl_gsdlc_04_b_runtime_console.py").read_text(encoding="utf-8")
    harness = (ROOT / "scripts/devpl_gsdlc_04_b_windows_harness.py").read_text(encoding="utf-8")
    probe = (ROOT / "scripts/devpl_gsdlc_04_b_fixture_binding_probe.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.0.9"' in runtime_console
    assert 'env["DEVPILOT_ALLOWED_WORKSPACE_ROOTS"] = str(fixture)' in runtime_console
    assert 'env["DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT"] = str(fixture)' in runtime_console
    assert 'env.pop("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", None)' in runtime_console
    assert '"scope": "gsdlc-04-b-browser-fixture-only"' in runtime_console
    assert "inventory-sales-local" in runtime_console
    assert '"fixture-binding-precheck"' in harness
    assert 'fixture_binding_ready' in harness
    assert 'ProjectEntryDryRunService' in probe
    assert 'UiWorkspaceContextResolver' in probe
    assert 'DEVPILOT_ALLOWED_WORKSPACE_ROOTS' in probe and 'DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT' in probe



def test_browser_fixture_ownership_is_external_and_git_clean_is_required() -> None:
    operator = (ROOT / "scripts/devpl_gsdlc_04_b_operator.py").read_text(encoding="utf-8")
    state = (ROOT / "scripts/devpl_gsdlc_04_b_fixture_state.py").read_text(encoding="utf-8")
    probe = (ROOT / "scripts/devpl_gsdlc_04_b_fixture_binding_probe.py").read_text(encoding="utf-8")
    assert "ownership_scope" in state and "external-evidence-only/no-marker-inside-fixture" in state
    assert "removed-v1.0.7-untracked-marker" in state
    assert "Only is reparable" not in state  # keep user-facing implementation Spanish, but no loose cleanup fallback
    assert "repair_legacy_marker" in operator
    assert "git_clean" in probe
    assert "Fixture Git debe estar limpio" in probe


def test_windows_harness_has_bounded_recovery_008_and_no_git_clean_reset() -> None:
    harness = (ROOT / "scripts/devpl_gsdlc_04_b_windows_harness.py").read_text(encoding="utf-8")
    assert 'HARNESS_VERSION = "1.0.10"' in harness
    assert '"browser-recovery-008"' in harness
    assert "repair_legacy_marker" in harness
    assert "prior_approval_reusable" in harness
    assert "git clean" not in harness.lower()
    assert "reset --hard" not in harness.lower()


def _load_windows_harness_module():
    import importlib.util
    path = ROOT / "scripts/devpl_gsdlc_04_b_windows_harness.py"
    spec = importlib.util.spec_from_file_location("devpl_gsdlc04b_harness_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_observation_workspace_is_version_isolated_and_never_overwrites_prior_guides(tmp_path: Path) -> None:
    harness = _load_windows_harness_module()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    legacy = evidence / "DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS.md"
    legacy.write_text("legacy manual evidence\n- `browser_acceptance`: `PASS`\n", encoding="utf-8")
    result = harness.prepare_observations(ROOT, evidence)
    current = evidence / "DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_v1_0_8.md"
    assert result["status"] == "PASS"
    assert current.is_file()
    assert legacy.read_text(encoding="utf-8").startswith("legacy manual evidence")
    before = current.read_bytes()
    current.write_text(current.read_text(encoding="utf-8") + "\nmanual note\n", encoding="utf-8")
    second = harness.prepare_observations(ROOT, evidence)
    assert second["template_action"] == "reused-current-version-preserved"
    assert current.read_bytes() != before
    assert current.read_text(encoding="utf-8").endswith("manual note\n")


def test_browser_evidence_validator_ignores_instructional_reference_and_requires_real_fields(tmp_path: Path) -> None:
    harness = _load_windows_harness_module()
    evidence = tmp_path / "evidence"
    browser = evidence / "browser"
    browser.mkdir(parents=True)
    harness.prepare_observations(ROOT, evidence)
    for name in [
        "00_project_entry_fixture_open.png", "01_editor_markdown_loaded.png", "02_autosave_saved.png",
        "03_restart_recovery.png", "04_version_history.png", "05_discard_recover.png", "06_json_hint.png",
        "07_conflict_banner.png", "08_project_guard.png",
    ]:
        (browser / name).write_bytes(b"png")
    with pytest.raises(harness.HarnessBlock):
        harness.browser_evidence_validate(evidence)
    obs = evidence / "DEVPL_GSDLC_04_B_MANUAL_BROWSER_OBSERVATIONS_v1_0_8.md"
    text = obs.read_text(encoding="utf-8")
    for case in [
        "Open Existing / PathGuard fixture", "Editor Markdown carga", "Autosave", "Recovery tras restart",
        "Version history", "Discard + recover", "JSON hints", "Conflict/stale preimage",
        "Project route guard", "Source no cambia al guardar draft", "Sesión/RBAC",
    ]:
        text = text.replace(f"| {case} | |", f"| {case} | PASS |")
    replacements = {
        "browser_acceptance": "PASS", "S0_open": "0", "S1_open": "0", "secrets_exposed": "false",
        "network_runtime_used": "false", "external_api_used": "false", "pilot_workspace_accessed": "false",
    }
    for key, value in replacements.items():
        text = text.replace(f"- `{key}`:", f"- `{key}`: `{value}`", 1)
    obs.write_text(text, encoding="utf-8")
    result = harness.browser_evidence_validate(evidence)
    assert result["status"] == "PASS"
    assert result["instructional_examples_parsed"] is False


def _load_fixture_state_module():
    import importlib.util
    path = ROOT / "scripts/devpl_gsdlc_04_b_fixture_state.py"
    spec = importlib.util.spec_from_file_location("devpl_gsdlc04b_fixture_state_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_exact_browser_fixture(tmp_path: Path) -> Path:
    import subprocess
    fixture = tmp_path / "fixture"
    (fixture / ".devpilot").mkdir(parents=True)
    (fixture / "docs").mkdir(parents=True)
    (fixture / ".devpilot/project.yaml").write_text(
        "project_id: gsdlc-04-b-browser-fixture\nproject_name: GSDLC 04 B Browser Fixture\nproject_type: software\n",
        encoding="utf-8",
        newline="\n",
    )
    (fixture / "docs/manual_authoring.json").write_text(
        '{"title":"Manual authoring fixture","version":1}\n', encoding="utf-8", newline="\n"
    )
    (fixture / "docs/manual_authoring.md").write_text(
        "# Manual authoring fixture\n\nApproved source v1.\n", encoding="utf-8", newline="\n"
    )
    subprocess.run(["git", "init"], cwd=fixture, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=fixture, check=True)
    subprocess.run(["git", "config", "user.name", "Fixture"], cwd=fixture, check=True)
    subprocess.run(["git", "add", ".devpilot/project.yaml", "docs/manual_authoring.json", "docs/manual_authoring.md"], cwd=fixture, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=fixture, check=True, capture_output=True)
    exclude = fixture / ".git/info/exclude"
    with exclude.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(".devpilot/\n")
    return fixture


def _write_valid_post_open_metadata(fixture: Path) -> None:
    execution = {
        "schema_id": "SCHEMA-DEVPL-GSDLC-03-D-BOOTSTRAP-EXECUTION-V1",
        "schema_version": "1.0",
        "status": "PASS",
        "project_id": "gsdlc04b-browser",
        "entry_mode": "OPEN_EXISTING",
        "target_root": str(fixture),
        "plan_hash": "1" * 64,
        "preimage_hash": "2" * 64,
        "approval_id": "APPROVAL-TEST009",
        "actor_id": "local-owner",
        "role_at_decision": "owner",
        "verification": {"ok": True, "failures": [], "git_clean": True, "writes_outside_workspace": 0, "network_used": False},
        "network_used": False,
        "external_api_used": False,
        "arbitrary_shell_used": False,
        "writes_outside_workspace": 0,
    }
    registration = {
        "schema_id": "devpilot.gsdlc03d.workspace_registration.v1",
        "workspace_id": "gsdlc04b-browser",
        "project_id": "gsdlc04b-browser",
        "root_path": str(fixture),
        "status": "registered-local",
        "default_effect": "deny",
        "network_allowed": False,
        "external_api_allowed": False,
        "registered_at": "2026-08-21T00:00:00Z",
        "registration_scope": "target-local",
    }
    (fixture / ".devpilot/bootstrap-execution.json").write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    (fixture / ".devpilot/workspace-registration.json").write_text(json.dumps(registration, indent=2) + "\n", encoding="utf-8")


def test_fixture_state_distinguishes_pre_open_and_valid_post_open_restart(tmp_path: Path) -> None:
    state_module = _load_fixture_state_module()
    fixture = _make_exact_browser_fixture(tmp_path)
    pre = state_module.inspect_fixture(fixture, enforce_exact_windows_path=False, phase_policy="pre-open")
    assert pre["fixture_phase"] == "PRE_OPEN" and pre["git_clean"] is True
    _write_valid_post_open_metadata(fixture)
    post = state_module.inspect_fixture(fixture, enforce_exact_windows_path=False, phase_policy="post-open-pass")
    assert post["fixture_phase"] == "POST_OPEN_PASS"
    assert post["post_open_metadata_present"] is True
    assert post["bootstrap_execution"]["status"] == "PASS"
    assert post["bootstrap_execution"]["entry_mode"] == "OPEN_EXISTING"
    assert post["workspace_registration"]["status"] == "registered-local"
    assert post["git_clean"] is True


def test_fixture_state_rejects_partial_or_invalid_post_open_metadata(tmp_path: Path) -> None:
    state_module = _load_fixture_state_module()
    fixture = _make_exact_browser_fixture(tmp_path)
    (fixture / ".devpilot/bootstrap-execution.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(state_module.FixtureStateError):
        state_module.inspect_fixture(fixture, enforce_exact_windows_path=False, phase_policy="either")
    (fixture / ".devpilot/bootstrap-execution.json").unlink()
    _write_valid_post_open_metadata(fixture)
    payload = json.loads((fixture / ".devpilot/bootstrap-execution.json").read_text(encoding="utf-8"))
    payload["status"] = "ROLLED-BACK"
    (fixture / ".devpilot/bootstrap-execution.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    with pytest.raises(state_module.FixtureStateError):
        state_module.inspect_fixture(fixture, enforce_exact_windows_path=False, phase_policy="post-open-pass")


def test_recovery_009_runtime_and_harness_are_restart_state_aware() -> None:
    runtime_console = (ROOT / "scripts/devpl_gsdlc_04_b_runtime_console.py").read_text(encoding="utf-8")
    harness = (ROOT / "scripts/devpl_gsdlc_04_b_windows_harness.py").read_text(encoding="utf-8")
    state = (ROOT / "scripts/devpl_gsdlc_04_b_fixture_state.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.0.9"' in runtime_console
    assert 'phase_policy="either"' in runtime_console
    assert '"fixture_phase": fixture_state["fixture_phase"]' in runtime_console
    assert 'HARNESS_VERSION = "1.0.10"' in harness
    assert '"browser-resume-009"' in harness
    assert 'phase_policy="post-open-pass"' in harness
    assert 'repeat_open_existing' in harness and 'repeat_b1_b2' in harness
    assert 'outputs" / "drafts" / "gsdlc_04_b' in harness
    assert 'POST_OPEN_PASS' in state and 'PRE_OPEN' in state
    assert 'no debe existir antes de Open Existing' not in runtime_console

def test_fixture_hash_after_accepts_windows_crlf_when_git_content_is_equivalent(tmp_path: Path) -> None:
    import subprocess
    harness = _load_windows_harness_module()
    fixture = _make_exact_browser_fixture(tmp_path)
    evidence = tmp_path / "evidence"
    evidence.mkdir()

    before = harness.fixture_hash(fixture, evidence, "before")
    assert before["status"] == "PASS"
    baseline = before["hashes"]["docs/manual_authoring.md"]

    subprocess.run(["git", "config", "core.autocrlf", "true"], cwd=fixture, check=True)
    md = fixture / "docs/manual_authoring.md"
    md.write_bytes(b"# Manual authoring fixture\r\n\r\nApproved source v1.\r\n")

    after = harness.fixture_hash(fixture, evidence, "after")
    assert after["status"] == "PASS"
    assert after["all_fixture_sources_restored"] is True
    assert after["hashes"]["docs/manual_authoring.md"] != baseline
    assert after["canonical_lf_hashes"]["docs/manual_authoring.md"] == baseline
    assert "docs/manual_authoring.md" in after["eol_only_representation_paths"]
    assert after["source_state"]["docs/manual_authoring.md"]["git_content_equivalent_to_head"] is True

    md.write_bytes(b"# Manual authoring fixture\r\n\r\nApproved source CHANGED.\r\n")
    with pytest.raises(harness.HarnessBlock):
        harness.fixture_hash(fixture, evidence, "after")
