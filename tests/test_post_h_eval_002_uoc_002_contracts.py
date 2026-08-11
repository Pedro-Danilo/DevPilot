from __future__ import annotations

import json
from pathlib import Path

from devpilot_core.schemas import SchemaValidator

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_uoc_002_state_backlog_manifest_and_flags_are_synchronized() -> None:
    backlog = _read("docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md")
    state = _json(".devpilot/project_state.json")
    manifest = _json("docs/post_h_eval_002_uoc_002_manifest.json")
    flags = _json(".devpilot/interfaces/ui_operational_console_flags.json")
    assert state["uoc_001_closed"] is True
    assert state["uoc_002_authorized"] is True
    assert state["uoc_002_candidate_repo"] == "repo_DevPilot_Local_330_CANDIDATE_POST_H_EVAL_002_UOC_002.zip"
    if state["uoc_002_closed"]:
        assert "UOC-002-closed/PASS" in backlog
        assert state["uoc_002_authoritative_baseline"] == "repo_DevPilot_Local_330_POST_H_EVAL_002_UOC_002.zip"
        current_repo = str(state["current_repo"])
        assert current_repo.startswith("repo_DevPilot_Local_")
        assert int(current_repo.split("_", 4)[3]) >= 330
        assert state["uoc_002_status"] == "closed/PASS"
        assert state["uoc_003_authorized"] is True
        assert manifest["status"] == "closed"
        assert manifest["decision"] == "PASS"
        assert manifest["closed"] is True
    else:
        assert "UOC-002-regression-recovery/pending-windows-selective-verification" in backlog
        assert state["current_repo"] == "repo_DevPilot_Local_329_POST_H_EVAL_002_UOC_001.zip"
        assert state["uoc_002_status"] == "implemented-initial/pending-windows-acceptance"
        assert state["uoc_003_authorized"] is False
        assert manifest["status"] == "implemented-initial"
        assert manifest["decision"] == "PENDING-WINDOWS-ACCEPTANCE"
        assert manifest["closed"] is False
    flag = next(x for x in flags["feature_flags"] if x["flag_id"] == "uoc.documents.metadata_git_search")
    assert flag["enabled"] is True
    assert all(x["state"] == "engaged" for x in flags["kill_switches"])


def test_uoc_002_api_and_ui_route_contracts_are_read_only_and_complete() -> None:
    api = _json(".devpilot/interfaces/api_route_contract_registry.json")
    ui = _json(".devpilot/interfaces/ui_route_contract_registry.json")
    route_ids = {
        "api.workspace.documents.history",
        "api.workspace.documents.diff",
        "api.workspace.documents.search",
        "api.workspace.documents.links",
    }
    routes = {x["route_id"]: x for x in api["routes"]}
    assert route_ids <= routes.keys()
    for route_id in route_ids:
        route = routes[route_id]
        assert route["method"] == "GET"
        assert route["auth_required"] is True
        assert route["policy_check_required"] is True
        assert route["mutations_allowed"] is False
        assert route["external_api_allowed"] is False
        assert route["remote_execution_allowed"] is False
        assert route["connector_write_allowed"] is False
        assert route["plugin_execution_allowed"] is False
    ui_route = next(x for x in ui["routes"] if x["route_id"] == "ui.workspace-documents")
    assert route_ids <= set(ui_route["allowed_api_routes"])
    assert "ui/web/src/components/DocumentInspectionPanel.ts" in ui_route["source_files"]
    state = _json(".devpilot/project_state.json")
    if state.get("uoc_005_status"):
        assert ui_route["shows_mutation_controls"] is True
        assert ui_route["mutation_controls"]["approval_required"] is True
        assert ui_route["mutation_controls"]["destructive_action_allowed"] is False
    else:
        assert ui_route["shows_mutation_controls"] is False


