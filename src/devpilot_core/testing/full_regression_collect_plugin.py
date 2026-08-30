from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _normalize_nodeid_path_only(nodeid: str) -> str:
    path_part, sep, suffix = str(nodeid).partition("::")
    normalized_path = path_part.replace("\\", "/")
    return normalized_path + (sep + suffix if sep else "")


def pytest_collection_finish(session: Any) -> None:
    target = os.environ.get("DEVPILOT_FULL_SESSION_COLLECTION")
    if not target:
        return
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [_normalize_nodeid_path_only(item.nodeid) for item in session.items]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
