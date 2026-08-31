from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "43254e3e61cdafe65e0ed2d773fe9032b0a81f05"


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate_instance(schema_path: str, instance_path: str) -> None:
    schema = read_json(schema_path)
    instance = read_json(instance_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda item: list(item.path))
    assert errors == [], "\n".join(error.message for error in errors)


def test_uoc_000_backlog_is_approved_and_uoc_001_is_next() -> None:
    text = (ROOT / "docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md").read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert 'status: "approved"' in frontmatter
    assert "UOC-000" in frontmatter and "closed/PASS" in frontmatter
    assert 'current_sprint: "UOC-' in frontmatter
    completed_line = next(line for line in frontmatter.splitlines() if line.startswith("completed_sprints:"))
    assert "UOC-000" in completed_line and "UOC-001" in completed_line
    assert "No se adelanta un sprint" in text


def test_ui_capability_registry_schema_and_complete_inventory() -> None:
    validate_instance(
        "docs/schemas/ui_capability_registry.schema.json",
        ".devpilot/interfaces/ui_capability_registry.json",
    )
    registry = read_json(".devpilot/interfaces/ui_capability_registry.json")
    cli = read_json(".devpilot/cli_registry/command_ownership_matrix.json")
    api = read_json(".devpilot/interfaces/api_route_contract_registry.json")
    ui = read_json(".devpilot/interfaces/ui_route_contract_registry.json")
    capabilities = registry["capabilities"]
    assert BASE_COMMIT in set(registry["source_commits"].values())
    assert read_json(".devpilot/project_state.json")["uoc_000_base_commit"] == BASE_COMMIT
    assert len(capabilities) == cli["summary"]["commands_total"]
    assert len(capabilities) >= 193
    assert {item["cli_command_id"] for item in capabilities} == {item["command_id"] for item in cli["commands"]}
    assert len({item["capability_id"] for item in capabilities}) == len(capabilities)
    assert registry["summary"]["classification_complete"] is True
    assert registry["summary"]["api_routes_total"] == len(api["routes"])
    assert registry["summary"]["api_routes_total"] >= 39
    assert registry["summary"]["ui_routes_total"] == len(ui["routes"])
    assert registry["summary"]["ui_routes_total"] >= 5
    assert {item["route_id"] for item in registry["ui_routes"]} == {item["route_id"] for item in ui["routes"]}


def test_uoc_000_policy_and_approval_gates() -> None:
    registry = read_json(".devpilot/interfaces/ui_capability_registry.json")
    capabilities = registry["capabilities"]
    assert registry["summary"]["mutating_without_policy_total"] == 0
    assert registry["summary"]["sensitive_ui_native_without_approval_total"] == 0
    assert all(item["policy"]["required"] for item in capabilities if item["risk_class"] in {"mutating", "sensitive", "forbidden"})
    assert all(item["parity_status"] == "POLICY-BLOCKED" for item in capabilities if item["risk_class"] == "forbidden")
    assert all(item["requires_approval"] for item in capabilities if item["risk_class"] == "sensitive" and item["parity_status"] == "UI-NATIVE")
    assert registry["safety"]["new_ui_routes_added"] >= 0
    uoc000_manifest = read_json("docs/post_h_eval_002_uoc_000_manifest.json")
    assert uoc000_manifest["gates"]["runtime_execution_enabled"] is False
    assert registry["safety"]["arbitrary_shell_allowed"] is False
    if registry["safety"]["runtime_execution_enabled"]:
        state = read_json(".devpilot/project_state.json")
        assert state.get("uoc_003_closed") is True
        assert registry["safety"]["remote_execution_enabled"] is False
        assert registry["safety"]["connector_write_enabled"] is False
        assert registry["safety"]["plugin_execution_enabled"] is False


def test_all_registry_references_resolve() -> None:
    registry = read_json(".devpilot/interfaces/ui_capability_registry.json")
    api_ids = {item["route_id"] for item in read_json(".devpilot/interfaces/api_route_contract_registry.json")["routes"]}
    ui_ids = {item["route_id"] for item in read_json(".devpilot/interfaces/ui_route_contract_registry.json")["routes"]}
    capability_ids = {item["capability_id"] for item in registry["capabilities"]}
    for capability in registry["capabilities"]:
        assert set(capability["api_route_ids"]) <= api_ids
        assert set(capability["ui_route_ids"]) <= ui_ids
    for route in registry["ui_routes"]:
        assert set(route["allowed_api_route_ids"]) <= api_ids
        assert set(route["mapped_cli_capability_ids"]) <= capability_ids