def test_uoc_002_schemas_are_registered_and_validate_minimal_payloads() -> None:
    catalog = _json("docs/schemas/schema_catalog.json")
    expected = {
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-HISTORY-V1",
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-DIFF-V1",
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-SEARCH-V1",
        "SCHEMA-DEVPL-WORKSPACE-DOCUMENT-LINKS-V1",
    }
    assert expected <= {x["schema_id"] for x in catalog["schemas"]}
    assert catalog["schemas_total"] == len(catalog["schemas"])
    doc = {"document_id": "doc_abcdefghijklmnopqrstuvwx", "relative_path": "docs/x.md", "name": "x.md"}
    payloads = {
        "WorkspaceDocumentHistory": {"summary": {"is_git_repo": True, "relative_path": "docs/x.md", "commits_total": 0, "limit": 20, "offset": 0, "next_offset": None, "read_only": True, "mutations_performed": False}, "document": doc, "commits": [], "safety": {"read_only": True, "mutations_performed": False, "git_commands_typed": True}},
        "WorkspaceDocumentDiff": {"summary": {"relative_path": "docs/x.md", "base_ref": "HEAD", "max_bytes": 1024, "truncated": False, "read_only": True, "mutations_performed": False}, "document": doc, "git_status": {}, "diff": "", "safety": {"read_only": True, "mutations_performed": False, "git_commands_typed": True}},
        "WorkspaceDocumentSearch": {"summary": {"workspace_id": "w", "query": "vision", "matching_total": 0, "indexed_documents": 1, "cache_scope": "in-memory-active-workspace", "read_only": True, "mutations_performed": False, "external_persistence": False}, "results": [], "safety": {"read_only": True, "mutations_performed": False, "search_index_external_persistence": False, "cross_workspace_results_allowed": False}},
        "WorkspaceDocumentLinks": {"summary": {"workspace_id": "w", "document_id": doc["document_id"], "outgoing_total": 0, "incoming_total": 0, "read_only": True, "mutations_performed": False}, "document": doc, "outgoing": [], "incoming": [], "safety": {"read_only": True, "mutations_performed": False, "absolute_paths_accepted_from_browser": False}},
    }
    validator = SchemaValidator(ROOT)
    for contract, payload in payloads.items():
        result = validator.validate_payload(schema=contract, payload=payload, instance_label=f"uoc-002-{contract}")
        assert result.ok, result.to_dict()


def test_uoc_002_tcr_source_registry_and_openapi_are_synchronized() -> None:
    source = _json(".devpilot/docs_governance/source_registry.json")
    tcr1 = _json(".devpilot/testing/test_contract_registry.json")
    tcr2 = _json(".devpilot/testing/test_contract_registry_v2.json")
    openapi = _json("docs/07_interfaces/openapi_v1.json")
    docs = {x["doc_id"] for x in source["documents"]}
    assert "DEVPL-UOC-002-DOCUMENT-INSPECTION-REPORT" in docs
    assert "UOC-002-MANIFEST" in docs
    assert any(x["contract_id"] == "post-h-eval-002-uoc-002-document-inspection" for x in tcr1["contracts"])
    assert any(x["contract_id"] == "post-h-eval-002-uoc-002-document-inspection" for x in tcr2["contracts"])
    for path in [
        "/api/v1/workspace/documents/search",
        "/api/v1/workspace/documents/{document_id}/history",
        "/api/v1/workspace/documents/{document_id}/diff",
        "/api/v1/workspace/documents/{document_id}/links",
    ]:
        assert path in openapi["paths"]


def test_uoc_002_runtime_surface_has_no_write_shell_or_external_persistence() -> None:
    sources = "\n".join(_read(path) for path in [
        "src/devpilot_core/application/workspace_document_inspection_service.py",
        "src/devpilot_core/repo/git_adapter.py",
        "src/devpilot_core/interfaces/api/routers/workspace_documents.py",
        "ui/web/src/components/DocumentInspectionPanel.ts",
        "ui/web/src/pages/WorkspaceDocumentsView.ts",
    ])
    for marker in ["shell=True", "innerHTML", "write_text(", "write_bytes(", "unlink(", "rmtree(", "localStorage.setItem"]:
        assert marker not in sources
    assert "subprocess.run" in sources
    assert "shell=False" in sources
    assert "memory-only" in sources
