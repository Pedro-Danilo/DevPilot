from __future__ import annotations

import os
import secrets
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

from .response_mapping import api_error_response

API_TOKEN_ENV_VAR = "DEVPILOT_API_TOKEN"
API_TOKEN_HEADER = "X-DevPilot-Token"
AUTHORIZATION_HEADER = "Authorization"
API_REMOTE_BIND_OVERRIDE_ENV_VAR = "DEVPILOT_API_ALLOW_NON_LOCALHOST"
LOCAL_API_ALLOWED_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")
SECURITY_POSTURE_ROUTE = "/api/v1/security/posture"
DEFAULT_ALLOWED_ORIGINS: tuple[str, ...] = (
    "http://127.0.0.1:8787",
    "http://localhost:8787",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)
PUBLIC_API_PATHS: tuple[str, ...] = (
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/openapi.json",
)
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "X-Permitted-Cross-Domain-Policies": "none",
}


@dataclass(frozen=True)
class ApiSecurityConfig:
    """Runtime security settings for the local API MVP.

    The token is intentionally held in memory only. It is not persisted and must
    not be written to normal command reports or logs. `api token` can generate a
    value for a user to place in the DEVPILOT_API_TOKEN environment variable.
    """

    token: str
    token_source: str
    allowed_origins: tuple[str, ...] = DEFAULT_ALLOWED_ORIGINS
    public_paths: tuple[str, ...] = PUBLIC_API_PATHS
    token_required: bool = True
    cors_enabled: bool = True
    policy_binding_enabled: bool = True
    non_local_bind_allowed: bool = False
    remote_bind_override_env_var: str = API_REMOTE_BIND_OVERRIDE_ENV_VAR
    remote_bind_override_status: str = "disabled"
    security_posture_endpoint: str = SECURITY_POSTURE_ROUTE
    settings_secrets_redacted: bool = True
    secrets_in_api_responses_allowed: bool = False

    @property
    def wildcard_cors_enabled(self) -> bool:
        return "*" in self.allowed_origins

    def to_safe_summary(self) -> dict[str, Any]:
        return {
            "token_required": self.token_required,
            "token_source": self.token_source,
            "token_redacted": redact_token(self.token),
            "cors_enabled": self.cors_enabled,
            "cors_wildcard_enabled": self.wildcard_cors_enabled,
            "allowed_origins": list(self.allowed_origins),
            "public_paths": list(self.public_paths),
            "policy_binding_enabled": self.policy_binding_enabled,
            "non_local_bind_allowed": self.non_local_bind_allowed,
            "remote_bind_override_env_var": self.remote_bind_override_env_var,
            "remote_bind_override_status": self.remote_bind_override_status,
            "security_posture_endpoint": self.security_posture_endpoint,
            "settings_secrets_redacted": self.settings_secrets_redacted,
            "secrets_in_api_responses_allowed": self.secrets_in_api_responses_allowed,
            "token_env_var": API_TOKEN_ENV_VAR,
            "preliminary": True,
        }


@dataclass(frozen=True)
class ApiRoutePolicy:
    operation: str
    action: str
    sensitivity: str = "protected"
    path_subject: str | None = None
    external_api: bool = False


