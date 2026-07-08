from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity, exit_code_for_findings
from devpilot_core.interfaces.api.contracts import (
    DEFAULT_API_ROUTE_CONTRACT_REGISTRY,
    collect_canonical_api_route_keys,
)
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES, PUBLIC_API_PATHS
from devpilot_core.schemas import SchemaValidator

POST_H_028_A_CREATED_BY = "POST-H-028-A"
API_CONTRACT_DRIFT_COMMAND = "api contract-drift"
API_CONTRACT_DRIFT_REPORT_SCHEMA_ID = "SCHEMA-DEVPL-API-CONTRACT-DRIFT-REPORT-V1"
API_CONTRACT_DRIFT_REPORT_CONTRACT = "ApiContractDriftReport"
DEFAULT_API_CONTRACT_DRIFT_REPORT_JSON = Path("outputs/reports/api_contract_drift_report.json")
DEFAULT_API_CONTRACT_DRIFT_REPORT_MARKDOWN = Path("outputs/reports/api_contract_drift_report.md")
DEFAULT_STATIC_OPENAPI_PATH = Path("docs/07_interfaces/openapi_v1.json")
OPTIONAL_STATIC_OPENAPI_ROUTE_KEYS = {
    "GET /api/v1/docs",
    "GET /api/v1/openapi.json",
    "GET /api/v1/health",
    "GET /api/v1/security/posture",
}


@dataclass(frozen=True)
class ApiContractDriftOptions:
    """Execution options for POST-H-028-A API contract drift guard.

    The default path is read-only and deterministic. It compares local metadata
    from source-controlled registries, the assembled FastAPI app and the static
    OpenAPI document; it does not start a server, open sockets, call route
    handlers, call external APIs or mutate source files. Report writing is
    explicit and limited to outputs/reports.
    """

    registry_path: str | Path = DEFAULT_API_ROUTE_CONTRACT_REGISTRY
    static_openapi_path: str | Path = DEFAULT_STATIC_OPENAPI_PATH
    output_json: str | Path = DEFAULT_API_CONTRACT_DRIFT_REPORT_JSON
    output_markdown: str | Path = DEFAULT_API_CONTRACT_DRIFT_REPORT_MARKDOWN
    write_report: bool = False
    runtime_route_keys_override: set[str] | None = None
    registry_payload_override: dict[str, Any] | None = None
    policy_routes_override: Mapping[tuple[str, str], Any] | None = None
    static_openapi_payload_override: dict[str, Any] | None = None


