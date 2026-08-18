from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from devpilot_core.application import ApplicationResponse, ApplicationService, AuthApplicationService
from devpilot_core.cli_models import CommandResult, ExitCode

from .response_mapping import http_exception_response, unhandled_exception_response, validation_error_response
from .uoc011_hardening import FixedWindowRateLimiter, UOC011_API_HARDENING_HEADERS, Uoc011ApiHardeningConfig, inspect_request_hardening
from .routers import actions, ai, approvals, auth, guided_sdlc, jobs, operator, portfolio, project_entry, quality, reports, security_posture, settings, status, traces, validation, workspace_documents, workspace_edits, workspace_git, workspace_validations
from .security import (
    API_ROUTE_POLICIES,
    API_SECURITY_HEADER_VALUE,
    DEFAULT_ALLOWED_ORIGINS,
    SECURITY_HEADERS,
    ApiSecurityConfig,
    build_security_error_response,
    evaluate_api_policy,
    extract_request_token,
    human_session_required_path,
    is_public_api_path,
    resolve_api_security_config,
    resolve_route_policy,
    validate_api_token,
)
from devpilot_core.identity.auth_models import CSRF_HEADER_NAME, SESSION_COOKIE_NAME
from devpilot_core.identity.session_service import CsrfInvalid, SessionInvalid

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8787

PUBLIC_AUTH_MUTATION_PATHS: frozenset[str] = frozenset({
    "/api/v1/auth/bootstrap/owner",
    "/api/v1/auth/login",
})



def _origin_is_allowed(origin: str | None, config: ApiSecurityConfig) -> bool:
    return bool(origin) and (origin in config.allowed_origins)


def _security_json_response(request: Request, payload: dict[str, Any], status_code: int) -> JSONResponse:
    """Return API security errors with enough CORS headers for browser clients.

    The auth/policy middleware is intentionally outside route handlers. When it
    blocks a request before FastAPI reaches the router, Starlette's CORS
    middleware may not decorate the early response. Sprint 70/71 keeps the Web UI
    debuggable by adding restricted CORS headers only for allow-listed local
    origins; this prevents browsers from collapsing 401/403 responses into a
    generic `Failed to fetch` network error.
    """

    headers = dict(SECURITY_HEADERS)
    config: ApiSecurityConfig = request.app.state.api_security
    origin = request.headers.get("origin")
    if _origin_is_allowed(origin, config):
        headers["Access-Control-Allow-Origin"] = str(origin)
        headers["Vary"] = "Origin"
        headers["Access-Control-Expose-Headers"] = "X-DevPilot-Policy, X-DevPilot-Api-Security"
    headers["X-DevPilot-Api-Security"] = API_SECURITY_HEADER_VALUE
    return JSONResponse(content=payload, status_code=status_code, headers=headers)