API_ROUTE_POLICIES: dict[tuple[str, str], ApiRoutePolicy] = {
    ("GET", "/api/v1/workspace/status"): ApiRoutePolicy("workspace.status", "read", "protected-read"),
    ("GET", "/api/v1/application/contract"): ApiRoutePolicy("app.contract", "read", "protected-read"),
    ("GET", "/api/v1/miasi/status"): ApiRoutePolicy("miasi.validate", "read", "protected-read"),
    ("GET", "/api/v1/standards/status"): ApiRoutePolicy("standards.status", "read", "protected-read"),
    ("GET", "/api/v1/model/providers"): ApiRoutePolicy("model.providers", "read", "protected-read"),
    ("GET", "/api/v1/repo/inventory"): ApiRoutePolicy("repo.inventory", "read", "protected-read"),
    ("GET", "/api/v1/reports"): ApiRoutePolicy("reports.list", "read", "protected-read", path_subject="outputs/reports"),
    ("GET", "/api/v1/reports/{report_id}"): ApiRoutePolicy("reports.read", "read", "protected-read", path_subject="outputs/reports"),
    ("GET", "/api/v1/observability/traces"): ApiRoutePolicy("observability.trace_report", "read", "protected-read"),
    ("GET", "/api/v1/observability/metrics"): ApiRoutePolicy("observability.metrics_summary", "read", "protected-read"),
    ("GET", "/api/v1/traces"): ApiRoutePolicy("observability.trace_report", "read", "protected-read", path_subject=".devpilot/devpilot.db"),
    ("GET", "/api/v1/traces/{trace_id}"): ApiRoutePolicy("observability.trace_inspect", "read", "protected-read", path_subject=".devpilot/devpilot.db"),
    ("GET", "/api/v1/metrics/summary"): ApiRoutePolicy("observability.metrics_summary", "read", "protected-read", path_subject=".devpilot/devpilot.db"),
    ("GET", "/api/v1/history/runs"): ApiRoutePolicy("history.runs", "read", "protected-read"),
    ("GET", "/api/v1/security/posture"): ApiRoutePolicy("api.security.posture", "read", "protected-security"),
    ("POST", "/api/v1/validation/frontmatter"): ApiRoutePolicy("validation.frontmatter", "read", "protected-validation"),
    ("POST", "/api/v1/validation/artifact"): ApiRoutePolicy("validation.artifact", "read", "protected-validation"),
    ("POST", "/api/v1/validation/readiness"): ApiRoutePolicy("validation.readiness", "read", "protected-validation"),
    ("POST", "/api/v1/review/code"): ApiRoutePolicy("review.code", "read", "protected-dry-run"),
    ("POST", "/api/v1/refactor/plan"): ApiRoutePolicy("refactor.plan", "read", "protected-plan-only"),
    ("GET", "/api/v1/approvals"): ApiRoutePolicy("approvals.list", "approval", "protected-approval", path_subject=".devpilot/devpilot.db"),
    ("GET", "/api/v1/approvals/{approval_id}"): ApiRoutePolicy("approvals.show", "approval", "protected-approval", path_subject=".devpilot/devpilot.db"),
    ("POST", "/api/v1/approvals/request"): ApiRoutePolicy("approvals.request", "approval", "protected-approval-write", path_subject=".devpilot/devpilot.db"),
    ("POST", "/api/v1/approvals/{approval_id}/approve"): ApiRoutePolicy("approvals.approve", "approval", "protected-approval-write", path_subject=".devpilot/devpilot.db"),
    ("POST", "/api/v1/approvals/{approval_id}/deny"): ApiRoutePolicy("approvals.deny", "approval", "protected-approval-write", path_subject=".devpilot/devpilot.db"),
    ("POST", "/api/v1/actions/dry-run"): ApiRoutePolicy("ui.actions.dry_run", "read", "protected-dry-run"),
    ("GET", "/api/v1/settings/workspace"): ApiRoutePolicy("settings.workspace", "read", "protected-settings-read", path_subject=".devpilot/project.yaml"),
    ("GET", "/api/v1/settings/providers"): ApiRoutePolicy("settings.providers", "read", "protected-settings-read", path_subject=".devpilot/providers.yaml"),
    ("GET", "/api/v1/settings/policy"): ApiRoutePolicy("settings.policy", "read", "protected-settings-read", path_subject=".devpilot/policy.yaml"),
    ("POST", "/api/v1/settings/providers/plan"): ApiRoutePolicy("settings.providers.plan", "read", "protected-settings-plan", path_subject=".devpilot/providers.yaml"),
    ("GET", "/api/v1/operator/dashboard"): ApiRoutePolicy("operator.dashboard", "read", "protected-operator-dashboard", path_subject=".devpilot/operator/dashboard_config.json"),
    ("GET", "/api/v1/portfolio/status"): ApiRoutePolicy("portfolio.status", "read", "protected-portfolio-status", path_subject=".devpilot/workspaces/workspace_registry.json"),
}


