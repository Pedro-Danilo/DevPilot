from __future__ import annotations

from fastapi import Request

from devpilot_core.application import ApplicationService


def get_application_service(request: Request) -> ApplicationService:
    """Return the per-app ApplicationService instance.

    The service is created by create_app(root=...). Keeping this as a dependency
    prevents routers from constructing or importing core modules directly.
    """

    return request.app.state.application_service