def create_app(
    root: str | Path | None = None,
    *,
    api_token: str | None = None,
    allowed_origins: tuple[str, ...] | list[str] | None = None,
    auth_service: AuthApplicationService | None = None,
) -> FastAPI:
    """Create the local FastAPI app for FUNC-SPRINT-67/68.

    Sprint 67 introduced the local API transport. Sprint 68 adds minimal local
    security controls before the Web UI can depend on it: in-memory token,
    restricted CORS, security headers and PolicyEngine binding for protected
    routes. This is still a local MVP, not enterprise authentication/RBAC.
    """

    resolved_root = Path(root or Path.cwd()).resolve()
    security_config = resolve_api_security_config(token=api_token, allowed_origins=allowed_origins)
    app = FastAPI(
        title="DevPilot Local API",
        version="1.0.0-post-h-014-e",
        description="Local secured API/UI shell for DevPilot visual dashboard, report/trace viewers, Approval Center, Settings UI and security posture diagnostics. POST-H-014-E quality-gated implementation.",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
    )
    app.state.devpilot_root = resolved_root
    app.state.auth_service = auth_service or AuthApplicationService(resolved_root)
    app.state.application_service = ApplicationService(
        resolved_root,
        enforce_workspace_paths=True,
        approval_auth_store=app.state.auth_service.store,
    )
    # UOC-008: reconcile stale/orphan governed jobs at API startup. The result is
    # retained for diagnostics; reconciliation never promotes an orphan to PASS.
    app.state.governed_job_reconciliation = app.state.application_service.jobs_reconcile(stale_after_seconds=120).to_dict()
    app.state.api_security = security_config
    app.state.uoc011_hardening_config = Uoc011ApiHardeningConfig()
    app.state.auth_login_limiter = FixedWindowRateLimiter()
    app.state.uoc011_rate_limiter = FixedWindowRateLimiter()

    def _api_error_json_response(request: Request, payload: dict[str, Any], status_code: int) -> JSONResponse:
        headers = dict(SECURITY_HEADERS)
        origin = request.headers.get("origin")
        if _origin_is_allowed(origin, request.app.state.api_security):
            headers["Access-Control-Allow-Origin"] = str(origin)
            headers["Vary"] = "Origin"
            headers["Access-Control-Expose-Headers"] = "X-DevPilot-Policy, X-DevPilot-Api-Security"
        headers["X-DevPilot-Api-Security"] = API_SECURITY_HEADER_VALUE
        return JSONResponse(content=payload, status_code=status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def api_request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:  # type: ignore[override]
        payload, status_code = validation_error_response(errors_total=len(exc.errors()))
        return _api_error_json_response(request, payload, status_code)

    @app.exception_handler(StarletteHTTPException)
    async def api_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:  # type: ignore[override]
        detail = exc.detail if isinstance(exc.detail, str) else None
        payload, status_code = http_exception_response(operation="api.http", status_code=int(exc.status_code), detail=detail)
        return _api_error_json_response(request, payload, status_code)

    @app.exception_handler(Exception)
    async def api_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
        payload, status_code = unhandled_exception_response(operation="api.unhandled", exc=exc)
        return _api_error_json_response(request, payload, status_code)

    if security_config.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(security_config.allowed_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-DevPilot-Token", "X-DevPilot-CSRF"],
            expose_headers=["X-DevPilot-Policy", "X-DevPilot-Api-Security", "X-DevPilot-RateLimit-Remaining", "X-DevPilot-UOC011-Hardening"],
            max_age=600,
        )

    @app.middleware("http")
    async def api_security_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        config: ApiSecurityConfig = request.app.state.api_security
        path = request.url.path
        method = request.method.upper()
        hardening = await inspect_request_hardening(request, config=request.app.state.uoc011_hardening_config, limiter=request.app.state.uoc011_rate_limiter)
        if not hardening.get("ok", False):
            payload, status_code = build_security_error_response(status_code=int(hardening.get("status_code", 429)), message=str(hardening.get("message", "Local request hardening blocked the request.")), finding_id=str(hardening.get("finding_id", "API_UOC011_HARDENING_BLOCK")), operation="api.uoc011.hardening")
            response = _security_json_response(request, payload, status_code)
            if hardening.get("retry_after") is not None:
                response.headers["Retry-After"] = str(hardening["retry_after"])
            response.headers["X-DevPilot-RateLimit-Remaining"] = str(hardening.get("remaining", 0))
            return response
        if path in PUBLIC_AUTH_MUTATION_PATHS and method == "POST":
            origin = request.headers.get("origin")
            if origin and not _origin_is_allowed(origin, config):
                payload, status_code = build_security_error_response(
                    status_code=403,
                    message="Public local authentication mutation requires an allow-listed local browser origin.",
                    finding_id="AUTH_PUBLIC_ORIGIN_BLOCK",
                    operation="api.auth.origin",
                )
                return _security_json_response(request, payload, status_code)

        if path.startswith("/api/v1/") and not is_public_api_path(path, method=method, config=config):
            human_session = None
            supplied_session = request.cookies.get(SESSION_COOKIE_NAME, "")
            if supplied_session:
                try:
                    human_session = request.app.state.auth_service.resolve(supplied_session)
                    request.state.authenticated_principal = human_session.principal
                    request.state.authenticated_session_context = human_session
                    request.state.auth_method = "human-session"
                except SessionInvalid:
                    human_session = None

            token_ok, finding_id = validate_api_token(config, extract_request_token(request.headers))
            session_required = request.app.state.application_service.rbac.human_session_required(method=method, path=path) or human_session_required_path(path, method)
            if session_required and human_session is None:
                payload, status_code = build_security_error_response(status_code=401, message="Authenticated human session is required for this local API endpoint.", finding_id="AUTH_HUMAN_SESSION_REQUIRED_BLOCK", operation="api.human_session")
                return _security_json_response(request, payload, status_code)
            if human_session is None and not token_ok:
                payload, status_code = build_security_error_response(status_code=401, message="Human session or legacy local API token is required for protected local API endpoints.", finding_id=finding_id or "API_TOKEN_INVALID_BLOCK", operation="api.token")
                return _security_json_response(request, payload, status_code)
            if human_session is not None and method in {"POST","PUT","PATCH","DELETE"}:
                origin = request.headers.get("origin")
                if origin and not _origin_is_allowed(origin, config):
                    payload, status_code = build_security_error_response(status_code=403, message="Browser origin is not allowed for authenticated session mutation.", finding_id="AUTH_ORIGIN_BLOCK", operation="api.csrf")
                    return _security_json_response(request, payload, status_code)
                try:
                    request.app.state.auth_service.require_csrf(supplied_session, request.headers.get(CSRF_HEADER_NAME, ""))
                except (CsrfInvalid, SessionInvalid):
                    payload, status_code = build_security_error_response(status_code=403, message="CSRF validation failed for authenticated session mutation.", finding_id="AUTH_CSRF_BLOCK", operation="api.csrf")
                    return _security_json_response(request, payload, status_code)

            route_policy = resolve_route_policy(method, path)
            if route_policy is None:
                payload, status_code = build_security_error_response(
                    status_code=403,
                    message="API route is not bound to an explicit DevPilot policy.",
                    finding_id="API_POLICY_BINDING_MISSING_BLOCK",
                    operation="api.policy",
                )
                return _security_json_response(request, payload, status_code)

            workspace_id = request.query_params.get("workspace_id") or "devpilot-local"
            if human_session is not None:
                rbac_decision = request.app.state.application_service.rbac.authorize_route(human_session.principal, method=method, path=path, workspace_id=workspace_id)
                request.state.devpilot_rbac = rbac_decision
                if not rbac_decision.allowed:
                    payload, status_code = build_security_error_response(status_code=403, message="Server-side RBAC denied the local API request.", finding_id=rbac_decision.reason_code, operation=rbac_decision.operation)
                    return _security_json_response(request, payload, status_code)
            elif token_ok and not request.app.state.application_service.rbac.legacy_token_allowed(method=method, path=path):
                payload, status_code = build_security_error_response(status_code=403, message="Legacy local API token is not authorized for this RBAC-protected operation.", finding_id="RBAC_LEGACY_TOKEN_DENY", operation="api.rbac")
                return _security_json_response(request, payload, status_code)

            policy_result = evaluate_api_policy(request.app.state.devpilot_root, route_policy)
            if not policy_result.ok:
                payload, status_code = build_security_error_response(
                    status_code=403,
                    message="PolicyEngine blocked the local API request.",
                    finding_id="API_POLICY_BINDING_BLOCK",
                    operation=route_policy.operation,
                )
                return _security_json_response(request, payload, status_code)
            request.state.devpilot_policy = policy_result

        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        for header, value in UOC011_API_HARDENING_HEADERS.items():
            response.headers.setdefault(header, value)
        response.headers.setdefault("X-DevPilot-RateLimit-Remaining", str(hardening.get("remaining", 0)))
        response.headers.setdefault("X-DevPilot-Api-Security", API_SECURITY_HEADER_VALUE)
        if hasattr(request.state, "devpilot_policy"):
            response.headers.setdefault("X-DevPilot-Policy", "allowed")
        return response

    app.include_router(auth.router)
    app.include_router(status.router)
    app.include_router(project_entry.router)
    app.include_router(workspace_documents.router)
    app.include_router(workspace_validations.router)
    app.include_router(workspace_edits.router)
    app.include_router(workspace_git.router)
    app.include_router(jobs.router)
    app.include_router(quality.router)
    app.include_router(ai.router)
    app.include_router(validation.router)
    app.include_router(actions.router)
    app.include_router(approvals.router)
    app.include_router(reports.router)
    app.include_router(traces.router)
    app.include_router(settings.router)
    app.include_router(operator.router)
    app.include_router(portfolio.router)
    app.include_router(security_posture.router)

    @app.get("/api/v1/health", tags=["status"])
    def health() -> dict[str, object]:
        summary = {
            "service": "devpilot-local-api",
            "sprint": "FUNC-SPRINT-72",
            "post_h_014_b_response_mapping": True,
            "post_h_014_c_ui_route_contract": True,
            "post_h_014_d_security_hardening": True,
            "post_h_014_e_quality_gate": True,
            "ui_api_shell_quality_gate": "ui-api-industrial-shell",
            "api_implemented": True,
            "api_security_implemented": True,
            "host_default": DEFAULT_API_HOST,
            "dry_run_default": True,
            "token_required": True,
            "cors_wildcard_enabled": False,
            "external_api_required": False,
            "report_viewer_implemented": True,
            "trace_viewer_implemented": True,
            "approval_center_implemented": True,
            "dry_run_action_launcher_implemented": True,
            "critical_actions_blocked_from_ui": True,
            "settings_ui_implemented": True,
            "settings_provider_editor_plan_only": True,
            "settings_secrets_redacted": True,
            "security_posture_endpoint": "/api/v1/security/posture",
            "portfolio_status_endpoint": "/api/v1/portfolio/status",
            "portfolio_status_read_only": True,
            "non_local_bind_allowed": False,
            "remote_bind_override_status": "future_disabled_by_design",
        }
        result = CommandResult(
            command="api health",
            ok=True,
            exit_code=ExitCode.PASS,
            message="DevPilot local API is healthy.",
            data={"summary": summary},
        )
        payload = ApplicationResponse.from_command_result(result, operation="api.health").to_dict()
        payload.update(summary)  # backward-compatible health fields for existing UI/tests.
        return payload

    app.include_router(guided_sdlc.router)
    return app


def _collect_route_paths_from_route_tree(route_items: object, *, prefix: str, seen: set[int]) -> set[str]:
    """Collect paths from Starlette/FastAPI route-like objects defensively."""

    paths: set[str] = set()
    if route_items is None:
        return paths

    try:
        iterator = iter(route_items)  # type: ignore[arg-type]
    except TypeError:
        iterator = iter([route_items])

    for route in iterator:
        route_id = id(route)
        if route_id in seen:
            continue
        seen.add(route_id)

        path = getattr(route, "path", None)
        if isinstance(path, str) and path.startswith(prefix):
            paths.add(path)

        nested_routes = getattr(route, "routes", None)
        if nested_routes is not None:
            paths.update(_collect_route_paths_from_route_tree(nested_routes, prefix=prefix, seen=seen))

        nested_router = getattr(route, "router", None)
        router_routes = getattr(nested_router, "routes", None) if nested_router is not None else None
        if router_routes is not None:
            paths.update(_collect_route_paths_from_route_tree(router_routes, prefix=prefix, seen=seen))

        nested_app = getattr(route, "app", None)
        app_routes = getattr(nested_app, "routes", None) if nested_app is not None else None
        if app_routes is not None:
            paths.update(_collect_route_paths_from_route_tree(app_routes, prefix=prefix, seen=seen))

    return paths


def api_route_paths(app: FastAPI, *, prefix: str = "/api/v1/") -> list[str]:
    """Return stable API route paths from a FastAPI application."""

    paths: set[str] = set()

    try:
        openapi_paths = getattr(app, "openapi")().get("paths", {})
    except Exception:
        openapi_paths = {}
    if isinstance(openapi_paths, dict):
        for path in openapi_paths:
            if isinstance(path, str) and path.startswith(prefix):
                paths.add(path)

    paths.update(_collect_route_paths_from_route_tree(getattr(app, "routes", []), prefix=prefix, seen=set()))
    return sorted(paths)


def api_security_summary(app: FastAPI) -> dict[str, Any]:
    config: ApiSecurityConfig = app.state.api_security
    protected_routes = [path for path in api_route_paths(app) if path not in config.public_paths]
    return {
        **config.to_safe_summary(),
        "protected_routes_total": len(protected_routes),
        "policy_bound_routes_total": len(API_ROUTE_POLICIES),
        "security_headers": sorted(SECURITY_HEADERS),
    }
