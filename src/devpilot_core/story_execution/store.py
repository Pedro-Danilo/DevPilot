from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import StoryExecutionState


class StoryExecutionStore:
    """Runtime-only atomic store for GSDLC-09-A story execution evidence."""

    def __init__(self, workspace_root: Path, *, workspace_id: str) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in str(workspace_id)).strip("-") or "platform"
        self.root = self.workspace_root / "outputs" / "story_execution" / "gsdlc_09_a" / safe
        self.state_path = self.root / "current_state.json"
        self.context_path = self.root / "story_context_pack.json"
        self.dor_path = self.root / "dor_report.json"

    def save_dor(self, payload: dict[str, Any]) -> None:
        self._atomic(self.dor_path, payload)

    def save_context(self, payload: dict[str, Any]) -> None:
        self._atomic(self.context_path, payload)

    def save_state(self, state: StoryExecutionState) -> dict[str, Any]:
        payload = state.to_dict()
        self._atomic(self.state_path, payload)
        return payload

    def load_state(self) -> StoryExecutionState | None:
        if not self.state_path.exists():
            return None
        return StoryExecutionState.from_dict(json.loads(self.state_path.read_text(encoding="utf-8")))

    def load_context(self) -> dict[str, Any] | None:
        return self._read(self.context_path)

    def load_dor(self) -> dict[str, Any] | None:
        return self._read(self.dor_path)

    def current_story_projection(self) -> dict[str, Any] | None:
        state = self.load_state()
        if state is None:
            return None
        payload = state.to_dict()
        return {
            "execution_id": payload["execution_id"],
            "story_id": payload["story_id"],
            "story_version": payload["story_version"],
            "status": payload["status"],
            "sequence": payload["sequence"],
            "context_pack_sha256": payload["context_pack_sha256"],
            "dor_report_sha256": payload["dor_report_sha256"],
            "state_sha256": payload["state_sha256"],
            "read_only": True,
        }

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _atomic(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        temp.replace(path)