def generate_api_token(*, nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def redact_token(token: str | None) -> str:
    if not token:
        return "<unset>"
    if len(token) <= 12:
        return "<redacted>"
    return f"{token[:4]}...{token[-4:]}"


def _normalized_local_host(value: str) -> str:
    host = str(value or "").strip().lower()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    return host


def is_local_api_host(host: str) -> bool:
    """Return whether an API bind host is allowed for the local-only shell."""

    return _normalized_local_host(host) in set(LOCAL_API_ALLOWED_HOSTS)


def is_allowed_local_origin(origin: str) -> bool:
    """Return whether a browser origin is allowed by the local CORS policy."""

    if not origin or origin == "*":
        return False
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"}:
        return False
    return is_local_api_host(parsed.hostname or "")


def sanitize_allowed_origins(origins: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    """Keep only explicit localhost/loopback origins; wildcard CORS is never accepted."""

    candidates = tuple(origins) if origins is not None else DEFAULT_ALLOWED_ORIGINS
    sanitized = tuple(origin for origin in candidates if is_allowed_local_origin(str(origin)))
    return sanitized or DEFAULT_ALLOWED_ORIGINS


def remote_bind_override_state(env: dict[str, str] | None = None) -> dict[str, Any]:
    """Describe the future non-local bind override without enabling it."""

    effective_env = env if env is not None else os.environ
    requested = bool(str(effective_env.get(API_REMOTE_BIND_OVERRIDE_ENV_VAR, "")).strip())
    return {
        "remote_bind_override_env_var": API_REMOTE_BIND_OVERRIDE_ENV_VAR,
        "remote_bind_override_requested": requested,
        "remote_bind_override_enabled": False,
        "remote_bind_override_status": "future_disabled_by_design",
    }


def validate_api_bind_host(*, host: str, port: int, env: dict[str, str] | None = None) -> CommandResult:
    """Validate that the local API is not bound to a non-local interface."""

    override = remote_bind_override_state(env)
    summary = {
        "host": host,
        "port": port,
        "allowed_hosts": sorted(LOCAL_API_ALLOWED_HOSTS),
        "server_started": False,
        "api_implemented": True,
        "api_security_implemented": True,
        "local_bind_required": True,
        "non_local_bind_allowed": False,
        "created_by": "POST-H-014-D",
        **override,
    }
    if is_local_api_host(host):
        return CommandResult(
            command="api serve host validation",
            ok=True,
            exit_code=ExitCode.PASS,
            message="API host is local and allowed.",
            data={"summary": summary},
            findings=[Finding("API_LOCAL_BIND_ALLOWED", "API host is restricted to localhost/loopback.", Severity.INFO, metadata={"host": host})],
        )
    return CommandResult(
        command="api serve",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message="Secured API local shell refuses non-local bind hosts.",
        data={"summary": summary},
        findings=[
            Finding(
                id="API_HOST_NOT_LOCALHOST_BLOCK",
                message="Refusing to bind secured local API to a non-localhost host. Non-local override remains future-disabled by design.",
                severity=Severity.BLOCK,
                metadata={"host": host, **override},
            )
        ],
    )


def resolve_api_security_config(
    *,
    token: str | None = None,
    allowed_origins: tuple[str, ...] | list[str] | None = None,
    env: dict[str, str] | None = None,
) -> ApiSecurityConfig:
    effective_env = env if env is not None else os.environ
    if token:
        resolved_token = token
        source = "explicit"
    elif effective_env.get(API_TOKEN_ENV_VAR):
        resolved_token = str(effective_env[API_TOKEN_ENV_VAR])
        source = "env"
    else:
        resolved_token = generate_api_token()
        source = "generated-ephemeral"

    origins = sanitize_allowed_origins(allowed_origins)
    return ApiSecurityConfig(token=resolved_token, token_source=source, allowed_origins=origins)


def extract_bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    prefix = "Bearer "
    if value.startswith(prefix):
        return value[len(prefix) :].strip()
    return None


def extract_request_token(headers: Any) -> str | None:
    header_value = headers.get(API_TOKEN_HEADER) if headers is not None else None
    if header_value:
        return str(header_value)
    return extract_bearer_token(headers.get(AUTHORIZATION_HEADER) if headers is not None else None)


def is_public_api_path(path: str, *, method: str = "GET", config: ApiSecurityConfig | None = None) -> bool:
    if method.upper() == "OPTIONS":
        return True
    public_paths = (config.public_paths if config else PUBLIC_API_PATHS)
    return path in public_paths


def build_security_error_response(*, status_code: int, message: str, finding_id: str, operation: str = "api.security") -> tuple[dict[str, Any], int]:
    return api_error_response(
        operation=operation,
        message=message,
        finding_id=finding_id,
        severity=Severity.BLOCK,
        status_hint=status_code,
        metadata={"token_redacted": True},
    )


def validate_api_token(config: ApiSecurityConfig, supplied_token: str | None) -> tuple[bool, str | None]:
    if not config.token_required:
        return True, None
    if not supplied_token:
        return False, "API_TOKEN_MISSING_BLOCK"
    if not secrets.compare_digest(config.token, supplied_token):
        return False, "API_TOKEN_INVALID_BLOCK"
    return True, None


def evaluate_api_policy(root: Path, route_policy: ApiRoutePolicy) -> CommandResult:
    return PolicyEngine(root).evaluate(
        PolicyRequest(
            action=route_policy.action,
            path=route_policy.path_subject,
            external_api=route_policy.external_api,
            dry_run=True,
            metadata={
                "component": "LocalAPI",
                "api_operation": route_policy.operation,
                "api_sensitivity": route_policy.sensitivity,
                "policy_binding": True,
            },
            subject=route_policy.operation,
        )
    )



def api_security_posture_summary(*, root: Path, config: ApiSecurityConfig, routes_total: int, policy_bound_routes_total: int) -> dict[str, Any]:
    """Return a redacted local API/UI security posture summary for operators."""

    return {
        **config.to_safe_summary(),
        "created_by": "POST-H-014-D",
        "root": str(root),
        "routes_total": routes_total,
        "policy_bound_routes_total": policy_bound_routes_total,
        "security_headers_total": len(SECURITY_HEADERS),
        "security_headers": sorted(SECURITY_HEADERS),
        "local_bind_required": True,
        "allowed_bind_hosts": sorted(LOCAL_API_ALLOWED_HOSTS),
        "non_local_bind_allowed": False,
        "remote_execution_enabled": False,
        "connector_write_enabled": False,
        "plugin_execution_enabled": False,
        "external_api_used": False,
        "network_used": False,
        "settings_secrets_redacted": True,
        "raw_secret_values_redacted": True,
        "stack_traces_redacted": True,
        "preliminary": True,
        **remote_bind_override_state(),
    }


def resolve_route_policy(method: str, path: str) -> ApiRoutePolicy | None:
    """Return route policy for exact or templated API path."""

    normalized = (method.upper(), path)
    if normalized in API_ROUTE_POLICIES:
        return API_ROUTE_POLICIES[normalized]
    if method.upper() == "GET":
        if path.startswith("/api/v1/approvals/") and path.count("/") == 4:
            return API_ROUTE_POLICIES.get(("GET", "/api/v1/approvals/{approval_id}"))
        if path.startswith("/api/v1/reports/") and path.count("/") == 4:
            return API_ROUTE_POLICIES.get(("GET", "/api/v1/reports/{report_id}"))
        if path.startswith("/api/v1/traces/") and path.count("/") == 4:
            return API_ROUTE_POLICIES.get(("GET", "/api/v1/traces/{trace_id}"))
    if method.upper() == "POST" and path.startswith("/api/v1/approvals/"):
        if path.endswith("/approve") and path.count("/") == 5:
            return API_ROUTE_POLICIES.get(("POST", "/api/v1/approvals/{approval_id}/approve"))
        if path.endswith("/deny") and path.count("/") == 5:
            return API_ROUTE_POLICIES.get(("POST", "/api/v1/approvals/{approval_id}/deny"))
    return None
