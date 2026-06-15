from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from devpilot_core.application import ApplicationService

from .routers import actions, status, validation

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8787


def create_app(root: str | Path | None = None) -> FastAPI:
    """Create the local FastAPI app for FUNC-SPRINT-67.

    The app is intentionally thin: it owns transport concerns only and delegates
    every DevPilot operation to ApplicationService. Token/CORS hardening is not
    implemented here because it is the explicit scope of FUNC-SPRINT-68.
    """

    resolved_root = Path(root or Path.cwd()).resolve()
    app = FastAPI(
        title="DevPilot Local API",
        version="1.0.0-implemented-initial",
        description="Local MVP API for DevPilot read-only/dry-run operations. Sprint 67 implementation.",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
    )
    app.state.devpilot_root = resolved_root
    app.state.application_service = ApplicationService(resolved_root, enforce_workspace_paths=True)

    app.include_router(status.router)
    app.include_router(validation.router)
    app.include_router(actions.router)

    @app.get("/api/v1/health", tags=["status"])
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "service": "devpilot-local-api",
            "sprint": "FUNC-SPRINT-67",
            "api_implemented": True,
            "host_default": DEFAULT_API_HOST,
            "dry_run_default": True,
            "external_api_required": False,
        }

    return app


def _collect_route_paths_from_route_tree(route_items: object, *, prefix: str, seen: set[int]) -> set[str]:
    """Collect paths from Starlette/FastAPI route-like objects defensively.

    FastAPI and Starlette have changed internal route containers across patch
    releases. Some versions flatten APIRoute instances directly into
    ``app.routes``; others can expose helper/router wrapper objects. This
    function intentionally avoids depending on one internal class and instead
    walks common route containers by duck-typing.
    """

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
    """Return stable API route paths from a FastAPI application.

    FastAPI/Starlette internals are not part of DevPilot's public contract.
    Recent releases can expose non-HTTP helper objects, while newer releases
    may keep included routers behind wrapper objects. DevPilot needs stable
    paths for CLI dry-run summaries and contract tests, so this helper combines
    two safe sources:

    1. the generated OpenAPI path map, which FastAPI keeps as the semantic HTTP
       contract for application routes;
    2. a defensive recursive route-tree walk, which also captures local docs and
       OpenAPI utility routes such as ``/api/v1/docs``.
    """

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
