from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devpilot_core.architecture.models import OwnershipEntry

DEFAULT_OWNERSHIP_REGISTRY = Path(".devpilot/architecture/ownership_registry.json")


def load_ownership_registry(root: Path, path: str | Path = DEFAULT_OWNERSHIP_REGISTRY) -> dict[str, Any]:
    """Load the local POST-H-005 ownership registry.

    The function is intentionally read-only and does not attempt to repair or
    generate missing ownership. Later POST-H-005-E validation can wrap this in a
    CommandResult, but POST-H-005-A keeps the helper minimal and deterministic.
    """

    registry_path = Path(root) / Path(path)
    return json.loads(registry_path.read_text(encoding="utf-8"))


def ownership_entries_from_payload(payload: dict[str, Any]) -> list[OwnershipEntry]:
    packages = payload.get("packages", [])
    if not isinstance(packages, list):
        raise ValueError("ownership registry must contain a packages list")
    return [
        OwnershipEntry(
            package=str(item["package"]),
            domain=str(item["domain"]),
            owner=str(item["owner"]),
            criticality=str(item["criticality"]),
            risk_level=str(item["risk_level"]),
            allowed_dependencies=tuple(item.get("allowed_dependencies", [])),
            restricted_dependencies=tuple(item.get("restricted_dependencies", [])),
            forbidden_dependencies=tuple(item.get("forbidden_dependencies", [])),
            test_contracts=tuple(item.get("test_contracts", [])),
            notes=str(item.get("notes", "")),
            preliminary=bool(item.get("preliminary", True)),
        )
        for item in packages
        if isinstance(item, dict)
    ]
