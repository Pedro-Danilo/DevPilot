"""R01-13: read-only status of the already-authoritative Guided SDLC gate.

This module NEVER evaluates alternative transition authority or mutates a state.
It consumes the final server-side UI gate and NextAction (including governed
Planning/Pre-code overlays) once, and yields one value for header/panel/CTA.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA = "MP132.R01.13.workflow-status.v1"


def project_workflow_status(
    status: Mapping[str, Any],
    next_action: Mapping[str, Any],
    ui_state: str,
    lifecycle_reconciliation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail closed on pending/unknown gates; never turn preview into apply authority."""
    raw = str(ui_state or "UNKNOWN").upper()
    kind = str(next_action.get("kind") or "INSPECT_STATE").upper()
    available = next_action.get("available") is True
    mutating = next_action.get("mutating") is True
    terminal = (status.get("progress") or {}).get("terminal") is True
    blockers = status.get("blockers") or []
    lifecycle = str(status.get("lifecycle_status") or "UNKNOWN").upper()
    reason = str(next_action.get("reason_code") or "NEXT_ACTION_UNKNOWN")[:128]
    freshness = str((status.get("freshness") or {}).get("status") or "UNKNOWN").upper()
    recon = dict(lifecycle_reconciliation or {})
    source_fp = str((status.get("freshness") or {}).get("state_fingerprint") or "")[:128]
    if raw in {"BLOCKED", "REVALIDATION_REQUIRED"} or lifecycle in {"BLOCKED", "REVALIDATION_REQUIRED"}:
        state = "BLOCKED"
    elif raw in {"UNKNOWN", "EMPTY"}:
        state = "UNKNOWN"
    elif raw == "STALE" or freshness == "STALE":
        state = "PENDING"
    elif raw == "READY" and available and kind in {"ADVANCE_TRANSITION", "CONTINUE_STEP", "COMPLETE"}:
        state = "READY"
    else:
        state = "PENDING"
    # Terminal status needs confirmed underlying terminal lifecycle, not a visually READY panel.
    terminal_ready = (state == "READY" and kind == "COMPLETE" and terminal
                      and lifecycle == "RELEASED" and not blockers
                      and recon.get("authoritative_blocker_count", 0) == 0)
    can_continue = state == "READY" and available and not mutating and kind != "COMPLETE"
    return {
        "schema": SCHEMA,
        "status": state,
        "gate_ui_state": raw,
        "next_action_id": str(next_action.get("action_id") or "next.inspect-state")[:128],
        "next_action_reason": reason,
        "source_state_fingerprint": source_fp or None,
        "terminal_ready": terminal_ready,
        "terminal_cta_enabled": terminal_ready,
        "continue_cta_enabled": can_continue,
        "read_only": True,
        "source_authority": "guided-sdlc.project_status.next_action",
        "network_used": False,
        "external_api_used": False,
        "mutations_performed": False,
    }
