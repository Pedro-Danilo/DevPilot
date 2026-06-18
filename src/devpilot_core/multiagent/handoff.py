from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return a compact UTC timestamp for handoff evidence."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class HandoffRecord:
    """Explicit governed handoff between two DevPilot agents.

    FUNC-SPRINT-90 deliberately models handoff as first-class evidence instead
    of allowing implicit delegation. Every coordinator step after the first must
    have a HandoffRecord and a local trace event before the child agent is run.
    """

    workflow_id: str
    sequence: int
    from_agent: str | None
    to_agent: str
    reason: str
    target: str
    dry_run: bool = True
    explicit: bool = True
    policy_checked: bool = False
    policy_allowed: bool = False
    trace_event_emitted: bool = False
    event_id: str | None = None
    event_path: str | None = None
    handoff_id: str = field(default_factory=lambda: f"handoff_{uuid.uuid4().hex}")
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "handoff_id": self.handoff_id,
            "workflow_id": self.workflow_id,
            "sequence": self.sequence,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "reason": self.reason,
            "target": self.target,
            "dry_run": self.dry_run,
            "explicit": self.explicit,
            "policy_checked": self.policy_checked,
            "policy_allowed": self.policy_allowed,
            "trace_event_emitted": self.trace_event_emitted,
            "created_at": self.created_at,
        }
        if self.event_id:
            payload["event_id"] = self.event_id
        if self.event_path:
            payload["event_path"] = self.event_path
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload
