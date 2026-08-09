from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_uoc_001_backlog_manifest_state_and_flags_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md")
    manifest = _json("docs/post_h_eval_002_uoc_001_manifest.json")
    state = _json(".devpilot/project_state.json")
    flags = _json(".devpilot/interfaces/ui_operational_console_flags.json")

    assert 'UOC-001-closed/PASS' in backlog
    assert 'canonical_baseline_commit: "resolved-by-UOC_001_CANONICAL_INTEGRATION.json"' in backlog
    assert manifest["sprint_id"] == "UOC-001"
    assert manifest["base_commit"] == "a986f83a7c2da99a734c88feb80bf5d66cde2e4a"
    assert manifest["gates"]["read_only"] is True
    assert manifest["gates"]["mutations_enabled"] is False
    assert manifest["status"] == "closed"
    assert manifest["decision"] == "PASS"
    assert manifest["gates"]["browser_acceptance_pending"] is False
    assert manifest["gates"]["browser_acceptance_pass"] is True
    assert manifest["gates"]["windows_path_security_pass"] is True
    assert manifest["gates"]["ui_eligible_documents_visibility_pass"] is True
    assert manifest["gates"]["policy_excluded_documents_hidden_pass"] is True
    assert manifest["browser_acceptance_contract"]["version"] == "3.0"
    assert manifest["browser_acceptance_contract"]["policy_aligned"] is True
    assert manifest["browser_acceptance_contract"]["sequence_aware"] is True
    assert state["uoc_001_status"] == "closed/PASS"
    assert state["uoc_001_ui_eligible_document_visibility_pass"] is True
    assert state["uoc_001_policy_excluded_documents_hidden_pass"] is True
    assert state["uoc_001_write_enabled"] is False
    assert state["uoc_002_authorized"] is True
    read_flag = next(item for item in flags["feature_flags"] if item["flag_id"] == "uoc.documents.read_only")
    assert read_flag["enabled"] is True
    metadata_flag = next(item for item in flags["feature_flags"] if item["flag_id"] == "uoc.documents.metadata_git_search")
    assert metadata_flag["enabled"] is True
    allowed_enabled = {"uoc.documents.read_only", "uoc.documents.metadata_git_search"}
    if state.get("uoc_003_status"):
        allowed_enabled.add("uoc.documents.validation_traceability")
    if state.get("uoc_004_status"):
        allowed_enabled.add("uoc.documents.edit_plan")
    assert all(
        item["enabled"] is False
        for item in flags["feature_flags"]
        if item["flag_id"] not in allowed_enabled
    )
    assert all(item["state"] == "engaged" for item in flags["kill_switches"])


def test_uoc_001_route_registries_are_exact_and_read_only() -> None:
    ui = _json(".devpilot/interfaces/ui_route_contract_registry.json")
    api = _json(".devpilot/interfaces/api_route_contract_registry.json")
    capability = _json(".devpilot/interfaces/ui_capability_registry.json")

    ui_route = next(item for item in ui["routes"] if item["route_id"] == "ui.workspace-documents")
    assert ui_route["path"] == "/workspace/documents"
    assert ui_route["shows_mutation_controls"] is False
    assert {
        "api.workspace.documents.list",
        "api.workspace.documents.read",
        "api.workspace.documents.metadata",
        "api.portfolio.status",
    } <= set(ui_route["allowed_api_routes"])
    api_routes = {item["route_id"]: item for item in api["routes"]}
    for route_id in [
        "api.workspace.documents.list",
        "api.workspace.documents.read",
        "api.workspace.documents.metadata",
    ]:
        route = api_routes[route_id]
        assert route["method"] == "GET"
        assert route["auth_required"] is True
        assert route["policy_check_required"] is True
        assert route["mutations_allowed"] is False
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False
        assert route["external_api_allowed"] is False
    assert api["summary"]["routes_total"] >= 42
    assert ui["summary"]["routes_total"] == 6
    assert capability["summary"]["api_routes_total"] >= 42
    assert capability["summary"]["ui_routes_total"] == 6
    assert capability["safety"]["document_write_enabled"] is False


def test_uoc_001_schemas_are_registered_and_accept_minimal_contracts() -> None:
    catalog = _json("docs/schemas/schema_catalog.json")
    ids = {entry["schema_id"] for entry in catalog["schemas"]}
    expected = {
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-INDEX-V1",
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-RESOURCE-V1",
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-METADATA-V1",
    }
    assert expected <= ids
    assert catalog["schemas_total"] == len(catalog["schemas"])

    safety = {
        "read_only": True,
        "mutations_performed": False,
        "absolute_paths_accepted_from_browser": False,
        "symlink_following": False,
        "external_api_used": False,
    }
    document_id = "doc_abcdefghijklmnopqrstuvwx"
    node = {
        "node_id": document_id,
        "document_id": document_id,
        "kind": "document",
        "name": "product_vision.md",
        "relative_path": "product_vision.md",
        "parent_id": None,
        "extension": ".md",
        "category": "product",
        "size_bytes": 9,
        "modified_at": "2026-08-04T00:00:00Z",
        "readable": True,
        "blocked_reason": None,
    }
    index = {
        "summary": {
            "workspace_id": "inventory-sales-local",
            "workspace_mode": "explicit-active-root",
            "nodes_total": 1,
            "matching_total": 1,
            "returned_total": 1,
            "documents_total": 1,
            "folders_total": 0,
            "offset": 0,
            "limit": 50,
            "next_offset": None,
            "allowed_extensions": [".md", ".json", ".yaml", ".yml", ".txt"],
            "maximum_inline_bytes": 1048576,
            "read_only": True,
            "mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        },
        "nodes": [node],
        "ui_workspace_context": {"configured": True},
        "safety": safety,
    }
    resource = {
        "summary": {
            "workspace_id": "inventory-sales-local",
            "document_id": document_id,
            "content_type": "text/markdown",
            "parse_status": "not-applicable",
            "read_only": True,
            "mutations_performed": False,
        },
        "document": {
            **node,
            "sha256": "a" * 64,
            "encoding": "utf-8",
            "content": "# Vision",
            "structured": None,
            "breadcrumbs": [
                {"label": "inventory-sales-local", "relative_path": None},
                {"label": "product_vision.md", "relative_path": "product_vision.md"},
            ],
        },
        "ui_workspace_context": {"configured": True},
        "safety": safety,
    }
    metadata = {
        "summary": {
            "workspace_id": "inventory-sales-local",
            "document_id": document_id,
            "read_only": True,
            "mutations_performed": False,
        },
        "document": {**node, "sha256": "a" * 64},
        "ui_workspace_context": {"configured": True},
        "safety": safety,
    }
    for contract, payload in [
        ("WorkspaceDocumentIndex", index),
        ("WorkspaceDocumentResource", resource),
        ("WorkspaceDocumentMetadata", metadata),
    ]:
        result = SchemaValidator(ROOT).validate_payload(schema=contract, payload=payload, instance_label=f"uoc-001-{contract}")
        assert result.ok is True, result.to_dict()


def test_uoc_001_documentation_and_tcr_are_registered() -> None:
    source = _json(".devpilot/docs_governance/source_registry.json")
    tcr1 = _json(".devpilot/testing/test_contract_registry.json")
    tcr2 = _json(".devpilot/testing/test_contract_registry_v2.json")
    docs = {item["doc_id"]: item for item in source["documents"]}
    assert "DEVPL-UOC-001-READ-ONLY-DOCUMENTS-REPORT" in docs
    assert "DEVPL-UOC-001-WORKSPACE-DOCUMENTS-API" in docs
    assert "UOC-001-MANIFEST" in docs
    assert any(item["contract_id"] == "post-h-eval-002-uoc-001-workspace-documents" for item in tcr1["contracts"])
    assert any(item["contract_id"] == "post-h-eval-002-uoc-001-workspace-documents" for item in tcr2["contracts"])


def test_uoc_001_no_write_or_shell_markers_in_new_runtime_surface() -> None:
    sources = "\n".join(
        _read(path)
        for path in [
            "src/devpilot_core/application/workspace_documents_service.py",
            "src/devpilot_core/interfaces/api/routers/workspace_documents.py",
            "ui/web/src/pages/WorkspaceDocumentsView.ts",
            "ui/web/src/components/DocumentTree.ts",
            "ui/web/src/components/DocumentViewer.ts",
        ]
    )
    for marker in ["subprocess", "shell=True", "write_text(", "write_bytes(", "unlink(", "rmtree(", "innerHTML"]:
        assert marker not in sources
    assert "O_NOFOLLOW" in sources
    assert "mutations_performed" in sources
