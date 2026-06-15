"""Local FastAPI adapter for DevPilot Local.

The API is an implemented-initial MVP for FUNC-SPRINT-67. It is local-first,
read-only/dry-run oriented and must remain behind ApplicationService.
"""

from .app import DEFAULT_API_HOST, DEFAULT_API_PORT, api_route_paths, create_app

__all__ = ["DEFAULT_API_HOST", "DEFAULT_API_PORT", "api_route_paths", "create_app"]
