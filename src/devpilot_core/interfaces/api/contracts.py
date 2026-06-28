from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
from typing import Any, Iterable

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.schemas import SchemaValidator

API_ROUTE_CONTRACT_REGISTRY_SCHEMA = "ApiRouteContractRegistry"
DEFAULT_API_ROUTE_CONTRACT_REGISTRY = Path(".devpilot/interfaces/api_route_contract_registry.json")
APP_PUBLIC_TRANSPORT_ROUTE_KEYS = frozenset(
    {
        "GET /api/v1/openapi.json",
        "GET /api/v1/docs",
        "GET /api/v1/health",
    }
)
CANONICAL_FASTAPI_ROUTER_MODULES = (
    "devpilot_core.interfaces.api.routers.status",
    "devpilot_core.interfaces.api.routers.validation",
    "devpilot_core.interfaces.api.routers.actions",
    "devpilot_core.interfaces.api.routers.approvals",
    "devpilot_core.interfaces.api.routers.reports",
    "devpilot_core.interfaces.api.routers.traces",
    "devpilot_core.interfaces.api.routers.settings",
    "devpilot_core.interfaces.api.routers.security_posture",
)
ALLOWED_API_CONTRACT_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


def collect_api_route_keys_from_route_items(route_items: Iterable[object] | object) -> set[str]:
    """Collect `METHOD /api/v1/path` keys from FastAPI/Starlette route-like objects.

    This helper is intentionally small and defensive. POST-H-014-A validates a
    route contract registry without starting a server or invoking HTTP handlers,
    so it only relies on route metadata already registered in APIRouter/FastAPI
    objects. HEAD and OPTIONS are transport details and are not contractual API
    operations for this registry.
    """

    keys: set[str] = set()
    seen: set[int] = set()
    for route in _iter_route_like_items(route_items, seen=seen):
        path = getattr(route, "path", None)
        if not isinstance(path, str) or not path.startswith("/api/v1/"):
            continue
        for method in getattr(route, "methods", set()) or set():
            method = str(method).upper()
            if method in ALLOWED_API_CONTRACT_METHODS:
                keys.add(f"{method} {path}")
    return keys


def collect_canonical_api_route_keys() -> set[str]:
    """Return the canonical POST-H-014-A API route inventory.

    The registry is contractually tied to the router modules plus the app-level
    public transport routes (`openapi`, `docs`, `health`). Relying only on
    `create_app().routes` made the test brittle in Windows environments where a
    stale bytecode/cache/runtime assembly exposed only the public app routes even
    though the router modules were present under `src/`. This function validates
    the source-of-truth router inventory directly and leaves runtime app assembly
    as a diagnostic warning in the validator.
    """

    keys = set(APP_PUBLIC_TRANSPORT_ROUTE_KEYS)
    for module_name in CANONICAL_FASTAPI_ROUTER_MODULES:
        module = importlib.import_module(module_name)
        router = getattr(module, "router", None)
        if router is not None:
            keys.update(collect_api_route_keys_from_route_items(getattr(router, "routes", [])))
    return keys


def _iter_route_like_items(route_items: Iterable[object] | object, *, seen: set[int]) -> Iterable[object]:
    if route_items is None:
        return
    try:
        iterator = iter(route_items)  # type: ignore[arg-type]
    except TypeError:
        iterator = iter([route_items])

    for route in iterator:
        route_identity = id(route)
        if route_identity in seen:
            continue
        seen.add(route_identity)
        yield route

        nested_routes = getattr(route, "routes", None)
        if nested_routes is not None:
            yield from _iter_route_like_items(nested_routes, seen=seen)

        nested_router = getattr(route, "router", None)
        router_routes = getattr(nested_router, "routes", None) if nested_router is not None else None
        if router_routes is not None:
            yield from _iter_route_like_items(router_routes, seen=seen)

        nested_app = getattr(route, "app", None)
        app_routes = getattr(nested_app, "routes", None) if nested_app is not None else None
        if app_routes is not None:
            yield from _iter_route_like_items(app_routes, seen=seen)


