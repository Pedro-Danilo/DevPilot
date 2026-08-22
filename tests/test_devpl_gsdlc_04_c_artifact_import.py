from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from devpilot_core.application import AuthApplicationService
from devpilot_core.application.artifact_import_service import ArtifactImportApplicationService, MAX_IMPORT_BYTES
from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.identity.auth_models import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from devpilot_core.identity.auth_store import LocalAuthStore
from devpilot_core.interfaces.api.app import create_app
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, resolve_route_policy

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"
ORIGIN = {"Origin": "http://127.0.0.1:5173"}


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / f"gsdlc04c-{tmp_path.name}"
    docs = root / "docs"
    docs.mkdir(parents=True)
    (docs / "existing.md").write_text("# Existing\n\nApproved source.\n", encoding="utf-8", newline="\n")
    (docs / "existing.json").write_text('{"version":1}\n', encoding="utf-8", newline="\n")
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(root))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(root))
    monkeypatch.delenv("DEVPILOT_UI_WORKSPACE_REGISTRY_PATH", raising=False)
    yield root
    token = hashlib.sha256(root.name.encode("utf-8")).hexdigest()[:20]
    shutil.rmtree(ROOT / "outputs" / "imports" / "gsdlc_04_c" / token, ignore_errors=True)


def _service() -> ArtifactImportApplicationService:
    documents = WorkspaceDocumentsApplicationService(ROOT)
    return ArtifactImportApplicationService(ROOT, documents=documents)


def _identity() -> dict[str, str]:
    return {"actor": "owner.local", "actor_role": "owner", "session_principal": "owner.local"}


def _preview(service: ArtifactImportApplicationService, **kwargs):
    return service.preview(**_identity(), **kwargs)


def _persist(service: ArtifactImportApplicationService, preview, **kwargs):
    return service.persist(**_identity(), expected_preview_sha256=preview.data["preview"]["preview_sha256"], **kwargs)


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def test_paste_preview_is_read_only_deterministic_and_has_diff(workspace: Path) -> None:
    service = _service()
    before = (workspace / "docs/existing.md").read_bytes()
    kwargs = dict(source_type="PASTE", destination_path="docs/existing.md", source_label="copied-note", source_reference="ticket:ABC-123", text_content="# Existing\n\nImported draft.\n")
    first = _preview(service, **kwargs); second = _preview(service, **kwargs)
    assert first.ok and second.ok
    p = first.data["preview"]
    assert p["preview_sha256"] == second.data["preview"]["preview_sha256"]
    assert p["original_sha256"] == p["normalized_sha256"]
    assert "-Approved source." in p["diff"] and "+Imported draft." in p["diff"]
    assert (workspace / "docs/existing.md").read_bytes() == before
    assert first.data["summary"]["network_used"] is False
    assert first.data["summary"]["url_fetch_performed"] is False


def test_paste_persist_is_draft_provenance_only_and_source_unchanged(workspace: Path) -> None:
    service = _service(); before = (workspace / "docs/existing.md").read_bytes()
    kwargs = dict(source_type="PASTE", destination_path="docs/new_from_paste.md", source_label="meeting notes", source_reference="manual-reference", text_content="# Pasted\n\nHello.\n")
    preview = _preview(service, **kwargs); assert preview.ok
    result = _persist(service, preview, **kwargs); assert result.ok, result.to_dict()
    record = result.data["import"]
    assert record["lifecycle_state"] == "DRAFT" and record["source_type"] == "PASTE"
    assert record["artifact"]["state"] == "DRAFT"
    assert record["artifact"]["provenance"]["source_type"] == "PASTE"
    assert record["artifact"]["provenance"]["author_actor"] == "owner.local"
    assert record["workspace_writes_performed"] is False and record["source_mutations_performed"] is False
    assert not (workspace / "docs/new_from_paste.md").exists()
    assert (workspace / "docs/existing.md").read_bytes() == before


def test_upload_normalizes_utf16_and_preserves_original_and_normalized_hashes(workspace: Path) -> None:
    service = _service()
    text = '{"name":"café","line":"one\\ntwo"}\r\n'
    raw = b"\xff\xfe" + text.encode("utf-16-le")
    kwargs = dict(source_type="UPLOAD", destination_path="docs/uploaded.json", original_filename="uploaded.json", declared_mime="application/json", content_base64=_b64(raw))
    preview = _preview(service, **kwargs); assert preview.ok, preview.to_dict()
    p = preview.data["preview"]
    assert p["encoding"] == "utf-16-le-bom"
    assert p["original_sha256"] == hashlib.sha256(raw).hexdigest()
    assert p["normalized_sha256"] == hashlib.sha256(p["normalized_content"].encode("utf-8")).hexdigest()
    assert p["original_sha256"] != p["normalized_sha256"]
    assert p["declared_mime"] == "application/json"
    persisted = _persist(service, preview, **kwargs); assert persisted.ok, persisted.to_dict()
    assert persisted.data["import"]["original_sha256"] == p["original_sha256"]
    assert persisted.data["import"]["normalized_sha256"] == p["normalized_sha256"]


@pytest.mark.parametrize("destination", [
    "../escape.md",
    "/absolute.md",
    "C:/escape.md",
    "//server/share/file.md",
    "docs/file.md:evil",
    "CON.md",
    "docs/NUL.json",
])
def test_destination_traversal_unc_ads_device_and_absolute_paths_block(workspace: Path, destination: str) -> None:
    result = _preview(_service(), source_type="PASTE", destination_path=destination, text_content="safe")
    assert result.ok is False and result.exit_code.value == 2


def test_symlink_parent_and_symlink_destination_block(workspace: Path) -> None:
    service = _service()
    outside = workspace.parent / "outside"; outside.mkdir()
    try:
        os.symlink(outside, workspace / "linked")
        parent = _preview(service, source_type="PASTE", destination_path="linked/escape.md", text_content="safe")
        assert parent.ok is False and any(f.id == "GSDLC04C_SYMLINK_BLOCK" for f in parent.findings)
        os.symlink(workspace / "docs/existing.md", workspace / "docs/link.md")
        target = _preview(service, source_type="PASTE", destination_path="docs/link.md", text_content="safe")
        assert target.ok is False and any(f.id == "GSDLC04C_SYMLINK_BLOCK" for f in target.findings)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation unavailable on this platform")


def test_oversize_unsupported_extension_mime_mismatch_and_binary_block(workspace: Path) -> None:
    service = _service()
    oversized = _preview(service, source_type="PASTE", destination_path="docs/large.md", text_content="x" * (MAX_IMPORT_BYTES + 1))
    assert oversized.ok is False and any(f.id == "GSDLC04C_OVERSIZE_BLOCK" for f in oversized.findings)
    unsupported = _preview(service, source_type="UPLOAD", destination_path="docs/a.exe", original_filename="a.exe", declared_mime="application/octet-stream", content_base64=_b64(b"MZ"))
    assert unsupported.ok is False
    mismatch = _preview(service, source_type="UPLOAD", destination_path="docs/a.json", original_filename="a.json", declared_mime="image/png", content_base64=_b64(b'{"ok":true}\n'))
    assert mismatch.ok is False and any(f.id == "GSDLC04C_MIME_MISMATCH_BLOCK" for f in mismatch.findings)
    binary = _preview(service, source_type="UPLOAD", destination_path="docs/a.md", original_filename="a.md", declared_mime="text/markdown", content_base64=_b64(b"abc\x00def"))
    assert binary.ok is False and any(f.id == "GSDLC04C_BINARY_BLOCK" for f in binary.findings)


def test_malformed_encoding_and_invalid_json_block(workspace: Path) -> None:
    service = _service()
    encoding = _preview(service, source_type="IMPORT", destination_path="docs/a.md", original_filename="a.md", declared_mime="text/markdown", content_base64=_b64(b"\xff\x00\x81"))
    assert encoding.ok is False and any(f.id in {"GSDLC04C_ENCODING_BLOCK", "GSDLC04C_BINARY_BLOCK"} for f in encoding.findings)
    invalid_json = _preview(service, source_type="PASTE", destination_path="docs/a.json", text_content='{"broken":')
    assert invalid_json.ok is False and any(f.id == "GSDLC04C_JSON_SYNTAX_BLOCK" for f in invalid_json.findings)


def test_secret_preview_is_redacted_and_persist_fails_closed(workspace: Path) -> None:
    service = _service(); secret_value = "sk-proj-abcdefghijklmnop"
    kwargs = dict(source_type="PASTE", destination_path="docs/secret.md", text_content=f"api_key={secret_value}\n")
    preview = _preview(service, **kwargs); assert preview.ok
    payload = preview.to_dict()
    assert preview.data["preview"]["secret_warning"] is True
    assert secret_value not in json.dumps(payload)
    assert "REDACTED" in preview.data["preview"]["normalized_content"]
    blocked = _persist(service, preview, **kwargs)
    assert blocked.ok is False and any(f.id == "GSDLC04C_SECRET_IMPORT_BLOCK" for f in blocked.findings)
    assert not (workspace / "docs/secret.md").exists()


