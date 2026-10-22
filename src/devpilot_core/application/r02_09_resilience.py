"""R02-09: durable, bounded call-start receipts for local model obligations.

No model response, prompt, credential or workspace document is stored here.
A STARTED/RESPONSE_RECEIVED/UNKNOWN receipt prevents uncertain replay after crash.
A failed, fully observed response uses a *new* explicit attempt, never auto-retry.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .r02_07_segmented import atomic_json, read_json

_STATUSES = frozenset({"STARTED", "RESPONSE_RECEIVED", "UNKNOWN", "FAILED", "COMPLETED"})


def begin_call(folder: Path, *, plan_hash: str, unit_id: str, model: str, attempt: int) -> Path:
    if not re.fullmatch(r"[a-f0-9]{64}", plan_hash) or not re.fullmatch(r"[A-Za-z0-9_-]{1,42}", unit_id):
        raise ValueError("R0209_RECEIPT_ID_INVALID")
    if not isinstance(attempt, int) or not 1 <= attempt <= 3 or not isinstance(model, str) or len(model) > 100:
        raise ValueError("R0209_ATTEMPT_INVALID")
    path = folder / "model_call_receipts" / f"{unit_id}.attempt-{attempt:02d}.json"
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("R0209_RECEIPT_SYMLINK_DENY")
    if path.exists():
        raise ValueError("R0209_ATTEMPT_ALREADY_CONSUMED")
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(path, {"schema": "R0209.local_call.v1", "plan_hash": plan_hash,
        "unit_id": unit_id, "model": model, "attempt": attempt,
        "status": "STARTED", "model_call_budget": 3,
        "raw_response_stored": False, "external_api_used": False, "workspace_writes": 0})
    return path


def transition(path: Path, status: str) -> None:
    if status not in _STATUSES or status == "STARTED":
        raise ValueError("R0209_RECEIPT_STATUS_INVALID")
    data = read_json(path)
    if data.get("schema") != "R0209.local_call.v1":
        raise ValueError("R0209_RECEIPT_DRIFT")
    previous = data.get("status")
    edges = {"STARTED": {"RESPONSE_RECEIVED", "FAILED", "UNKNOWN"},
             "RESPONSE_RECEIVED": {"FAILED", "COMPLETED"}}
    if status not in edges.get(previous, set()):
        raise ValueError("R0209_RECEIPT_TRANSITION_DENY")
    data["status"] = status
    atomic_json(path, data)


def guard_replay(folder: Path, unit_id: str, plan_hash: str, model: str) -> None:
    """Reject uncertain prior attempts before any new remote call."""
    directory = folder / "model_call_receipts"
    if directory.is_symlink():
        raise ValueError("R0209_RECEIPT_SYMLINK_DENY")
    if not directory.is_dir():
        return
    for path in directory.glob(f"{unit_id}.attempt-*.json"):
        data = read_json(path)
        if (data.get("schema") != "R0209.local_call.v1" or
            data.get("unit_id") != unit_id or data.get("plan_hash") != plan_hash or
            data.get("model") != model or data.get("status") not in _STATUSES):
            raise ValueError("R0209_RECEIPT_DRIFT")
        if data["status"] in {"STARTED", "RESPONSE_RECEIVED", "UNKNOWN"}:
            raise ValueError("R0209_UNCERTAIN_MODEL_CALL_BLOCK")
        if data["status"] == "COMPLETED":
            # execute_one() calls this guard only for a unit with no checkpoint.
            raise ValueError("R0209_COMPLETED_CALL_CHECKPOINT_MISSING")


def verify_checkpoint_receipts(folder: Path, unit_id: str, plan_hash: str, model: str) -> None:
    """Existing historical checkpoints need not have R02-09 receipts.

    For a new checkpoint with our receipts, however, one completed call is
    mandatory and every recorded attempt must be bound to the same source.
    """
    directory=folder/"model_call_receipts"
    if directory.is_symlink():
        raise ValueError("R0209_RECEIPT_SYMLINK_DENY")
    if not directory.is_dir():
        return
    receipts=sorted(directory.glob(f"{unit_id}.attempt-*.json"))
    if not receipts:
        return
    completed=0
    for path in receipts:
        data=read_json(path)
        if (data.get("schema")!="R0209.local_call.v1" or
            data.get("unit_id")!=unit_id or data.get("plan_hash")!=plan_hash or
            data.get("model")!=model or data.get("status") not in _STATUSES):
            raise ValueError("R0209_RECEIPT_DRIFT")
        if data["status"]=="COMPLETED":
            completed+=1
        elif data["status"] not in {"FAILED"}:
            raise ValueError("R0209_UNCERTAIN_MODEL_CALL_BLOCK")
    if completed!=1:
        raise ValueError("R0209_CHECKPOINT_RECEIPT_MISSING_OR_MULTIPLE")
