from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from devpilot_core.miasi.applicability import MIASIApplicabilityEvaluator

PRE_CODE_STATE_ROOT = Path("outputs/pre_code_wizard/gsdlc_05_e")


def _deferred_miasi(platform_root: Path, workspace_id: str) -> dict[str, Any]:
    evaluator = MIASIApplicabilityEvaluator(platform_root)
    context_path = evaluator.context_path(workspace_id)
    try:
        context_source = context_path.relative_to(platform_root).as_posix()
    except ValueError:
        context_source = str(context_path)
    return {
        "status": "NOT_EVALUATED",
        "gate_status": "DEFERRED",
        "reason_codes": ["MIASI_APPLICABILITY_DEFERRED_UNTIL_PRE_CODE"],
        "risk_level": "unknown",
        "project_decision": {},
        "feature_decisions": [],
        "required_controls": [],
        "missing_controls": [],
        "policy_binding": {},
        "blockers": [],
        "evidence_refs": [],
        "context_source": context_source,
        "reevaluation_required": True,
        "agent_execution_allowed": False,
        "rag_execution_allowed": False,
        "execution_reason_code": "MIASI_EVALUATION_DEFERRED",
        "network_used": False,
        "external_api_used": False,
        "model_execution_used": False,
        "agents_executed": False,
        "rag_executed": False,
        "source_mutations_performed": False,
        "pre_code_authoritative": False,
        "blocking_scope": "pre-code-readiness",
    }


def load_pre_code_boundary(platform_root: Path, workspace_id: str) -> dict[str, Any]:
    """Read-only bridge between the Pre-code runtime and cross-surface status.

    It never mutates WorkspaceEngineeringState or managed workspace source.
    MIPSoftware global lifecycle and the bounded Pre-code profile remain separate
    authorities; this projection only exposes their relationship honestly.
    """
    root = Path(platform_root).resolve()
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(workspace_id))
    state_path = root / PRE_CODE_STATE_ROOT / safe / "state.json"
    if not state_path.is_file():
        return {
            "available": False,
            "workspace_id": workspace_id,
            "state_path": state_path.relative_to(root).as_posix(),
            "reason_code": "PRE_CODE_RUNTIME_STATE_MISSING",
        }
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "available": False,
            "workspace_id": workspace_id,
            "state_path": state_path.relative_to(root).as_posix(),
            "reason_code": "PRE_CODE_RUNTIME_STATE_INVALID",
        }
    stages = state.get("stages") if isinstance(state.get("stages"), dict) else {}
    ordered = ("product-vision", "scope", "requirements", "architecture", "security", "test-strategy", "traceability")
    statuses = {stage_id: str((stages.get(stage_id) or {}).get("status") or "MISSING") for stage_id in ordered}
    frozen = sum(1 for status in statuses.values() if status == "FROZEN")
    current = next((stage_id for stage_id in ordered if statuses[stage_id] != "FROZEN"), None)
    evaluator = MIASIApplicabilityEvaluator(root)
    context_path = evaluator.context_path(workspace_id)
    if context_path.is_file():
        try:
            miasi = evaluator.evaluate_workspace(workspace_id, {"artifacts": []}).to_payload()
            miasi.update({"pre_code_authoritative": True, "blocking_scope": "pre-code-readiness"})
        except Exception:
            miasi = {
                **_deferred_miasi(root, workspace_id),
                "status": "REVIEW_REQUIRED",
                "gate_status": "BLOCK",
                "reason_codes": ["MIASI_APPLICABILITY_EVALUATION_ERROR"],
                "pre_code_authoritative": True,
                "reevaluation_required": True,
            }
    else:
        miasi = _deferred_miasi(root, workspace_id)
    all_frozen = frozen == len(ordered)
    ready = bool(all_frozen and str(miasi.get("gate_status") or "").upper() == "PASS" and str(state.get("status") or "").upper() == "PRE_CODE_READY")
    return {
        "available": True,
        "profile_id": str(state.get("profile_id") or "guided-pre-code-manual-v1"),
        "workspace_id": workspace_id,
        "state_status": str(state.get("status") or "NOT_STARTED"),
        "state_path": state_path.relative_to(root).as_posix(),
        "mandatory_stages_total": len(ordered),
        "mandatory_stages_frozen": frozen,
        "percent": round(100.0 * frozen / len(ordered), 2),
        "all_stages_frozen": all_frozen,
        "current_stage_id": current,
        "statuses": statuses,
        "miasi": miasi,
        "strict_readiness_status": "PASS" if ready else "BLOCK",
        "pre_code_ready": ready,
        "next_boundary": "planning-roadmap" if ready else ("miasi-applicability" if all_frozen else "pre-code-stage"),
        "server_authoritative": True,
        "read_only": True,
        "source_mutations_performed": False,
    }
