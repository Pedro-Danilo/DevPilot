from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from devpilot_core.workspace.environment_discovery import (
    BOOTSTRAP_PLAN_SCHEMA_ID,
    ENVIRONMENT_DISCOVERY_SCHEMA_ID,
    EnvironmentDiscoveryService,
    ToolProbeSpec,
    _find_executable_candidates,
    _locate_npm_cli,
    _locate_npm_cli_from_node,
    _run_read_only,
    sanitized_environment_keys,
)

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def intake_for(target: Path, *, mode: str = "CREATE_NEW") -> dict:
    payload = load("evals/fixtures/gsdlc_03_a_inventory_sales_intake.valid.json")
    payload["target_root"] = str(target)
    payload["entry_mode"] = mode
    payload.pop("git_source", None)
    return payload


def ready_tool(tool_id: str, minimum: str, path: str | None = None) -> dict:
    versions = {"python": "3.13.0", "node": "22.0.0", "npm": "10.9.0", "git": "2.50.0"}
    selected = path or str(Path(sys.executable).resolve())
    return {
        "tool_id": tool_id,
        "minimum_version": minimum,
        "status": "ready",
        "candidates_total": 1,
        "candidate_paths": [selected],
        "selected_path": selected,
        "version": versions[tool_id],
        "meets_minimum": True,
        "probe_mode": "typed-read-only",
        "shell_used": False,
        "message": "deterministic test probe",
    }


def install_ready_probes(monkeypatch, service: EnvironmentDiscoveryService) -> None:
    def probe(spec: ToolProbeSpec):
        return ready_tool(spec.tool_id, spec.minimum_version)

    def probe_npm(*, minimum_version: str, node_probe):
        row = ready_tool("npm", minimum_version)
        row["execution_mode"] = "node+npm-cli.js"
        row["native_cli_path"] = "C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js"
        return row

    monkeypatch.setattr(service, "_probe_tool", probe)
    monkeypatch.setattr(service, "_probe_npm", probe_npm)


def test_03_b_schemas_and_catalog_are_registered_and_valid() -> None:
    catalog = load(".devpilot/workspaces/bootstrap_planning_catalog.json")
    schemas = {
        "docs/schemas/bootstrap_planning_catalog.schema.json": catalog,
    }
    for rel, instance in schemas.items():
        schema = load(rel)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(instance)

    schema_catalog = load("docs/schemas/schema_catalog.json")
    ids = {row["schema_id"] for row in schema_catalog["schemas"]}
    assert {
        "SCHEMA-DEVPL-GSDLC-03-B-ENVIRONMENT-DISCOVERY-REPORT-V1",
        "SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLAN-V1",
        "SCHEMA-DEVPL-GSDLC-03-B-BOOTSTRAP-PLANNING-CATALOG-V1",
    } <= ids


def test_create_discovery_and_bootstrap_plan_are_read_only_deterministic_and_schema_valid(tmp_path: Path, monkeypatch) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    target = allowed / "worktrees" / "project-a"
    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(allowed,))
    install_ready_probes(monkeypatch, service)
    payload = intake_for(target)

    before = sorted(str(p.relative_to(allowed)) for p in allowed.rglob("*"))
    discovery = service.discover(payload)
    assert discovery.ok, discovery.to_dict()
    report = discovery.data["report"]
    assert report["schema_id"] == ENVIRONMENT_DISCOVERY_SCHEMA_ID
    assert report["safety"]["writes_performed"] is False
    assert report["safety"]["network_used"] is False
    assert report["filesystem"]["write_probe_performed"] is False
    assert not target.exists()
    Draft202012Validator(load("docs/schemas/environment_discovery_report.schema.json")).validate(report)

    first = service.build_bootstrap_plan(payload)
    second = service.build_bootstrap_plan(payload)
    assert first.ok and second.ok
    plan = first.data["bootstrap_plan"]
    assert plan == second.data["bootstrap_plan"]
    assert plan["schema_id"] == BOOTSTRAP_PLAN_SCHEMA_ID
    assert plan["planning_only"] is True and plan["execution_enabled"] is False
    assert plan["safety"]["writes_performed"] is False
    assert plan["safety"]["network_used"] is False
    assert plan["network"]["runtime_network_used"] is False
    assert plan["network"]["required_by_plan"] is True
    assert len(plan["directories"]) > 0 and len(plan["files"]) > 0
    assert plan["venv"]["required"] is True and plan["venv"]["writes"] is True
    assert len(plan["dependency_jobs"]) == 2
    assert all(row["execution_status"] == "planned-only" for row in plan["dependency_jobs"])
    assert first.data["ui_projection"]["execution_enabled"] is False
    Draft202012Validator(load("docs/schemas/bootstrap_plan.schema.json")).validate(plan)
    after = sorted(str(p.relative_to(allowed)) for p in allowed.rglob("*"))
    assert after == before
    assert not target.exists()