@dataclass(frozen=True)
class ApiRouteContractValidationOptions:
    """Options for POST-H-014-A API route contract validation.

    The validator is deliberately read-only. It validates local JSON contracts,
    compares them against the canonical FastAPI router inventory and enforces
    no-go flags. It does not start a server, bind sockets, call the network,
    write reports or execute any API operation.
    """

    registry_path: Path = DEFAULT_API_ROUTE_CONTRACT_REGISTRY
    include_public_transport_routes: bool = True
    runtime_app_route_tree_diagnostic: bool = True


class ApiRouteContractRegistryValidator:
    """Validate the local FastAPI route registry introduced by POST-H-014-A."""

    def __init__(self, root: Path, *, options: ApiRouteContractValidationOptions | None = None) -> None:
        self.root = Path(root).resolve()
        self.options = options or ApiRouteContractValidationOptions()

    @property
    def registry_path(self) -> Path:
        path = Path(self.options.registry_path)
        return path if path.is_absolute() else self.root / path

    def validate(self) -> CommandResult:
        findings: list[Finding] = []
        summary: dict[str, Any] = {
            "registry_path": self._display(self.registry_path),
            "schema": API_ROUTE_CONTRACT_REGISTRY_SCHEMA,
            "routes_total": 0,
            "registered_route_keys_total": 0,
            "fastapi_route_keys_total": 0,
            "canonical_router_route_keys_total": 0,
            "runtime_app_route_keys_total": 0,
            "runtime_app_missing_canonical_routes_total": 0,
            "runtime_app_extra_routes_total": 0,
            "unregistered_routes_total": 0,
            "stale_registry_routes_total": 0,
            "duplicate_route_ids_total": 0,
            "duplicate_method_path_total": 0,
            "mutating_routes_total": 0,
            "mutating_routes_with_justification_total": 0,
            "remote_execution_allowed_total": 0,
            "connector_write_allowed_total": 0,
            "plugin_execution_allowed_total": 0,
            "sensitive_routes_missing_auth_or_policy_total": 0,
            "application_service_routes_total": 0,
            "public_routes_total": 0,
            "read_only": True,
            "dry_run": True,
            "network_used": False,
            "external_api_used": False,
            "mutations_performed": False,
            "source_mutations_performed": False,
            "preliminary": True,
        }
        payload: dict[str, Any] = {}

        if not self.registry_path.exists():
            findings.append(Finding("API_ROUTE_CONTRACT_REGISTRY_MISSING", "API route contract registry is missing.", Severity.BLOCK, path=self._relative(self.registry_path)))
            return self._result(False, findings, summary, payload)

        try:
            import json

            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(Finding("API_ROUTE_CONTRACT_REGISTRY_INVALID_JSON", f"API route contract registry is not valid JSON: {exc}", Severity.ERROR, path=self._relative(self.registry_path)))
            return self._result(False, findings, summary, payload)

        schema_result = SchemaValidator(self.root).validate(schema=API_ROUTE_CONTRACT_REGISTRY_SCHEMA, instance=self._relative(self.registry_path))
        findings.extend(schema_result.findings)

        routes = payload.get("routes", []) if isinstance(payload, dict) else []
        if not isinstance(routes, list):
            routes = []
        summary["routes_total"] = len(routes)

        route_ids = [str(item.get("route_id", "")) for item in routes if isinstance(item, dict)]
        keys = [self._route_key(item) for item in routes if isinstance(item, dict)]
        duplicate_route_ids = sorted({route_id for route_id in route_ids if route_ids.count(route_id) > 1 and route_id})
        duplicate_keys = sorted({key for key in keys if keys.count(key) > 1 and key})
        summary["duplicate_route_ids_total"] = len(duplicate_route_ids)
        summary["duplicate_method_path_total"] = len(duplicate_keys)
        for route_id in duplicate_route_ids:
            findings.append(Finding("API_ROUTE_CONTRACT_DUPLICATE_ID", f"Duplicate API route_id detected: {route_id}", Severity.BLOCK, metadata={"route_id": route_id}))
        for key in duplicate_keys:
            findings.append(Finding("API_ROUTE_CONTRACT_DUPLICATE_METHOD_PATH", f"Duplicate API route method/path contract detected: {key}", Severity.BLOCK, metadata={"route_key": key}))

        registered_keys = {key for key in keys if key}
        summary["registered_route_keys_total"] = len(registered_keys)
        fastapi_keys = self._collect_fastapi_route_keys()
        summary["fastapi_route_keys_total"] = len(fastapi_keys)
        summary["canonical_router_route_keys_total"] = len(fastapi_keys)
        unregistered = sorted(fastapi_keys - registered_keys)
        stale = sorted(registered_keys - fastapi_keys)
        summary["unregistered_routes_total"] = len(unregistered)
        summary["stale_registry_routes_total"] = len(stale)
        for key in unregistered:
            findings.append(Finding("API_ROUTE_NOT_REGISTERED_BLOCK", f"FastAPI route is not registered in API route contract registry: {key}", Severity.BLOCK, metadata={"route_key": key}))
        for key in stale:
            findings.append(Finding("API_ROUTE_CONTRACT_STALE_BLOCK", f"Registry route is not present in FastAPI router inventory: {key}", Severity.BLOCK, metadata={"route_key": key}))

        if self.options.runtime_app_route_tree_diagnostic:
            runtime_keys = self._collect_runtime_app_route_keys()
            runtime_missing = sorted(fastapi_keys - runtime_keys)
            runtime_extra = sorted(runtime_keys - fastapi_keys)
            summary["runtime_app_route_keys_total"] = len(runtime_keys)
            summary["runtime_app_missing_canonical_routes_total"] = len(runtime_missing)
            summary["runtime_app_extra_routes_total"] = len(runtime_extra)
            if runtime_missing:
                findings.append(
                    Finding(
                        "API_ROUTE_RUNTIME_APP_INCOMPLETE_WARNING",
                        "Runtime FastAPI app route tree is missing canonical router routes; registry validation used router-module inventory to avoid Windows/cache false negatives.",
                        Severity.WARNING,
                        metadata={
                            "missing_total": len(runtime_missing),
                            "sample": runtime_missing[:10],
                        },
                    )
                )
            if runtime_extra:
                findings.append(
                    Finding(
                        "API_ROUTE_RUNTIME_APP_EXTRA_WARNING",
                        "Runtime FastAPI app route tree exposes routes not declared by canonical router inventory.",
                        Severity.WARNING,
                        metadata={
                            "extra_total": len(runtime_extra),
                            "sample": runtime_extra[:10],
                        },
                    )
                )

        for route in [item for item in routes if isinstance(item, dict)]:
            route_id = str(route.get("route_id", ""))
            risk = str(route.get("risk_level", ""))
            auth_required = bool(route.get("auth_required"))
            policy_check_required = bool(route.get("policy_check_required"))
            public = bool(route.get("public"))
            app_required = bool(route.get("application_service_required"))
            mutating = bool(route.get("mutations_allowed"))
            justification = str(route.get("mutation_exception_justification", "")).strip()

            if public:
                summary["public_routes_total"] += 1
            if app_required:
                summary["application_service_routes_total"] += 1
            if mutating:
                summary["mutating_routes_total"] += 1
                if justification:
                    summary["mutating_routes_with_justification_total"] += 1
                else:
                    findings.append(Finding("API_ROUTE_MUTATION_UNJUSTIFIED_BLOCK", "Mutating API route lacks explicit local-state mutation justification.", Severity.BLOCK, metadata={"route_id": route_id, "path": route.get("path")}))
            for field_name, finding_id in (
                ("remote_execution_allowed", "API_ROUTE_REMOTE_EXECUTION_BLOCK"),
                ("connector_write_allowed", "API_ROUTE_CONNECTOR_WRITE_BLOCK"),
                ("plugin_execution_allowed", "API_ROUTE_PLUGIN_EXECUTION_BLOCK"),
            ):
                if bool(route.get(field_name)):
                    summary_key = field_name.replace("allowed", "allowed_total")
                    summary[summary_key] = int(summary.get(summary_key, 0)) + 1
                    findings.append(Finding(finding_id, f"API route enables a no-go capability: {field_name}", Severity.BLOCK, metadata={"route_id": route_id, "path": route.get("path")}))
            if bool(route.get("external_api_allowed")):
                findings.append(Finding("API_ROUTE_EXTERNAL_API_BLOCK", "API route contract enables external API usage.", Severity.BLOCK, metadata={"route_id": route_id, "path": route.get("path")}))
            sensitive = risk in {"medium", "high", "critical"} or mutating
            if sensitive and not public and (not auth_required or not policy_check_required):
                summary["sensitive_routes_missing_auth_or_policy_total"] += 1
                findings.append(Finding("API_ROUTE_SENSITIVE_AUTH_POLICY_BLOCK", "Sensitive API route must require both auth and policy binding.", Severity.BLOCK, metadata={"route_id": route_id, "path": route.get("path"), "risk_level": risk}))
            if app_required and route.get("response_contract") != "ApplicationResponse":
                findings.append(Finding("API_ROUTE_APP_RESPONSE_CONTRACT_BLOCK", "ApplicationService-backed API route must declare ApplicationResponse as response_contract.", Severity.BLOCK, metadata={"route_id": route_id, "path": route.get("path"), "response_contract": route.get("response_contract")}))

        ok = not any(f.severity in {Severity.FAIL, Severity.BLOCK, Severity.ERROR} for f in findings)
        return self._result(ok, findings, summary, payload)

    def _result(self, ok: bool, findings: list[Finding], summary: dict[str, Any], registry: dict[str, Any]) -> CommandResult:
        return CommandResult(
            command="api route-contracts validate",
            ok=ok,
            exit_code=ExitCode.PASS if ok else self._exit_code_from_findings(findings),
            message="API route contract registry passed." if ok else "API route contract registry has blocking findings.",
            data={
                "summary": summary,
                "registry": registry,
                "notes": [
                    "POST-H-014-A validates local FastAPI route inventory against a versioned contract registry.",
                    "The validator is read-only and does not start a server, execute route handlers, call network services or mutate source files.",
                    "The blocking route comparison uses canonical APIRouter modules plus app-level public transport routes; runtime app assembly drift is emitted as a warning diagnostic.",
                    "UI route contracts were added in POST-H-014-C; local API/UI security posture is hardened in POST-H-014-D.",
                ],
            },
            findings=findings or [Finding("API_ROUTE_CONTRACT_REGISTRY_PASS", "API route contract registry matches FastAPI app routes and no-go flags.", Severity.INFO, metadata=summary)],
        )

    def _collect_fastapi_route_keys(self) -> set[str]:
        return collect_canonical_api_route_keys()

    def _collect_runtime_app_route_keys(self) -> set[str]:
        try:
            from devpilot_core.interfaces.api.app import create_app

            app = create_app(self.root)
            return collect_api_route_keys_from_route_items(getattr(app, "routes", []))
        except Exception as exc:
            return set()

    @staticmethod
    def _route_key(route: dict[str, Any]) -> str:
        method = str(route.get("method", "")).upper().strip()
        path = str(route.get("path", "")).strip()
        return f"{method} {path}" if method and path else ""

    def _relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(path).replace("\\", "/")

    @staticmethod
    def _display(path: Path) -> str:
        return str(path).replace("\\", "/")

    @staticmethod
    def _exit_code_from_findings(findings: list[Finding]) -> ExitCode:
        severities = {finding.severity for finding in findings}
        if Severity.ERROR in severities:
            return ExitCode.ERROR
        if Severity.BLOCK in severities:
            return ExitCode.BLOCK
        if Severity.FAIL in severities:
            return ExitCode.FAIL
        return ExitCode.PASS
