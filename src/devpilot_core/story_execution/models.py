from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any


class StoryExecutionStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    CHANGES_READY = "CHANGES_READY"
    VALIDATING = "VALIDATING"
    COMMIT_READY = "COMMIT_READY"
    DONE = "DONE"


_ALLOWED_TRANSITIONS: dict[StoryExecutionStatus, StoryExecutionStatus] = {
    StoryExecutionStatus.PLANNED: StoryExecutionStatus.IN_PROGRESS,
    StoryExecutionStatus.IN_PROGRESS: StoryExecutionStatus.CHANGES_READY,
    StoryExecutionStatus.CHANGES_READY: StoryExecutionStatus.VALIDATING,
    StoryExecutionStatus.VALIDATING: StoryExecutionStatus.COMMIT_READY,
    StoryExecutionStatus.COMMIT_READY: StoryExecutionStatus.DONE,
}


class StoryExecutionTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class StoryExecutionState:
    execution_id: str
    workspace_id: str
    project_id: str
    story_id: str
    story_version: str
    status: StoryExecutionStatus
    sequence: int
    dor_report_sha256: str
    context_pack_id: str
    context_pack_sha256: str
    created_at_utc: str
    updated_at_utc: str
    history: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_id": "SCHEMA-DEVPL-STORY-EXECUTION-STATE-V1",
            "schema_version": "1.0.0",
            "execution_id": self.execution_id,
            "workspace_id": self.workspace_id,
            "project_id": self.project_id,
            "story_id": self.story_id,
            "story_version": self.story_version,
            "status": self.status.value,
            "sequence": self.sequence,
            "dor_report_sha256": self.dor_report_sha256,
            "context_pack_id": self.context_pack_id,
            "context_pack_sha256": self.context_pack_sha256,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "history": list(self.history),
            "runtime_only": True,
            "source_mutations_performed": False,
            "network_used": False,
            "external_api_used": False,
        }
        payload["state_sha256"] = canonical_sha256(payload)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StoryExecutionState":
        expected = str(payload.get("state_sha256") or "")
        body = {k: v for k, v in payload.items() if k != "state_sha256"}
        if expected and canonical_sha256(body) != expected:
            raise StoryExecutionTransitionError("STORY_EXECUTION_STATE_HASH_MISMATCH")
        return cls(
            execution_id=str(payload["execution_id"]),
            workspace_id=str(payload["workspace_id"]),
            project_id=str(payload["project_id"]),
            story_id=str(payload["story_id"]),
            story_version=str(payload["story_version"]),
            status=StoryExecutionStatus(str(payload["status"])),
            sequence=int(payload["sequence"]),
            dor_report_sha256=str(payload["dor_report_sha256"]),
            context_pack_id=str(payload["context_pack_id"]),
            context_pack_sha256=str(payload["context_pack_sha256"]),
            created_at_utc=str(payload["created_at_utc"]),
            updated_at_utc=str(payload["updated_at_utc"]),
            history=tuple(payload.get("history") or []),
        )

    def transition(self, target: StoryExecutionStatus, *, actor_id: str, observed_at_utc: str) -> "StoryExecutionState":
        expected = _ALLOWED_TRANSITIONS.get(self.status)
        if expected != target:
            raise StoryExecutionTransitionError(f"STORY_EXECUTION_INVALID_TRANSITION:{self.status.value}->{target.value}")
        if self.status is StoryExecutionStatus.PLANNED and target is StoryExecutionStatus.IN_PROGRESS:
            if not self.dor_report_sha256 or not self.context_pack_sha256:
                raise StoryExecutionTransitionError("STORY_EXECUTION_DOR_CONTEXT_REQUIRED")
        event = {
            "sequence": self.sequence + 1,
            "from": self.status.value,
            "to": target.value,
            "actor_id": str(actor_id),
            "observed_at_utc": str(observed_at_utc),
        }
        return replace(
            self,
            status=target,
            sequence=self.sequence + 1,
            updated_at_utc=str(observed_at_utc),
            history=(*self.history, event),
        )


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