def test_open_existing_plan_does_not_invent_create_side_effects(tmp_path: Path, monkeypatch) -> None:
    allowed = tmp_path / "evaluation"
    target = allowed / "existing"
    target.mkdir(parents=True)
    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(allowed,))
    install_ready_probes(monkeypatch, service)
    monkeypatch.setattr(service, "_git_discovery", lambda intake, git_probe: {
        "status": "PASS", "root": str(target), "head": "a" * 40, "dirty": False,
        "status_entries_total": 0, "status_payload_exposed": False, "writes_performed": False,
    })
    payload = intake_for(target, mode="OPEN_EXISTING")
    result = service.build_bootstrap_plan(payload)
    assert result.ok, result.to_dict()
    plan = result.data["bootstrap_plan"]
    assert plan["directories"] == []
    assert plan["files"] == []
    assert plan["dependency_jobs"] == []
    assert plan["venv"]["required"] is False and plan["venv"]["writes"] is False
    assert [row["operation_id"] for row in plan["git_operations"]] == []
    assert [row["kind"] for row in plan["expected_side_effects"]] == ["workspace-registration"]


def test_remote_import_is_plan_only_network_declared_and_not_contacted(tmp_path: Path, monkeypatch) -> None:
    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    target = allowed / "imported"
    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(allowed,))
    install_ready_probes(monkeypatch, service)
    payload = intake_for(target, mode="IMPORT_GIT")
    payload["git_source"] = {"kind": "remote-url", "location": "https://example.invalid/repo.git"}
    result = service.build_bootstrap_plan(payload)
    assert result.ok, result.to_dict()
    plan = result.data["bootstrap_plan"]
    clone = [row for row in plan["git_operations"] if row["operation_id"] == "git.clone.remote"]
    assert len(clone) == 1
    assert clone[0]["network_required"] is True
    assert clone[0]["remote_execution_enabled"] is False
    assert clone[0]["network_approval_required"] is True
    assert plan["network"] == {
        "required_by_plan": True,
        "runtime_network_used": False,
        "silent_network_allowed": False,
        "remote_git_disabled_by_default": True,
    }
    assert plan["directories"] == [] and plan["files"] == [] and plan["dependency_jobs"] == []
    assert plan["venv"]["required"] is False
    assert result.data["discovery"]["git"]["status"] == "PLAN_ONLY_REMOTE"
    assert result.data["discovery"]["git"]["network_used"] is False


def test_missing_and_ambiguous_executables_fail_closed_without_installer(tmp_path: Path, monkeypatch) -> None:
    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(tmp_path,))
    import devpilot_core.workspace.environment_discovery as module

    monkeypatch.setattr(module, "_find_executable_candidates", lambda names: [])
    missing = service._probe_tool(ToolProbeSpec("node", "20.0", ("node",), ("--version",)))
    assert missing["status"] == "missing"
    assert service._tool_findings(missing)[0].severity.value == "block"

    a = tmp_path / "a" / "node.exe"
    b = tmp_path / "b" / "node.exe"
    monkeypatch.setattr(module, "_find_executable_candidates", lambda names: [a, b])
    ambiguous = service._probe_tool(ToolProbeSpec("node", "20.0", ("node.exe",), ("--version",)))
    assert ambiguous["status"] == "ambiguous"
    assert ambiguous["candidates_total"] == 2
    assert service._tool_findings(ambiguous)[0].severity.value == "block"


def test_path_scanner_detects_multiple_distinct_candidates(tmp_path: Path, monkeypatch) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    first.mkdir(); second.mkdir()
    name = "devpilot-probe.exe" if sys.platform.startswith("win") else "devpilot-probe"
    for directory in (first, second):
        p = directory / name
        p.write_text("probe", encoding="utf-8")
        try:
            p.chmod(0o755)
        except OSError:
            pass
    monkeypatch.setenv("PATH", str(first) + __import__("os").pathsep + str(second))
    found = _find_executable_candidates((name,))
    assert len(found) == 2
    assert {p.parent for p in found} == {first.resolve(), second.resolve()}


def test_timeout_is_bounded_and_returns_structured_status() -> None:
    result = _run_read_only([sys.executable, "-c", "import time; time.sleep(0.2)"], timeout_seconds=0.01)
    assert result["status"] == "TIMEOUT"
    assert result["returncode"] == 124


