from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_TARGET_NODEIDS: set[str] = set()
_TARGET_FILES: set[str] = set()
_ROOT: Path | None = None


def _normalize_nodeid(value: str) -> str:
    path_part, sep, suffix = str(value).partition("::")
    normalized = path_part.replace("\\", "/")
    return normalized + (sep + suffix if sep else "")


def pytest_configure(config: Any) -> None:
    global _TARGET_NODEIDS, _TARGET_FILES, _ROOT
    manifest = os.environ.get("DEVPILOT_FULL_SESSION_NODEID_MANIFEST")
    if not manifest:
        raise RuntimeError("DEVPILOT_FULL_SESSION_NODEID_MANIFEST is required")
    payload = json.loads(Path(manifest).read_text(encoding="utf-8"))
    nodeids = payload.get("nodeids") if isinstance(payload, dict) else None
    if not isinstance(nodeids, list) or not nodeids:
        raise RuntimeError("nodeid manifest must contain a non-empty nodeids list")
    normalized = [_normalize_nodeid(str(item)) for item in nodeids]
    if len(normalized) != len(set(normalized)):
        raise RuntimeError("nodeid manifest contains duplicate nodeids")
    _TARGET_NODEIDS = set(normalized)
    _TARGET_FILES = {item.partition("::")[0] for item in normalized}
    _ROOT = Path(str(config.rootpath)).resolve()


def pytest_ignore_collect(collection_path: Any, config: Any) -> bool | None:
    if not _TARGET_FILES or _ROOT is None:
        return None
    path = Path(str(collection_path)).resolve()
    try:
        relative = path.relative_to(_ROOT).as_posix()
    except ValueError:
        return None
    if relative.startswith("tests/") and path.suffix == ".py" and path.name.startswith("test_"):
        return relative not in _TARGET_FILES
    return None


def pytest_collection_modifyitems(config: Any, items: list[Any]) -> None:
    if not _TARGET_NODEIDS:
        return
    selected = []
    deselected = []
    for item in items:
        normalized = _normalize_nodeid(item.nodeid)
        if normalized in _TARGET_NODEIDS:
            selected.append(item)
        else:
            deselected.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = selected
    observed = {_normalize_nodeid(item.nodeid) for item in selected}
    missing = sorted(_TARGET_NODEIDS - observed)
    if missing:
        raise RuntimeError(f"nodeid manifest selection missing {len(missing)} nodeids; first={missing[0]}")