def test_stale_preview_hash_blocks_and_reference_never_fetches(workspace: Path) -> None:
    service = _service()
    original = dict(source_type="PASTE", destination_path="docs/ref.md", source_reference="https://example.invalid/source", text_content="alpha")
    preview = _preview(service, **original); assert preview.ok
    changed = dict(original); changed["text_content"] = "beta"
    result = service.persist(**_identity(), expected_preview_sha256=preview.data["preview"]["preview_sha256"], **changed)
    assert result.ok is False and any(f.id == "GSDLC04C_PREVIEW_STALE_BLOCK" for f in result.findings)
    assert preview.data["summary"]["url_fetch_performed"] is False
    assert preview.data["summary"]["network_used"] is False


def test_runtime_record_survives_service_restart_and_recent_is_schema_backed(workspace: Path) -> None:
    kwargs = dict(source_type="IMPORT", destination_path="docs/restart.md", original_filename="restart.md", declared_mime="text/markdown", source_label="disk import", content_base64=_b64(b"# Restart\n"))
    service = _service(); preview = _preview(service, **kwargs); persisted = _persist(service, preview, **kwargs)
    assert persisted.ok
    restarted = _service(); recent = restarted.recent(limit=10)
    assert recent.ok and recent.data["imports"]
    item = recent.data["imports"][0]
    assert item["source_type"] == "IMPORT" and item["lifecycle_state"] == "DRAFT"


def _human_client(tmp_path: Path) -> TestClient:
    store = LocalAuthStore(tmp_path / "auth")
    auth = AuthApplicationService(tmp_path / "auth", store=store)
    client = TestClient(create_app(ROOT, api_token="legacy-gsdlc04c", auth_service=auth))
    boot = client.post("/api/v1/auth/bootstrap/owner", json={"username":"owner.local","display_name":"Local Owner","password":PASSWORD}, headers=ORIGIN)
    assert boot.status_code == 201, boot.text
    return client


def _csrf_headers(client: TestClient) -> dict[str, str]:
    return {"Origin": ORIGIN["Origin"], CSRF_HEADER_NAME: str(client.cookies.get(CSRF_COOKIE_NAME))}


def test_api_import_routes_require_human_session_and_bind_server_actor(workspace: Path, tmp_path: Path) -> None:
    legacy = TestClient(create_app(ROOT, api_token="legacy-gsdlc04c"))
    blocked = legacy.post("/api/v1/workspace/artifact-imports/preview", headers={"X-DevPilot-Token":"legacy-gsdlc04c"}, json={"source_type":"PASTE","destination_path":"docs/api.md","text_content":"hello"})
    assert blocked.status_code in {401, 403}
    client = _human_client(tmp_path)
    response = client.post("/api/v1/workspace/artifact-imports/preview", headers=_csrf_headers(client), json={"source_type":"PASTE","destination_path":"docs/api.md","text_content":"hello","source_label":"browser"})
    assert response.status_code == 200, response.text
    preview = response.json()["data"]["preview"]
    persist = client.post("/api/v1/workspace/artifact-imports/persist", headers=_csrf_headers(client), json={"source_type":"PASTE","destination_path":"docs/api.md","text_content":"hello","source_label":"browser","expected_preview_sha256":preview["preview_sha256"]})
    assert persist.status_code == 200, persist.text
    provenance = persist.json()["data"]["import"]["artifact"]["provenance"]
    assert provenance["author_actor"] != "browser-supplied-actor"
    assert provenance["session_principal"] == provenance["author_actor"]


def test_route_security_and_rbac_contracts_are_explicit() -> None:
    expected = {
        ("POST", "/api/v1/workspace/artifact-imports/preview"): "workspace.artifact_imports.preview",
        ("POST", "/api/v1/workspace/artifact-imports/persist"): "workspace.artifact_imports.persist",
        ("GET", "/api/v1/workspace/artifact-imports/recent"): "workspace.artifact_imports.recent",
    }
    for (method, path), operation in expected.items():
        policy = resolve_route_policy(method, path)
        assert policy is not None and policy.operation == operation
    assert len([p for p in API_ROUTE_POLICIES.values() if "artifact_imports" in p.operation]) == 3
    catalog = json.loads((ROOT / ".devpilot/identity/server_rbac_policy_catalog.json").read_text(encoding="utf-8"))
    policies = {x["route_id"]: x for x in catalog["route_policies"]}
    for route_id in ["api.workspace.artifact-imports.preview", "api.workspace.artifact-imports.persist", "api.workspace.artifact-imports.recent"]:
        assert policies[route_id]["human_session_required"] is True
        assert policies[route_id]["legacy_token_allowed"] is False
        assert policies[route_id]["workspace_scope_required"] is True


