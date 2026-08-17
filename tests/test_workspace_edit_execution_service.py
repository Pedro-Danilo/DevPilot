from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from devpilot_core.application.workspace_documents_service import WorkspaceDocumentsApplicationService
from devpilot_core.application.workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from devpilot_core.application.approval_service import ApprovalApplicationService
from devpilot_core.application.auth_service import AuthApplicationService
from devpilot_core.application.workspace_edit_plan_service import WorkspaceEditPlanApplicationService
from devpilot_core.cli_models import Finding, Severity
from devpilot_core.schemas import SchemaValidator
from uoc004_fixtures import create_uoc004_workspace, sha

ROOT = Path(__file__).resolve().parents[1]


def make_platform(tmp_path: Path) -> Path:
    platform = tmp_path / "platform"
    for rel in [".devpilot/approval/sensitive_action_catalog.json", ".devpilot/approval/approval_authority_matrix.json", ".devpilot/identity/identity_registry.json", ".devpilot/identity/server_rbac_policy_catalog.json"]:
        target = platform / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    return platform


def make_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform = make_platform(tmp_path)
    ws = create_uoc004_workspace(tmp_path / "inventory-sales-local")
    subprocess.run(["git", "init", "-q"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.email", "uoc005@example.invalid"], cwd=ws, check=True)
    subprocess.run(["git", "config", "user.name", "UOC005 Fixture"], cwd=ws, check=True)
    subprocess.run(["git", "add", "."], cwd=ws, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture baseline"], cwd=ws, check=True)
    control = tmp_path / "control" / "uoc005"
    monkeypatch.setenv("DEVPILOT_ALLOWED_WORKSPACE_ROOTS", str(ws))
    monkeypatch.setenv("DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT", str(ws))
    monkeypatch.setenv("DEVPILOT_UOC005_CONTROL_ROOT", str(control))
    auth = AuthApplicationService(platform)
    issue = auth.bootstrap_owner(username="owner", display_name="DevPilot Owner", password="TestOwnerPassword!2026")
    docs = WorkspaceDocumentsApplicationService(platform)
    plans = WorkspaceEditPlanApplicationService(platform, documents=docs)
    execs = WorkspaceEditExecutionApplicationService(
        platform, documents=docs, plans=plans, approval_auth_store=auth.store
    )
    listing = docs.list_documents(limit=100)
    ids = {n["relative_path"]: n["document_id"] for n in listing.data["nodes"] if n.get("kind") == "document"}
    return platform, ws, control, plans, execs, ids, auth, issue


def plan_markdown(plans: WorkspaceEditPlanApplicationService, ws: Path, document_id: str):
    path = ws / "docs/00_product/product_vision.md"
    proposed = path.read_text(encoding="utf-8") + "\n## UOC-005 fixture\n\nApproval-bound change.\n"
    result = plans.plan(document_id=document_id, document_sha_before=sha(path), proposed_content=proposed)
    assert result.ok, [f.to_dict() for f in result.findings]
    return result.data["plan"], path


def approve(
    platform: Path,
    auth: AuthApplicationService,
    issue,
    approval_id: str,
):
    """Decide a historical low-level fixture request through current D authority.

    These service tests continue exercising the UOC-005 mutation machinery
    directly, but an executable sensitive action is never authorized by the
    legacy actor-only decision path after GSDLC-02-D.
    """
    approvals = ApprovalApplicationService(platform, auth_store=auth.store)
    result = approvals.decide_authenticated(
        approval_id=approval_id,
        decision="approved",
        principal=issue.context.principal,
        session=issue.context,
        caller_actor=None,
        reason="Fixture authenticated human approval",
    )
    assert result.ok, [f.to_dict() for f in result.findings]


def test_apply_requires_exact_approved_binding_and_supports_manual_rollback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform, ws, control, plans, execs, ids, auth, issue = make_service(tmp_path, monkeypatch)
    plan, path = plan_markdown(plans, ws, ids["docs/00_product/product_vision.md"])
    base = sha(path)
    blocked = execs.apply(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id="", actor="local-owner")
    assert not blocked.ok and sha(path) == base
    request = execs.request_apply_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="local-owner", reason="Apply reviewed plan")
    assert request.ok
    approval_id = request.data["approval"]["approval_id"]
    approve(platform, auth, issue, approval_id)
    applied = execs.apply(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="local-owner")
    assert applied.ok, [f.to_dict() for f in applied.findings]
    execution = applied.data["execution"]
    assert sha(path) == plan["document"]["proposed_sha256"]
    backup = (control / execution["backup_ref"]).resolve()
    assert backup.is_file()
    assert backup.is_relative_to(control.resolve())
    assert execution["approval"]["status"] == "approved"
    assert execution["approval"]["action"] == "filesystem.workspace_document_apply"
    assert execution["duration_ms"] >= 0
    report = (control / execution["report_ref"]).resolve()
    evidence = (control / execution["evidence_ref"]).resolve()
    assert report.is_file() and report.is_relative_to(control.resolve())
    assert evidence.is_file() and evidence.is_relative_to(control.resolve())
    validated = SchemaValidator(ROOT).validate_payload(schema="WorkspaceEditExecution", payload=execution, instance_label="uoc005-execution")
    assert validated.ok, validated.to_dict()
    assert subprocess.run(["git", "diff", "--name-only"], cwd=ws, check=True, text=True, capture_output=True).stdout.strip() == "docs/00_product/product_vision.md"
    rb_req = execs.request_rollback_approval(execution_id=execution["execution_id"], actor="local-owner", reason="Restore fixture")
    assert rb_req.ok
    rb_approval = rb_req.data["approval"]["approval_id"]
    approve(platform, auth, issue, rb_approval)
    rolled = execs.rollback(execution_id=execution["execution_id"], approval_id=rb_approval, actor="local-owner")
    assert rolled.ok and sha(path) == base
    assert rolled.data["execution"]["rollback"]["approval"]["status"] == "approved"
    assert rolled.data["execution"]["rollback"]["integrity_pass"] is True
    assert subprocess.run(["git", "status", "--porcelain"], cwd=ws, check=True, text=True, capture_output=True).stdout.strip() == ""


def test_absent_expired_hash_mismatch_and_stale_source_block_without_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform, ws, _, plans, execs, ids, auth, issue = make_service(tmp_path, monkeypatch)
    plan, path = plan_markdown(plans, ws, ids["docs/00_product/product_vision.md"])
    base = sha(path)
    req = execs.request_apply_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="local-owner", reason="Review")
    approval_id = req.data["approval"]["approval_id"]
    approve(platform, auth, issue, approval_id)
    mismatch = execs.apply(plan_id=plan["plan_id"], plan_hash="0" * 64, approval_id=approval_id, actor="local-owner")
    assert not mismatch.ok and sha(path) == base
    path.write_text(path.read_text(encoding="utf-8") + "\nexternal drift\n", encoding="utf-8")
    drift_sha = sha(path)
    stale = execs.apply(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="local-owner")
    assert not stale.ok and sha(path) == drift_sha


def test_expired_approved_binding_is_rejected_without_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform, ws, _, plans, execs, ids, auth, issue = make_service(tmp_path, monkeypatch)
    plan, path = plan_markdown(plans, ws, ids["docs/00_product/product_vision.md"])
    base = sha(path)
    req = execs.request_apply_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="local-owner", reason="Review")
    approval_id = req.data["approval"]["approval_id"]
    approve(platform, auth, issue, approval_id)
    record = execs.approvals.store.get(approval_id)
    assert record is not None
    payload = record.to_dict(); payload["expires_at"] = "2020-01-01T00:00:00Z"
    execs.approvals.store.local_store.update_approval(payload)
    blocked = execs.apply(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="local-owner")
    assert not blocked.ok and sha(path) == base


