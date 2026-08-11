from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_uoc008_project_state_preserves_candidate_or_closed_lifecycle_without_rewinding_pilot() -> None:
    state = load_json(".devpilot/project_state.json")
    assert state["uoc_008_authorized"] is True
    assert state["uoc_008_job_console_available"] is True
    assert state["uoc_008_runtime_capability_execution_enabled_total"] == 0
    assert state["current_micro_sprint"] == "POST-H-EVAL-002-02-B"
    assert state["next_micro_sprint"] == "POST-H-EVAL-002-02-C"
    status = state["uoc_008_status"]
    assert status in {"implemented-initial/pending-windows-browser-closure", "closed/PASS"}
    if status == "implemented-initial/pending-windows-browser-closure":
        assert state["current_repo"] == "repo_DevPilot_Local_335_POST_H_EVAL_002_UOC_007.zip"
        assert state["uoc_009_authorized"] is False
    else:
        assert state["uoc_008_authoritative_baseline"] == "repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip"
        current_number = int(state["current_repo"].split("repo_DevPilot_Local_", 1)[1].split("_", 1)[0])
        assert current_number >= 336
        assert state["uoc_009_authorized"] is True


def test_uoc008_ui_and_api_routes_are_registered_without_relaxing_no_go_gates() -> None:
    ui = load_json(".devpilot/interfaces/ui_route_contract_registry.json")
    api = load_json(".devpilot/interfaces/api_route_contract_registry.json")
    route = next(item for item in ui["routes"] if item["route_id"] == "ui.jobs")
    assert route["path"] == "/jobs"
    assert route["local_only"] is True
    for key in ("remote_execution_allowed", "connector_write_allowed", "plugin_execution_allowed", "external_api_allowed"):
        assert route[key] is False
    expected = {"api.jobs.list", "api.jobs.inspect", "api.jobs.logs", "api.jobs.cancel", "api.jobs.retry"}
    assert set(route["allowed_api_routes"]) == expected
    registered = {item["route_id"] for item in api["routes"]}
    assert expected <= registered


def test_uoc008_runtime_is_observability_and_lifecycle_not_generic_cli_execution() -> None:
    capability = load_json(".devpilot/interfaces/governed_job_capability_registry.json")
    ui_capability = load_json(".devpilot/interfaces/ui_capability_registry.json")
    assert capability["summary"]["capabilities_total"] == 193
    historical = load_json("docs/post_h_eval_002_uoc_008_manifest.json")
    assert historical["capability_execution_enabled_total"] == 0
    assert ui_capability["summary"]["uoc_008_runtime_capability_execution_enabled_total"] == 0
    # Later sprints may bind typed adapters, but arbitrary/remote execution remains prohibited.
    for item in capability["capabilities"]:
        if item["runtime"]["execution_enabled"]:
            assert item["runtime"]["adapter_bound"] is True
            assert item["contracts"]["typed_parameters_schema_id"]
    source = (ROOT / "src/devpilot_core/application/governed_job_operations.py").read_text(encoding="utf-8")
    assert "shell=False" in source
    assert "taskkill" in source
    assert "GovernedJobRuntimeLock" in source
    assert "record_progress" in source
    assert "eval(" not in source and "exec(" not in source and "shell=True" not in source


def test_uoc008_job_console_uses_typed_client_and_has_operational_states() -> None:
    view = (ROOT / "ui/web/src/pages/JobsView.ts").read_text(encoding="utf-8")
    main = (ROOT / "ui/web/src/main.ts").read_text(encoding="utf-8")
    assert "ui.jobs" in main and "path: '/jobs'" in main
    for marker in ("Job Console", "Heartbeat", "STALE", "Solicitar cancelación", "Crear retry gobernado", "Logs sanitizados"):
        assert marker in view
    for marker in ("listJobs", "inspectJob", "jobLogs", "cancelJob", "retryJob"):
        assert marker in view
    assert "child_process" not in view and "devpilot_core" not in view


def test_uoc008_documentation_and_schemas_are_registered() -> None:
    for relative in (
        "docs/07_interfaces/job_console_operational_observability.md",
        "docs/audits/uoc_008_job_console_operational_observability_report.md",
        "docs/post_h_eval_002_uoc_008_manifest.json",
        "docs/schemas/job_operational_snapshot.schema.json",
        "docs/schemas/job_log_page.schema.json",
    ):
        assert (ROOT / relative).is_file(), relative
    catalog = load_json("docs/schemas/schema_catalog.json")
    ids = {item["schema_id"] for item in catalog["schemas"]}
    assert "SCHEMA-DEVPL-JOB-OPERATIONAL-SNAPSHOT-V1" in ids
    assert "SCHEMA-DEVPL-JOB-LOG-PAGE-V1" in ids


def test_uoc008_manifest_is_lifecycle_aware_and_freezes_its_own_baseline() -> None:
    manifest = load_json("docs/post_h_eval_002_uoc_008_manifest.json")
    assert manifest["baseline_repo"] == "repo_DevPilot_Local_335_POST_H_EVAL_002_UOC_007.zip"
    assert manifest["baseline_sha256"] == "5134ffb607ec65fa3c2a1a720505bcf6583fb3edcaacd66f6b65c883990ffde0"
    assert manifest["browser_acceptance_required"] is True
    assert manifest["status"] in {"implemented-initial/pending-windows-browser-closure", "closed/PASS"}
    if manifest["status"] == "implemented-initial/pending-windows-browser-closure":
        assert manifest["criteria"]["windows_browser_acceptance"] == "pending"
        assert manifest["uoc_009_authorized"] is False
    else:
        assert manifest["criteria"]["windows_browser_acceptance"] == "PASS"
        assert manifest["criteria"]["canonical_closure"] == "PASS"
        assert manifest["output_repo"] == "repo_DevPilot_Local_336_POST_H_EVAL_002_UOC_008.zip"
        assert manifest["uoc_009_authorized"] is True