def test_ui_import_workbench_is_safe_preview_first_and_provenance_visible() -> None:
    component = (ROOT / "ui/web/src/components/ArtifactImportWorkbench.ts").read_text(encoding="utf-8")
    view = (ROOT / "ui/web/src/pages/WorkspaceDocumentsView.ts").read_text(encoding="utf-8")
    assert "PASTE" in component and "UPLOAD" in component and "IMPORT" in component
    assert "Generar preview" in component and "Crear DRAFT" in component
    assert "SHA original" in component and "SHA normalizado" in component and "Artifact provenance" in component
    assert "URL/reference es metadata" in component and "nunca hace fetch" in component
    assert ".innerHTML =" not in component and ".innerHTML=" not in component and "textContent" in component
    assert "MAX_IMPORT_BYTES = 1_048_576" in component and "input.accept='.md,.json" in component
    assert "createArtifactImportWorkbench" in view


def test_schema_openapi_and_ui_contracts_register_04_c() -> None:
    schemas = json.loads((ROOT / "docs/schemas/schema_catalog.json").read_text(encoding="utf-8"))
    assert schemas["schemas_total"] == len(schemas["schemas"])
    assert any(x["schema_id"] == "SCHEMA-DEVPL-GSDLC-04-C-ARTIFACT-IMPORT-RECORD-V1" for x in schemas["schemas"])
    api = json.loads((ROOT / ".devpilot/interfaces/api_route_contract_registry.json").read_text(encoding="utf-8"))
    ids = {x["route_id"] for x in api["routes"]}
    expected = {"api.workspace.artifact-imports.preview", "api.workspace.artifact-imports.persist", "api.workspace.artifact-imports.recent"}
    assert expected <= ids
    ui = json.loads((ROOT / ".devpilot/interfaces/ui_route_contract_registry.json").read_text(encoding="utf-8"))
    route = next(x for x in ui["routes"] if x["route_id"] == "ui.workspace-documents")
    assert expected <= set(route["allowed_api_routes"])
    openapi = json.loads((ROOT / "docs/07_interfaces/openapi_v1.json").read_text(encoding="utf-8"))
    for path in ["/api/v1/workspace/artifact-imports/preview", "/api/v1/workspace/artifact-imports/persist", "/api/v1/workspace/artifact-imports/recent"]:
        assert path in openapi["paths"]
    assert openapi["x-devpilot-gsdlc-04-c"]["source_write_enabled"] is False
    assert openapi["x-devpilot-gsdlc-04-c"]["url_fetch_enabled"] is False


def test_windows_operator_preimage_authority_accepts_only_eol_equivalent_clean_content() -> None:
    import importlib.util

    path = ROOT / "scripts/devpl_gsdlc_04_c_operator.py"
    spec = importlib.util.spec_from_file_location("devpl_gsdlc_04_c_operator_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    archive_crlf = b'{\r\n  "status": "closed/PASS"\r\n}\r\n'
    checkout_lf = module.canonical_lf_bytes(archive_crlf)
    pre_raw = hashlib.sha256(archive_crlf).hexdigest()
    pre_canonical = hashlib.sha256(checkout_lf).hexdigest()

    equivalent, used_eol = module.preimage_equivalent_with_git_authority(
        target_bytes=checkout_lf,
        git_blob=checkout_lf,
        expected_raw_sha256=pre_raw,
        expected_canonical_lf_sha256=pre_canonical,
        path_clean=True,
    )
    assert equivalent is True and used_eol is True

    changed = checkout_lf.replace(b"closed/PASS", b"different")
    equivalent, used_eol = module.preimage_equivalent_with_git_authority(
        target_bytes=changed,
        git_blob=checkout_lf,
        expected_raw_sha256=pre_raw,
        expected_canonical_lf_sha256=pre_canonical,
        path_clean=False,
    )
    assert equivalent is False and used_eol is False