def test_npm_windows_native_cli_layout_can_be_resolved_without_cmd(tmp_path: Path) -> None:
    node = tmp_path / "nodejs" / "node.exe"
    npm = tmp_path / "nodejs" / "npm.cmd"
    cli = tmp_path / "nodejs" / "node_modules" / "npm" / "bin" / "npm-cli.js"
    cli.parent.mkdir(parents=True)
    node.write_bytes(b"")
    npm.write_bytes(b"")
    cli.write_text("// fixture", encoding="utf-8")
    assert _locate_npm_cli(npm, node) == cli.resolve()


def test_environment_projection_never_exposes_secret_values(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DEVPILOT_API_TOKEN", "VERY-SENSITIVE-TOKEN")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert "DEVPILOT_API_TOKEN" not in sanitized_environment_keys()
    allowed = tmp_path / "evaluation"; allowed.mkdir()
    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(allowed,))
    install_ready_probes(monkeypatch, service)
    result = service.discover(intake_for(allowed / "target"))
    serialized = json.dumps(result.to_dict())
    assert "VERY-SENSITIVE-TOKEN" not in serialized
    assert "DEVPILOT_API_TOKEN" not in serialized
    assert result.data["report"]["environment"]["values_exposed"] is False


def test_03_b_api_route_and_rbac_successors_preserve_03_a_snapshots() -> None:
    api_snapshot = load(".devpilot/interfaces/api_route_contract_registry_gsdlc03a_at_close.json")
    api_current = load(".devpilot/interfaces/api_route_contract_registry.json")
    rbac_snapshot = load(".devpilot/identity/server_rbac_policy_catalog_gsdlc03a_at_close.json")
    rbac_current = load(".devpilot/identity/server_rbac_policy_catalog.json")
    assert api_snapshot["summary"]["routes_total"] == 98
    assert api_current["summary"]["routes_total"] == 100
    assert rbac_snapshot["summary"]["route_policies_total"] == 98
    assert rbac_current["summary"]["route_policies_total"] == 100
    for operation in {"project_entry.environment_discovery", "project_entry.bootstrap_plan"}:
        route = [row for row in api_current["routes"] if row["operation"] == operation]
        policy = [row for row in rbac_current["route_policies"] if row["operation"] == operation]
        assert len(route) == len(policy) == 1
        assert route[0]["mutations_allowed"] is False and route[0]["external_api_allowed"] is False
        assert policy[0]["human_session_required"] is True and policy[0]["legacy_token_allowed"] is False


def test_03_a_closure_authority_is_materialized_and_authorizes_03_b() -> None:
    adjudication = load("DEVPL_GSDLC_03_A_FINAL_OWNER_ADJUDICATION_v1_0_0.json")
    assert adjudication["decision"] == "CLOSED/PASS"
    assert adjudication["successor_commit"] == "2ebed62c243ea4034a5381023fb118de33c4aecd"
    assert adjudication["successor_sha256"] == "81212d518b21be447f136acf0357ef32a6f5e48c1975056dad7225d87a4b2d0b"
    assert adjudication["authorizes"] == "DEVPL-GSDLC-03-B"


def test_application_service_exposes_read_only_discovery_and_ui_plan_projection(tmp_path: Path, monkeypatch) -> None:
    from devpilot_core.application import ApplicationService
    from devpilot_core.interfaces.api.models import dispatch_application_request
    import devpilot_core.workspace.environment_discovery as module

    allowed = tmp_path / "evaluation"
    allowed.mkdir()
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(allowed))

    def probe(self, spec: ToolProbeSpec):
        return ready_tool(spec.tool_id, spec.minimum_version)

    def npm_probe(self, *, minimum_version: str, node_probe):
        row = ready_tool("npm", minimum_version)
        row["execution_mode"] = "node+npm-cli.js"
        row["native_cli_path"] = "C:/Program Files/nodejs/node_modules/npm/bin/npm-cli.js"
        return row

    monkeypatch.setattr(module.EnvironmentDiscoveryService, "_probe_tool", probe)
    monkeypatch.setattr(module.EnvironmentDiscoveryService, "_probe_npm", npm_probe)

    payload = intake_for(allowed / "new-project")
    service = ApplicationService(ROOT)
    discovery_body, discovery_status = dispatch_application_request(
        service, operation="project_entry.environment_discovery", payload={"intake": payload, "timeout_seconds": 1.0}
    )
    assert discovery_status == 200 and discovery_body["ok"] is True
    assert discovery_body["data"]["report"]["safety"]["writes_performed"] is False

    plan_body, plan_status = dispatch_application_request(
        service, operation="project_entry.bootstrap_plan", payload={"intake": payload, "timeout_seconds": 1.0}
    )
    assert plan_status == 200 and plan_body["ok"] is True
    assert plan_body["data"]["ui_projection"]["read_only"] is True
    assert plan_body["data"]["ui_projection"]["execution_enabled"] is False
    assert plan_body["data"]["bootstrap_plan"]["safety"]["pilot_workspace_accessed"] is False


