from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

DEFAULT_UI_ROUTE_CONTRACT_REGISTRY = Path(".devpilot/interfaces/ui_route_contract_registry.json")
DEFAULT_API_ROUTE_CONTRACT_REGISTRY = Path(".devpilot/interfaces/api_route_contract_registry.json")
UI_ROUTE_CONTRACT_REGISTRY_SCHEMA = "UiRouteContractRegistry"
POST_H_014_C_CREATED_BY = "POST-H-014-C"

_REQUIRED_CRITICAL_UI_ROUTES = {
    "ui.dashboard",
    "ui.reports",
    "ui.traces",
    "ui.approvals",
    "ui.settings",
}
_REQUIRED_STATUSES = {"PASS", "BLOCK", "ERROR", "PENDING"}
_NO_GO_FLAGS = (
    "remote_execution_allowed",
    "connector_write_allowed",
    "plugin_execution_allowed",
    "external_api_allowed",
)


class UiRouteContractRegistryValidator:
    """Validate the POST-H-014-C Web UI route contract registry.

    This validator is deterministic and read-only. It validates the registry
    structure, verifies that every allowed API route references the existing
    ApiRouteContractRegistry, checks product-state requirements, and confirms
    that the declared source files carry contract markers. It does not start
    Vite, a browser, a FastAPI server, network calls or external APIs.
    """

    def __init__(
        self,
        root: Path,
        *,
        registry_path: str | Path = DEFAULT_UI_ROUTE_CONTRACT_REGISTRY,
        api_registry_path: str | Path = DEFAULT_API_ROUTE_CONTRACT_REGISTRY,
    ) -> None:
        self.root = Path(root)
        self.registry_path = Path(registry_path)
        self.api_registry_path = Path(api_registry_path)

    @property
    def resolved_registry_path(self) -> Path:
        return self.root / self.registry_path

    @property
    def resolved_api_registry_path(self) -> Path:
        return self.root / self.api_registry_path

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        schema_result = SchemaValidator(self.root).validate(
            schema=UI_ROUTE_CONTRACT_REGISTRY_SCHEMA,
            instance=self.registry_path,
        )
        if not schema_result.ok:
            findings.extend(schema_result.findings)

        try:
            payload = json.loads(self.resolved_registry_path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(
                Finding(
                    id="UI_ROUTE_CONTRACT_REGISTRY_LOAD_ERROR",
                    message=f"UI route contract registry could not be loaded: {exc}",
                    severity=Severity.ERROR,
                    path=_display(self.registry_path),
                )
            )
            return self._result(False, findings, {})

        try:
            api_payload = json.loads(self.resolved_api_registry_path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(
                Finding(
                    id="UI_ROUTE_CONTRACT_API_REGISTRY_LOAD_ERROR",
                    message=f"API route contract registry could not be loaded: {exc}",
                    severity=Severity.ERROR,
                    path=_display(self.api_registry_path),
                )
            )
            return self._result(False, findings, {})

        routes = [item for item in payload.get("routes", []) if isinstance(item, dict)]
        route_ids = [str(route.get("route_id", "")) for route in routes]
        api_route_ids = {str(route.get("route_id", "")) for route in api_payload.get("routes", []) if isinstance(route, dict)}

        duplicate_route_ids = sorted({route_id for route_id in route_ids if route_ids.count(route_id) > 1 and route_id})
        for route_id in duplicate_route_ids:
            findings.append(
                Finding(
                    id="UI_ROUTE_CONTRACT_DUPLICATE_ID",
                    message=f"Duplicate UI route contract id: {route_id}",
                    severity=Severity.BLOCK,
                    path=_display(self.registry_path),
                    metadata={"route_id": route_id},
                )
            )

        missing_critical = sorted(_REQUIRED_CRITICAL_UI_ROUTES - set(route_ids))
        for route_id in missing_critical:
            findings.append(
                Finding(
                    id="UI_ROUTE_CONTRACT_CRITICAL_PAGE_MISSING",
                    message=f"Critical UI page is not contract-registered: {route_id}",
                    severity=Severity.BLOCK,
                    path=_display(self.registry_path),
                    metadata={"route_id": route_id},
                )
            )

        unknown_api_routes: list[dict[str, str]] = []
        no_go_violations: list[dict[str, str]] = []
        missing_state_contracts: list[str] = []
        missing_status_visibility: list[str] = []
        missing_badges: list[str] = []
        missing_source_files: list[dict[str, str]] = []
        missing_source_markers: list[dict[str, str]] = []
        mutation_controls_missing_justification: list[str] = []

        for route in routes:
            route_id = str(route.get("route_id", ""))
            for api_route_id in route.get("allowed_api_routes", []) or []:
                if api_route_id not in api_route_ids:
                    unknown_api_routes.append({"route_id": route_id, "api_route_id": str(api_route_id)})
                    findings.append(
                        Finding(
                            id="UI_ROUTE_CONTRACT_UNKNOWN_API_ROUTE",
                            message=f"UI route {route_id} references unknown API route {api_route_id}.",
                            severity=Severity.BLOCK,
                            path=_display(self.registry_path),
                            metadata={"route_id": route_id, "api_route_id": api_route_id},
                        )
                    )

            for flag in _NO_GO_FLAGS:
                if route.get(flag) is not False:
                    no_go_violations.append({"route_id": route_id, "flag": flag})
                    findings.append(
                        Finding(
                            id="UI_ROUTE_CONTRACT_NO_GO_FLAG_ENABLED",
                            message=f"UI route {route_id} violates no-go flag {flag}.",
                            severity=Severity.BLOCK,
                            path=_display(self.registry_path),
                            metadata={"route_id": route_id, "flag": flag, "value": route.get(flag)},
                        )
                    )

            if not all(route.get(name) is True for name in ("local_first_badge_required", "dry_run_badge_required", "no_remote_badge_required")):
                missing_badges.append(route_id)

            state_contract = route.get("state_contract") or {}
            if not all(state_contract.get(name) is True for name in ("loading", "empty", "error", "block_visible")):
                missing_state_contracts.append(route_id)

            statuses = set(route.get("status_visibility") or [])
            if not _REQUIRED_STATUSES.issubset(statuses):
                missing_status_visibility.append(route_id)

            if route.get("shows_mutation_controls") is True:
                mutation_controls = route.get("mutation_controls") or {}
                if mutation_controls.get("destructive_action_allowed") is not False or not str(mutation_controls.get("justification", "")).strip():
                    mutation_controls_missing_justification.append(route_id)

            for source_file in route.get("source_files", []) or []:
                source_path = self.root / str(source_file)
                if not source_path.exists():
                    missing_source_files.append({"route_id": route_id, "source_file": str(source_file)})
                    findings.append(
                        Finding(
                            id="UI_ROUTE_CONTRACT_SOURCE_FILE_MISSING",
                            message=f"Source file declared by {route_id} does not exist: {source_file}",
                            severity=Severity.BLOCK,
                            path=str(source_file),
                            metadata={"route_id": route_id},
                        )
                    )
                    continue
                source = source_path.read_text(encoding="utf-8")
                if route_id not in source:
                    missing_source_markers.append({"route_id": route_id, "source_file": str(source_file)})

        for route_id in missing_badges:
            findings.append(Finding("UI_ROUTE_CONTRACT_BADGES_MISSING", f"UI route {route_id} does not require local/dry-run/no-remote badges.", Severity.BLOCK, metadata={"route_id": route_id}))
        for route_id in missing_state_contracts:
            findings.append(Finding("UI_ROUTE_CONTRACT_STATES_MISSING", f"UI route {route_id} does not declare loading/empty/error/block-visible states.", Severity.BLOCK, metadata={"route_id": route_id}))
        for route_id in missing_status_visibility:
            findings.append(Finding("UI_ROUTE_CONTRACT_STATUS_VISIBILITY_MISSING", f"UI route {route_id} does not expose required PASS/BLOCK/ERROR/PENDING status visibility.", Severity.BLOCK, metadata={"route_id": route_id}))
        for route_id in mutation_controls_missing_justification:
            findings.append(Finding("UI_ROUTE_CONTRACT_MUTATION_JUSTIFICATION_MISSING", f"UI route {route_id} shows mutation controls without safe local justification.", Severity.BLOCK, metadata={"route_id": route_id}))
        for item in missing_source_markers:
            findings.append(
                Finding(
                    id="UI_ROUTE_CONTRACT_SOURCE_MARKER_MISSING",
                    message=f"Source file {item['source_file']} does not reference contract id {item['route_id']}.",
                    severity=Severity.BLOCK,
                    path=item["source_file"],
                    metadata=item,
                )
            )

        summary = {
            "schema_valid": schema_result.ok,
            "routes_total": len(routes),
            "critical_routes_total": sum(1 for route in routes if route.get("critical") is True),
            "required_critical_routes_total": len(_REQUIRED_CRITICAL_UI_ROUTES),
            "missing_critical_routes_total": len(missing_critical),
            "unknown_api_routes_total": len(unknown_api_routes),
            "no_go_violations_total": len(no_go_violations),
            "missing_source_files_total": len(missing_source_files),
            "missing_source_markers_total": len(missing_source_markers),
            "pages_missing_state_contracts_total": len(missing_state_contracts),
            "pages_missing_status_visibility_total": len(missing_status_visibility),
            "pages_missing_badges_total": len(missing_badges),
            "mutation_controls_missing_justification_total": len(mutation_controls_missing_justification),
            "local_first": payload.get("safety", {}).get("local_first") is True,
            "dry_run_visible": payload.get("safety", {}).get("dry_run_visible") is True,
            "external_api_allowed": payload.get("safety", {}).get("external_api_allowed") is True,
            "read_only": True,
            "network_used": False,
            "external_api_used": False,
            "source_mutations_performed": False,
        }
        return self._result(not _has_blocking(findings), findings, summary)

    def _result(self, ok: bool, findings: list[Finding], summary: dict[str, Any]) -> CommandResult:
        if ok:
            findings.append(
                Finding(
                    id="UI_ROUTE_CONTRACT_REGISTRY_PASS",
                    message="UI route contract registry validation passed.",
                    severity=Severity.INFO,
                    metadata=summary,
                )
            )
        return CommandResult(
            command="ui route-contracts validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else ExitCode.BLOCK,
            message="UI route contract registry validation passed." if ok else "UI route contract registry validation has blocking findings.",
            data={
                "summary": summary,
                "registry_path": _display(self.registry_path),
                "api_registry_path": _display(self.api_registry_path),
                "notes": [
                    "POST-H-014-C validates UI route contracts read-only and never starts a browser, server, network call or external API.",
                    "Quality-gate integration is intentionally deferred to POST-H-014-E.",
                ],
            },
            findings=findings,
        )


def validate_ui_route_contract_registry(root: Path, registry_path: str | Path = DEFAULT_UI_ROUTE_CONTRACT_REGISTRY) -> CommandResult:
    return UiRouteContractRegistryValidator(root, registry_path=registry_path).validate()


def _has_blocking(findings: list[Finding]) -> bool:
    return any(finding.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for finding in findings)


def _display(path: str | Path) -> str:
    return str(path).replace("\\", "/")