def test_post_validation_block_triggers_automatic_rollback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform, ws, _, plans, execs, ids, auth, issue = make_service(tmp_path, monkeypatch)
    plan, path = plan_markdown(plans, ws, ids["docs/00_product/product_vision.md"])
    base = sha(path)
    req = execs.request_apply_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="local-owner", reason="Review")
    approval_id = req.data["approval"]["approval_id"]
    approve(platform, auth, issue, approval_id)
    monkeypatch.setattr(execs, "_post_validate", lambda plan, target: [Finding("FORCED_POST_BLOCK", "forced", Severity.BLOCK)])
    result = execs.apply(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="local-owner")
    assert not result.ok
    assert result.data["execution"]["status"] == "rolled-back-automatic"
    assert sha(path) == base


def test_manual_rollback_is_blocked_after_staging(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    platform, ws, _, plans, execs, ids, auth, issue = make_service(tmp_path, monkeypatch)
    plan, path = plan_markdown(plans, ws, ids["docs/00_product/product_vision.md"])
    req = execs.request_apply_approval(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], actor="local-owner", reason="Review")
    approval_id = req.data["approval"]["approval_id"]
    approve(platform, auth, issue, approval_id)
    applied = execs.apply(plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval_id, actor="local-owner")
    assert applied.ok
    subprocess.run(["git", "add", "docs/00_product/product_vision.md"], cwd=ws, check=True)
    blocked = execs.request_rollback_approval(execution_id=applied.data["execution"]["execution_id"], actor="local-owner", reason="Too late")
    assert not blocked.ok