def test_git_233_windows_compatibility_floor_is_explicit_successor_not_03a_rewrite(tmp_path: Path, monkeypatch) -> None:
    catalog = load(".devpilot/workspaces/technology_catalog.json")
    git_req = next(row for row in catalog["tool_requirements"] if row["tool_id"] == "git")
    assert git_req["minimum_version"] == "2.40"

    planning = load(".devpilot/workspaces/bootstrap_planning_catalog.json")
    rule = next(row for row in planning["tool_compatibility"] if row["tool_id"] == "git")
    assert rule["declared_minimum_version"] == "2.40"
    assert rule["effective_minimum_version"] == "2.33.0"
    assert rule["execution_scope"] == "discovery-and-planning-only"

    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(tmp_path,))
    spec = service._tool_spec("git", "2.40", entry_mode=__import__("devpilot_core.workspace.project_entry_contracts", fromlist=["ProjectEntryMode"]).ProjectEntryMode.CREATE_NEW)
    assert spec.minimum_version == "2.33.0"
    assert spec.declared_minimum_version == "2.40"
    assert spec.compatibility_policy == "validated-legacy-floor"


def test_windows_git_233_version_is_ready_under_03b_compatibility_policy(tmp_path: Path, monkeypatch) -> None:
    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(tmp_path,))
    git_path = tmp_path / "git.exe"
    git_path.write_bytes(b"fixture")
    spec = service._tool_spec("git", "2.40", entry_mode=__import__("devpilot_core.workspace.project_entry_contracts", fromlist=["ProjectEntryMode"]).ProjectEntryMode.CREATE_NEW)

    import devpilot_core.workspace.environment_discovery as module
    monkeypatch.setattr(module, "_find_executable_candidates", lambda names: [git_path])
    monkeypatch.setattr(module, "_run_read_only", lambda argv, timeout_seconds: {
        "status": "PASS", "returncode": 0, "stdout": "git version 2.33.0.windows.2", "stderr": "", "message": "fixture"
    })
    row = service._probe_tool(spec)
    assert row["status"] == "ready"
    assert row["version"] == "2.33.0"
    assert row["minimum_version"] == "2.33.0"
    assert row["declared_minimum_version"] == "2.40"
    assert row["meets_declared_minimum"] is False
    assert row["compatibility_policy"] == "validated-legacy-floor"


def test_npm_multiple_path_wrappers_do_not_override_selected_node_distribution(tmp_path: Path, monkeypatch) -> None:
    node = tmp_path / "nodejs" / "node.exe"
    cli = tmp_path / "nodejs" / "node_modules" / "npm" / "bin" / "npm-cli.js"
    cli.parent.mkdir(parents=True)
    node.write_bytes(b"fixture")
    cli.write_text("// fixture", encoding="utf-8")
    wrapper_a = tmp_path / "nodejs" / "npm.cmd"
    wrapper_b = tmp_path / "other" / "npm.cmd"
    wrapper_b.parent.mkdir()
    wrapper_a.write_bytes(b"fixture")
    wrapper_b.write_bytes(b"fixture")

    service = EnvironmentDiscoveryService(ROOT, allowed_roots=(tmp_path,))
    import devpilot_core.workspace.environment_discovery as module
    monkeypatch.setattr(module, "_find_executable_candidates", lambda names: [wrapper_a, wrapper_b])
    monkeypatch.setattr(module, "_run_read_only", lambda argv, timeout_seconds: {
        "status": "PASS", "returncode": 0, "stdout": "10.2.3", "stderr": "", "message": "fixture"
    })
    node_probe = ready_tool("node", "20.0", str(node))
    row = service._probe_npm(minimum_version="10.0", node_probe=node_probe)
    assert row["status"] == "ready"
    assert row["candidates_total"] == 1
    assert Path(row["selected_path"]) == cli.resolve()
    assert row["execution_mode"] == "node+npm-cli.js"
    assert row["version"] == "10.2.3"