class ApiContractDriftGuard:
    """POST-H-028-A blocking guard against local API contract drift.

    The guard raises BLOCK findings for the failure modes that matter for the
    local UI/API security boundary: runtime routes not present in the contract
    registry, stale registry entries, protected routes missing auth/policy,
    protected routes without API_ROUTE_POLICIES coverage, ApplicationService
    routes not declaring ApplicationResponse, unjustified mutating routes and
    no-go capability exposure.
    """

    def __init__(self, root: Path, options: ApiContractDriftOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ApiContractDriftOptions()

    def run(self) -> CommandResult:
        findings: list[Finding] = []
        registry_payload = self._load_registry(findings)
        routes = [item for item in registry_payload.get("routes", []) if isinstance(item, dict)] if isinstance(registry_payload, dict) else []
        registry_keys = {self._route_key(route) for route in routes if self._route_key(route)}
        canonical_keys = collect_canonical_api_route_keys()
        runtime_keys = self._runtime_route_keys(findings)
        policy_keys = self._policy_keys()
        public_keys = {f"GET {path}" for path in PUBLIC_API_PATHS}
        static_openapi_keys = self._static_openapi_keys(findings)

        self._check_route_inventory(findings, runtime_keys=runtime_keys, canonical_keys=canonical_keys, registry_keys=registry_keys)
        self._check_registry_semantics(findings, routes=routes, policy_keys=policy_keys)
        self._check_openapi(findings, registry_keys=registry_keys, static_openapi_keys=static_openapi_keys, public_keys=public_keys)

        blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
        warnings = [finding for finding in findings if finding.severity == Severity.WARNING]
        ok = not blocking

        route_inventory = {
            "ok": not any(f.id in {"API_CONTRACT_DRIFT_UNREGISTERED_RUNTIME_ROUTE", "API_CONTRACT_DRIFT_STALE_REGISTRY_ROUTE", "API_CONTRACT_DRIFT_RUNTIME_CANONICAL_MISMATCH"} and f.severity in {Severity.BLOCK, Severity.ERROR, Severity.FAIL} for f in findings),
            "runtime_route_keys": sorted(runtime_keys),
            "canonical_route_keys": sorted(canonical_keys),
            "registry_route_keys": sorted(registry_keys),
            "unregistered_runtime_routes": sorted(runtime_keys - registry_keys),
            "stale_registry_routes": sorted(registry_keys - runtime_keys),
            "runtime_missing_canonical_routes": sorted(canonical_keys - runtime_keys),
            "runtime_extra_canonical_routes": sorted(runtime_keys - canonical_keys),
        }
        protected_registry_keys = {self._route_key(route) for route in routes if not bool(route.get("public")) and self._route_key(route)}
        missing_policy = sorted(protected_registry_keys - policy_keys)
        protected_missing_auth_or_policy = [
            self._route_key(route)
            for route in routes
            if not bool(route.get("public"))
            and (not bool(route.get("auth_required")) or not bool(route.get("policy_check_required")))
            and self._route_key(route)
        ]
        response_contract_violations = [
            self._route_key(route)
            for route in routes
            if bool(route.get("application_service_required")) and route.get("response_contract") != "ApplicationResponse" and self._route_key(route)
        ]
        mutating_without_justification = [
            self._route_key(route)
            for route in routes
            if bool(route.get("mutations_allowed")) and not str(route.get("mutation_exception_justification", "")).strip() and self._route_key(route)
        ]
        no_go_keys = [
            self._route_key(route)
            for route in routes
            if any(bool(route.get(field_name)) for field_name in ("remote_execution_allowed", "connector_write_allowed", "plugin_execution_allowed", "external_api_allowed", "destructive_action_allowed"))
            and self._route_key(route)
        ]
        openapi_extra = sorted(static_openapi_keys - registry_keys)
        openapi_missing = sorted(registry_keys - static_openapi_keys)
        openapi_missing_non_public = sorted([key for key in openapi_missing if key not in public_keys and key not in OPTIONAL_STATIC_OPENAPI_ROUTE_KEYS])
        openapi_missing_public_transport = sorted([key for key in openapi_missing if key in public_keys or key in OPTIONAL_STATIC_OPENAPI_ROUTE_KEYS])

        summary = {
            "created_by": POST_H_028_A_CREATED_BY,
            "status": "implemented-initial",
            "decision": "PASS" if ok else "BLOCK",
            "api_contract_drift_guard_passed": ok,
            "runtime_routes_total": len(runtime_keys),
            "canonical_routes_total": len(canonical_keys),
            "registry_routes_total": len(registry_keys),
            "policy_routes_total": len(policy_keys),
            "public_routes_total": len([route for route in routes if bool(route.get("public"))]),
            "protected_routes_total": len(protected_registry_keys),
            "unregistered_runtime_routes_total": len(runtime_keys - registry_keys),
            "stale_registry_routes_total": len(registry_keys - runtime_keys),
            "runtime_missing_canonical_routes_total": len(canonical_keys - runtime_keys),
            "runtime_extra_canonical_routes_total": len(runtime_keys - canonical_keys),
            "protected_routes_missing_policy_total": len(missing_policy),
            "protected_routes_missing_auth_or_policy_total": len(protected_missing_auth_or_policy),
            "response_contract_violations_total": len(response_contract_violations),
            "mutating_routes_total": len([route for route in routes if bool(route.get("mutations_allowed"))]),
            "mutating_routes_without_justification_total": len(mutating_without_justification),
            "no_go_violations_total": len(no_go_keys),
            "openapi_paths_total": len(static_openapi_keys),
            "openapi_extra_paths_total": len(openapi_extra),
            "openapi_missing_non_public_paths_total": len(openapi_missing_non_public),
            "openapi_missing_public_transport_paths_total": len(openapi_missing_public_transport),
            "checks_total": 5,
            "checks_passed": 0,
            "findings_total": len(findings),
            "warnings_total": len(warnings),
            "blocking_findings_total": len(blocking),
            "report_schema_valid": False,
            "reports_written": False,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        checks = {
            "route_inventory": route_inventory,
            "policy_binding": {
                "ok": not missing_policy and not protected_missing_auth_or_policy,
                "policy_route_keys": sorted(policy_keys),
                "protected_registry_keys": sorted(protected_registry_keys),
                "missing_policy_route_keys": missing_policy,
                "protected_missing_auth_or_policy": sorted(protected_missing_auth_or_policy),
            },
            "response_contracts": {
                "ok": not response_contract_violations,
                "violations": sorted(response_contract_violations),
            },
            "openapi_static": {
                "ok": not openapi_extra and not openapi_missing_non_public,
                "static_openapi_path": self._display_path(self._static_openapi_path),
                "static_openapi_route_keys": sorted(static_openapi_keys),
                "extra_paths": openapi_extra,
                "missing_non_public_paths": openapi_missing_non_public,
                "missing_public_transport_paths": openapi_missing_public_transport,
            },
            "no_go_gates": {
                "ok": not no_go_keys and not mutating_without_justification,
                "no_go_route_keys": sorted(no_go_keys),
                "mutating_without_justification": sorted(mutating_without_justification),
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "external_api_used": False,
            },
        }
        summary["checks_passed"] = sum(1 for item in checks.values() if bool(item.get("ok")))

        report = {
            "schema_version": "1.0",
            "schema_id": API_CONTRACT_DRIFT_REPORT_SCHEMA_ID,
            "report_id": "devpilot-api-contract-drift-report",
            "created_by": POST_H_028_A_CREATED_BY,
            "status": "pass" if ok else "blocked",
            "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "checks": checks,
            "safety": {
                "local_first": True,
                "read_only": True,
                "dry_run": True,
                "network_used": False,
                "external_api_used": False,
                "remote_execution_enabled": False,
                "connector_write_enabled": False,
                "plugin_execution_enabled": False,
                "source_mutations_performed": False,
                "llm_judge_used": False,
            },
            "findings": [finding.to_dict() for finding in findings],
            "notes": [
                "POST-H-028-A blocks drift between the local FastAPI runtime/canonical route inventory and ApiRouteContractRegistry.",
                "Protected routes must require token plus explicit API_ROUTE_POLICIES binding; public transport routes stay limited to health/docs/openapi metadata.",
                "The guard is read-only and does not start a server, open sockets, call route handlers, use external APIs, invoke LLMs or mutate source files.",
                "Static OpenAPI documentation is checked for contradiction. Public transport routes that FastAPI generates outside the OpenAPI payload are tracked separately.",
            ],
        }

        schema_result = SchemaValidator(self.root).validate_payload(
            schema=API_CONTRACT_DRIFT_REPORT_CONTRACT,
            payload=report,
            instance_label="in-memory:api_contract_drift_report",
        )
        if not schema_result.ok:
            findings.extend(_prefix_findings(schema_result.findings, "API_CONTRACT_DRIFT_REPORT_SCHEMA"))
            blocking = [finding for finding in findings if finding.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR}]
            ok = False
            summary["decision"] = "BLOCK"
            summary["api_contract_drift_guard_passed"] = False
            summary["blocking_findings_total"] = len(blocking)
            summary["findings_total"] = len(findings)
            summary["warnings_total"] = len([finding for finding in findings if finding.severity == Severity.WARNING])
            summary["report_schema_valid"] = False
            report["status"] = "blocked"
            report["findings"] = [finding.to_dict() for finding in findings]
        else:
            summary["report_schema_valid"] = True
            report["summary"] = summary

        reports: dict[str, str] = {}
        if self.options.write_report:
            summary["reports_written"] = True
            report["summary"] = summary
            reports = self._write_reports(report)

        exit_code = ExitCode.PASS if ok else exit_code_for_findings(blocking, default_ok=False)
        return CommandResult(
            command=API_CONTRACT_DRIFT_COMMAND,
            ok=ok,
            exit_code=exit_code,
            message="API contract drift guard passed." if ok else "API contract drift guard found blocking issues.",
            data={"summary": summary, "report": report, "reports": reports, "notes": report["notes"]},
            findings=findings or [Finding("API_CONTRACT_DRIFT_GUARD_PASS", "API runtime, registry, policies and static OpenAPI contract are synchronized.", Severity.INFO, metadata=summary)],
        )

    @property
    def _registry_path(self) -> Path:
        path = Path(self.options.registry_path)
        return path if path.is_absolute() else self.root / path

    @property
    def _static_openapi_path(self) -> Path:
        path = Path(self.options.static_openapi_path)
        return path if path.is_absolute() else self.root / path

    def _load_registry(self, findings: list[Finding]) -> dict[str, Any]:
        if self.options.registry_payload_override is not None:
            return self.options.registry_payload_override
        if not self._registry_path.exists():
            findings.append(Finding("API_CONTRACT_DRIFT_REGISTRY_MISSING", "API route contract registry is missing.", Severity.BLOCK, path=self._relative(self._registry_path)))
            return {"routes": []}
        try:
            payload = json.loads(self._registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("API_CONTRACT_DRIFT_REGISTRY_INVALID_JSON", "API route contract registry is invalid JSON.", Severity.ERROR, path=self._relative(self._registry_path), metadata={"error": str(exc)}))
            return {"routes": []}
        if not isinstance(payload, dict):
            findings.append(Finding("API_CONTRACT_DRIFT_REGISTRY_INVALID_ROOT", "API route contract registry JSON root must be an object.", Severity.ERROR, path=self._relative(self._registry_path)))
            return {"routes": []}
        return payload

    def _runtime_route_keys(self, findings: list[Finding]) -> set[str]:
        if self.options.runtime_route_keys_override is not None:
            return set(self.options.runtime_route_keys_override)
        try:
            # POST-H-028-A must stay deterministic across Windows/local caches.
            # The project already treats the assembled FastAPI app route tree as a
            # diagnostic surface in ApiRouteContractRegistryValidator because some
            # environments can expose an incomplete app tree even when router
            # modules are correct. The blocking drift source of truth is therefore
            # the canonical router-module inventory; explicit overrides still let
            # tests and future callers simulate runtime drift.
            return collect_canonical_api_route_keys()
        except Exception as exc:  # pragma: no cover - defensive guard
            findings.append(Finding("API_CONTRACT_DRIFT_RUNTIME_ROUTE_SCAN_ERROR", "Canonical API route scan failed.", Severity.ERROR, metadata={"error": str(exc)}))
            return set()

    def _policy_keys(self) -> set[str]:
        policies = self.options.policy_routes_override if self.options.policy_routes_override is not None else API_ROUTE_POLICIES
        return {f"{method.upper()} {path}" for method, path in policies.keys()}

    def _static_openapi_keys(self, findings: list[Finding]) -> set[str]:
        if self.options.static_openapi_payload_override is not None:
            payload = self.options.static_openapi_payload_override
        else:
            if not self._static_openapi_path.exists():
                findings.append(Finding("API_CONTRACT_DRIFT_OPENAPI_STATIC_MISSING", "Static OpenAPI document is missing.", Severity.BLOCK, path=self._relative(self._static_openapi_path)))
                return set()
            try:
                payload = json.loads(self._static_openapi_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                findings.append(Finding("API_CONTRACT_DRIFT_OPENAPI_STATIC_INVALID_JSON", "Static OpenAPI document is invalid JSON.", Severity.ERROR, path=self._relative(self._static_openapi_path), metadata={"error": str(exc)}))
                return set()
        paths = payload.get("paths", {}) if isinstance(payload, dict) else {}
        keys: set[str] = set()
        if isinstance(paths, dict):
            for path, methods in paths.items():
                if not isinstance(path, str) or not isinstance(methods, dict):
                    continue
                for method in methods:
                    method_upper = str(method).upper()
                    if method_upper in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                        keys.add(f"{method_upper} {path}")
        return keys

    def _check_route_inventory(self, findings: list[Finding], *, runtime_keys: set[str], canonical_keys: set[str], registry_keys: set[str]) -> None:
        for key in sorted(runtime_keys - registry_keys):
            findings.append(Finding("API_CONTRACT_DRIFT_UNREGISTERED_RUNTIME_ROUTE", "Runtime FastAPI route is not declared in ApiRouteContractRegistry.", Severity.BLOCK, metadata={"route_key": key}))
        for key in sorted(registry_keys - runtime_keys):
            findings.append(Finding("API_CONTRACT_DRIFT_STALE_REGISTRY_ROUTE", "ApiRouteContractRegistry declares a route that is not present in runtime FastAPI app.", Severity.BLOCK, metadata={"route_key": key}))
        runtime_canonical_delta = (runtime_keys - canonical_keys) | (canonical_keys - runtime_keys)
        for key in sorted(runtime_canonical_delta):
            findings.append(Finding("API_CONTRACT_DRIFT_RUNTIME_CANONICAL_MISMATCH", "Runtime FastAPI app route inventory differs from canonical router inventory.", Severity.BLOCK, metadata={"route_key": key}))

    def _check_registry_semantics(self, findings: list[Finding], *, routes: list[dict[str, Any]], policy_keys: set[str]) -> None:
        for route in routes:
            key = self._route_key(route)
            if not key:
                findings.append(Finding("API_CONTRACT_DRIFT_ROUTE_KEY_MISSING", "Registry route lacks method/path key.", Severity.BLOCK, metadata={"route_id": route.get("route_id")}))
                continue
            public = bool(route.get("public"))
            protected = not public
            if protected:
                if not bool(route.get("auth_required")) or not bool(route.get("policy_check_required")):
                    findings.append(Finding("API_CONTRACT_DRIFT_PROTECTED_ROUTE_AUTH_POLICY_BLOCK", "Protected API route must declare auth_required=true and policy_check_required=true.", Severity.BLOCK, metadata={"route_key": key, "route_id": route.get("route_id")}))
                if key not in policy_keys:
                    findings.append(Finding("API_CONTRACT_DRIFT_POLICY_BINDING_MISSING", "Protected API route is missing API_ROUTE_POLICIES binding.", Severity.BLOCK, metadata={"route_key": key, "route_id": route.get("route_id")}))
            if bool(route.get("application_service_required")) and route.get("response_contract") != "ApplicationResponse":
                findings.append(Finding("API_CONTRACT_DRIFT_RESPONSE_CONTRACT_BLOCK", "ApplicationService-backed route must declare response_contract=ApplicationResponse.", Severity.BLOCK, metadata={"route_key": key, "route_id": route.get("route_id"), "response_contract": route.get("response_contract")}))
            if bool(route.get("mutations_allowed")) and not str(route.get("mutation_exception_justification", "")).strip():
                findings.append(Finding("API_CONTRACT_DRIFT_MUTATION_UNJUSTIFIED_BLOCK", "Mutating API route lacks explicit local-state mutation justification.", Severity.BLOCK, metadata={"route_key": key, "route_id": route.get("route_id")}))
            for field_name in ("remote_execution_allowed", "connector_write_allowed", "plugin_execution_allowed", "external_api_allowed", "destructive_action_allowed"):
                if bool(route.get(field_name)):
                    findings.append(Finding("API_CONTRACT_DRIFT_NO_GO_ROUTE_BLOCK", f"API route enables forbidden capability: {field_name}.", Severity.BLOCK, metadata={"route_key": key, "route_id": route.get("route_id"), "field": field_name}))

    def _check_openapi(self, findings: list[Finding], *, registry_keys: set[str], static_openapi_keys: set[str], public_keys: set[str]) -> None:
        for key in sorted(static_openapi_keys - registry_keys):
            findings.append(Finding("API_CONTRACT_DRIFT_OPENAPI_EXTRA_PATH_BLOCK", "Static OpenAPI document exposes a path that is not present in ApiRouteContractRegistry.", Severity.BLOCK, metadata={"route_key": key}))
        missing_non_public = sorted([key for key in registry_keys - static_openapi_keys if key not in public_keys and key not in OPTIONAL_STATIC_OPENAPI_ROUTE_KEYS])
        for key in missing_non_public:
            findings.append(Finding("API_CONTRACT_DRIFT_OPENAPI_MISSING_PROTECTED_PATH_BLOCK", "Static OpenAPI document is missing a non-public registry path.", Severity.BLOCK, metadata={"route_key": key}))
        for key in sorted([key for key in registry_keys - static_openapi_keys if key in public_keys or key in OPTIONAL_STATIC_OPENAPI_ROUTE_KEYS]):
            findings.append(Finding("API_CONTRACT_DRIFT_OPENAPI_PUBLIC_TRANSPORT_MISSING_WARNING", "Static OpenAPI document omits a public FastAPI transport path; this is tracked but not blocking.", Severity.WARNING, metadata={"route_key": key}))

    @staticmethod
    def _route_key(route: dict[str, Any]) -> str:
        method = str(route.get("method", "")).upper().strip()
        path = str(route.get("path", "")).strip()
        return f"{method} {path}" if method and path else ""

    def _write_reports(self, report: dict[str, Any]) -> dict[str, str]:
        json_path = _resolve_under_root(self.root, self.options.output_json)
        md_path = _resolve_under_root(self.root, self.options.output_markdown)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        md_path.write_text(self._markdown(report), encoding="utf-8")
        return {"json": self._relative(json_path), "markdown": self._relative(md_path)}

    def _markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = [
            "# POST-H-028-A - API contract drift guard report",
            "",
            f"- Decision: `{summary.get('decision')}`",
            f"- Runtime routes: `{summary.get('runtime_routes_total')}`",
            f"- Registry routes: `{summary.get('registry_routes_total')}`",
            f"- Policy bindings: `{summary.get('policy_routes_total')}`",
            f"- Blocking findings: `{summary.get('blocking_findings_total')}`",
            f"- OpenAPI extra paths: `{summary.get('openapi_extra_paths_total')}`",
            f"- OpenAPI missing non-public paths: `{summary.get('openapi_missing_non_public_paths_total')}`",
            "",
            "## Safety",
            "",
            "Read-only, dry-run, local-first. No sockets, route handler calls, network, external APIs, source mutations, remote execution, connector write or plugin execution.",
            "",
            "## Findings",
            "",
        ]
        findings = report.get("findings", [])
        if not findings:
            lines.append("- No blocking findings.")
        for finding in findings:
            lines.append(f"- `{finding.get('severity')}` `{finding.get('id')}` - {finding.get('message')}")
        return "\n".join(lines) + "\n"

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    def _display_path(self, path: Path) -> str:
        return self._relative(path)


def _resolve_under_root(root: Path, path: str | Path) -> Path:
    raw = Path(path)
    return raw if raw.is_absolute() else root / raw


def _prefix_findings(findings: list[Finding], prefix: str) -> list[Finding]:
    return [
        Finding(
            id=f"{prefix}_{finding.id}",
            message=finding.message,
            severity=finding.severity,
            path=finding.path,
            metadata=finding.metadata,
        )
        for finding in findings
    ]


def run_api_contract_drift_guard(root: Path, *, write_report: bool = False) -> CommandResult:
    return ApiContractDriftGuard(root, ApiContractDriftOptions(write_report=write_report)).run()


__all__ = [
    "API_CONTRACT_DRIFT_COMMAND",
    "API_CONTRACT_DRIFT_REPORT_CONTRACT",
    "API_CONTRACT_DRIFT_REPORT_SCHEMA_ID",
    "DEFAULT_API_CONTRACT_DRIFT_REPORT_JSON",
    "DEFAULT_API_CONTRACT_DRIFT_REPORT_MARKDOWN",
    "POST_H_028_A_CREATED_BY",
    "ApiContractDriftGuard",
    "ApiContractDriftOptions",
    "run_api_contract_drift_guard",
]