def test_base_resource_schemas_are_valid() -> None:
    paths = [
        "docs/schemas/ui_document_resource.schema.json",
        "docs/schemas/ui_edit_plan.schema.json",
        "docs/schemas/ui_approval_binding.schema.json",
        "docs/schemas/ui_governed_job.schema.json",
        "docs/schemas/ui_evidence_reference.schema.json",
        "docs/schemas/ui_operational_console_flags.schema.json",
        "docs/schemas/ui_operational_console_manifest.schema.json",
    ]
    for path in paths:
        Draft202012Validator.check_schema(read_json(path))
    validate_instance(
        "docs/schemas/ui_operational_console_flags.schema.json",
        ".devpilot/interfaces/ui_operational_console_flags.json",
    )
    validate_instance(
        "docs/schemas/ui_operational_console_manifest.schema.json",
        "docs/post_h_eval_002_uoc_000_manifest.json",
    )


def test_feature_flags_and_kill_switches_fail_closed() -> None:
    flags = read_json(".devpilot/interfaces/ui_operational_console_flags.json")
    assert flags["default_mode"] == "disabled-until-sprint-gate"
    enabled = {item["flag_id"] for item in flags["feature_flags"] if item["enabled"]}
    assert {"uoc.documents.read_only", "uoc.documents.metadata_git_search"} <= enabled
    state = read_json(".devpilot/project_state.json")
    authorized_numbers = [
        number for number in range(1, 12)
        if state.get(f"uoc_{number:03d}_authorized") is True or state.get(f"uoc_{number:03d}_closed") is True
    ]
    highest_authorized = max(authorized_numbers, default=0)
    for item in flags["feature_flags"]:
        match = __import__("re").match(r"UOC-(\d{3})$", item["owner_sprint"])
        if match and int(match.group(1)) > highest_authorized:
            assert item["enabled"] is False
    assert all(item["state"] == "engaged" for item in flags["kill_switches"])
    safety = flags["safety"]
    assert safety["arbitrary_shell_allowed"] is False
    assert safety["remote_execution_enabled"] is False
    assert safety["connector_write_enabled"] is False
    assert safety["plugin_execution_enabled"] is False
    assert safety["external_api_required"] is False


def test_uoc_000_adrs_freeze_required_decisions() -> None:
    no_shell = (ROOT / "docs/architecture/adr_ui_no_arbitrary_shell.md").read_text(encoding="utf-8")
    opaque = (ROOT / "docs/architecture/adr_ui_opaque_resource_identifiers.md").read_text(encoding="utf-8")
    jobs = (ROOT / "docs/architecture/adr_governed_job_execution.md").read_text(encoding="utf-8")
    assert 'status: "approved"' in no_shell
    assert "No se implementa terminal web" in no_shell
    assert "shell=True" in no_shell
    assert 'decision: "opaque-identifiers-only"' in opaque
    assert "PathGuard" in opaque
    assert 'decision: "typed-governed-jobs"' in jobs
    assert "maximum" not in jobs or "7200" in jobs
    assert "no loops autónomos ilimitados" in jobs


def test_project_state_and_manifest_close_uoc_000() -> None:
    state = read_json(".devpilot/project_state.json")
    manifest = read_json("docs/post_h_eval_002_uoc_000_manifest.json")
    assert state["post_h_eval_002_canonical_commit"] == BASE_COMMIT
    assert state["api_gap_sec_001_closed"] is True
    assert state["uoc_000_closed"] is True
    assert state["uoc_000_s0_open"] == 0
    assert state["uoc_000_s1_open"] == 0
    assert state["uoc_001_authorized"] is True
    assert manifest["status"] == "implemented-initial"
    assert manifest["gates"]["all_cli_commands_classified"] is True
    assert manifest["gates"]["all_ui_routes_mapped"] is True
    assert manifest["next_sprint"] == "UOC-001"


def test_uoc_000_is_registered_in_tcr_and_docs_governance() -> None:
    contract_id = "post-h-eval-002-uoc-000-capability-contracts"
    v1 = read_json(".devpilot/testing/test_contract_registry.json")
    v2 = read_json(".devpilot/testing/test_contract_registry_v2.json")
    sources = read_json(".devpilot/docs_governance/source_registry.json")
    assert sum(item["contract_id"] == contract_id for item in v1["contracts"]) == 1
    assert sum(item["contract_id"] == contract_id for item in v2["contracts"]) == 1
    paths = {item["path"] for item in sources["documents"]}
    required = {
        "docs/backlogs/POST-H-EVAL-002_ui_operational_console_evolution.md",
        ".devpilot/interfaces/ui_capability_registry.json",
        "docs/07_interfaces/ui_capability_registry.md",
        "docs/audits/uoc_000_capability_inventory_report.md",
        "docs/post_h_eval_002_uoc_000_manifest.json",
        "tests/test_post_h_eval_002_uoc_000_contracts.py",
    }
    assert required <= paths
