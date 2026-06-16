from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from devpilot_core.application import ApplicationService

from .routers import actions, reports, status, traces, validation
from .security import (
    API_ROUTE_POLICIES,
    DEFAULT_ALLOWED_ORIGINS,
    SECURITY_HEADERS,
    ApiSecurityConfig,
    build_security_error_response,
    evaluate_api_policy,
    extract_request_token,
    is_public_api_path,
    resolve_api_security_config,
    resolve_route_policy,
    validate_api_token,
)

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8787


def _origin_is_allowed(origin: str | None, config: ApiSecurityConfig) -> bool:
    return bool(origin) and (origin in config.allowed_origins)


def _security_json_response(request: Request, payload: dict[str, Any], status_code: int) -> JSONResponse:
    """Return API security errors with enough CORS headers for browser clients.

    The auth/policy middleware is intentionally outside route handlers. When it
    blocks a request before FastAPI reaches the router, Starlette's CORS
    middleware may not decorate the early response. Sprint 70 keeps the Web UI
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
    headers["X-DevPilot-Api-Security"] = "token+cors+policy"
    return JSONResponse(content=payload, status_code=status_code, headers=headers)


def create_app(
    root: str | Path | None = None,
    *,
    api_token: str | None = None,
    allowed_origins: tuple[str, ...] | list[str] | None = None,
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
        version="1.0.0-report-trace-viewer",
        description="Local secured MVP API for DevPilot read-only/dry-run operations, Report Viewer and Trace Viewer. Sprint 70 implementation.",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
    )
    app.state.devpilot_root = resolved_root
    app.state.application_service = ApplicationService(resolved_root, enforce_workspace_paths=True)
    app.state.api_security = security_config

    if security_config.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(security_config.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-DevPilot-Token"],
            expose_headers=["X-DevPilot-Policy", "X-DevPilot-Api-Security"],
            max_age=600,
        )

    @app.middleware("http")
    async def api_security_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        config: ApiSecurityConfig = request.app.state.api_security
        path = request.url.path
        method = request.method.upper()
        if path.startswith("/api/v1/") and not is_public_api_path(path, method=method, config=config):
            token_ok, finding_id = validate_api_token(config, extract_request_token(request.headers))
            if not token_ok:
                payload, status_code = build_security_error_response(
                    status_code=401,
                    message="API token is required for protected local API endpoints." if finding_id == "API_TOKEN_MISSING_BLOCK" else "API token is invalid for protected local API endpoints.",
                    finding_id=finding_id or "API_TOKEN_INVALID_BLOCK",
                    operation="api.token",
                )
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
        response.headers.setdefault("X-DevPilot-Api-Security", "token+cors+policy")
        if hasattr(request.state, "devpilot_policy"):
            response.headers.setdefault("X-DevPilot-Policy", "allowed")
        return response

    app.include_router(status.router)
    app.include_router(validation.router)
    app.include_router(actions.router)
    app.include_router(reports.router)
    app.include_router(traces.router)

    @app.get("/api/v1/health", tags=["status"])
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "service": "devpilot-local-api",
            "sprint": "FUNC-SPRINT-70",
            "api_implemented": True,
            "api_security_implemented": True,
            "host_default": DEFAULT_API_HOST,
            "dry_run_default": True,
            "token_required": True,
            "cors_wildcard_enabled": False,
            "external_api_required": False,
            "report_viewer_implemented": True,
            "trace_viewer_implemented": True,
        }

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
