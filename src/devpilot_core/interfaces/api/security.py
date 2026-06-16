from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from devpilot_core.application import ApplicationResponse
from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.policy import PolicyEngine, PolicyRequest

API_TOKEN_ENV_VAR = "DEVPILOT_API_TOKEN"
API_TOKEN_HEADER = "X-DevPilot-Token"
AUTHORIZATION_HEADER = "Authorization"
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
}


def generate_api_token(*, nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def redact_token(token: str | None) -> str:
    if not token:
        return "<unset>"
    if len(token) <= 12:
        return "<redacted>"
    return f"{token[:4]}...{token[-4:]}"


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

    origins = tuple(allowed_origins) if allowed_origins is not None else DEFAULT_ALLOWED_ORIGINS
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
    result = CommandResult(
        command="api security",
        ok=False,
        exit_code=ExitCode.BLOCK,
        message=message,
        data={"summary": {"operation": operation, "status_hint": status_code, "token_redacted": True, "preliminary": True}},
        findings=[Finding(id=finding_id, message=message, severity=Severity.BLOCK, metadata={"operation": operation})],
    )
    return ApplicationResponse.from_command_result(result, operation=operation).to_dict(), status_code


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
