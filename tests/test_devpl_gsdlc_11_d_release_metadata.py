from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from devpilot_core.application.release_metadata_service import ReleaseMetadataApplicationService


@dataclass
class _Context:
    configured: bool = True
    valid: bool = True
    active_workspace_root: Path | None = None
    active_workspace_id: str = "devpilot-local"


class _Resolver:
    def __init__(self, root: Path) -> None:
        self.context = _Context(active_workspace_root=root)

    def resolve(self):
        return self.context


def _git(root: Path, *args: str) -> str:
    cp = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)
    return cp.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".devpilot").mkdir(parents=True)
    (root / "docs/audits").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nname="devpilot-local"\nversion="0.1.0"\n', encoding="utf-8")
    state = {
        "gsdlc_11_c_status": "CLOSED/PASS/WINDOWS-VALIDATED",
        "gsdlc_11_d_authorized": True,
        "gsdlc_11_full_regression_budget_consumed": 0,
    }
    (root / ".devpilot/project_state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    (root / "docs/audits/DEVPL_GSDLC_11_C_IMPLEMENTATION_REPORT.md").write_text("# 11-C\nPASS\n", encoding="utf-8")
    _git(root.parent, "init", str(root))
    _git(root, "config", "user.email", "devpilot@example.invalid")
    _git(root, "config", "user.name", "DevPilot Test")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "GSDLC-11-C closed REQ-RELEASE-001 STORY-ROLLBACK-001")
    return root


def _service(root: Path) -> ReleaseMetadataApplicationService:
    return ReleaseMetadataApplicationService(root, context_resolver=_Resolver(root))


def _prepare(service: ReleaseMetadataApplicationService):
    return service.prepare(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], mode="MANUAL", version="0.1.0", manual_notes="Validated local release lifecycle.")


def test_11d_happy_path_creates_only_exact_local_annotated_tag(tmp_path: Path):
    root = _repo(tmp_path)
    service = _service(root)
    prepared = _prepare(service)
    assert prepared.ok
    plan_result = service.tag_plan(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"])
    assert plan_result.ok
    plan = plan_result.data["tag_plan"]
    approved = service.approve(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], reason="Reviewed exact local release plan.")
    assert approved.ok
    approval = approved.data["release_approval"]
    executed = service.tag_execute(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval["approval_id"])
    assert executed.ok
    verification = executed.data["tag_verification"]
    assert verification["exact_commit_match"] is True
    assert verification["annotated"] is True
    assert verification["push_performed"] is False
    assert verification["publish_performed"] is False
    assert _git(root, "rev-list", "-n", "1", "v0.1.0") == _git(root, "rev-parse", "HEAD")
    assert _git(root, "cat-file", "-t", "refs/tags/v0.1.0") == "tag"
    assert _git(root, "remote", "-v") == ""


def test_11d_agent_proposal_has_no_approval_authority(tmp_path: Path):
    root = _repo(tmp_path)
    service = _service(root)
    result = service.prepare(actor="pedro", actor_roles=["release-manager"], workspace_scopes=["devpilot-local"], mode="AGENT_ASSISTED", version="0.1.0", agent_proposal="Proposed text from a local agent.")
    assert result.ok
    provenance = result.data["provenance"]
    assert provenance["mode"] == "AGENT_ASSISTED"
    assert provenance["proposal_has_authority"] is False
    status = service.status(actor="pedro", actor_roles=["release-manager"], workspace_scopes=["devpilot-local"])
    assert status.data["authority"]["model_or_agent_can_approve"] is False


def test_11d_version_drift_blocks(tmp_path: Path):
    root = _repo(tmp_path)
    result = _service(root).prepare(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], mode="MANUAL", version="0.2.0")
    assert not result.ok
    assert any(f.id == "GSDLC11D_VERSION_DRIFT_BLOCK" for f in result.findings)


def test_11d_unauthorized_role_cannot_prepare_or_approve(tmp_path: Path):
    root = _repo(tmp_path)
    service = _service(root)
    blocked = service.prepare(actor="viewer", actor_roles=["viewer"], workspace_scopes=["devpilot-local"], mode="MANUAL", version="0.1.0")
    assert not blocked.ok
    assert any(f.id == "GSDLC11D_RELEASE_ROLE_BLOCK" for f in blocked.findings)


def test_11d_existing_tag_conflict_fails_closed(tmp_path: Path):
    root = _repo(tmp_path)
    _git(root, "tag", "-a", "v0.1.0", "-m", "historical tag")
    result = _service(root).prepare(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], mode="MANUAL", version="0.1.0")
    assert not result.ok
    assert any(f.id == "GSDLC11D_EXISTING_TAG_CONFLICT_BLOCK" for f in result.findings)


def test_11d_approval_hash_mismatch_blocks_tag(tmp_path: Path):
    root = _repo(tmp_path)
    service = _service(root)
    assert _prepare(service).ok
    plan_result = service.tag_plan(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"])
    plan = plan_result.data["tag_plan"]
    approved = service.approve(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], reason="Reviewed")
    approval = approved.data["release_approval"]
    approval_path = root / "outputs/release/gsdlc11d/release_approval.json"
    altered = json.loads(approval_path.read_text(encoding="utf-8"))
    altered["plan_hash"] = "0" * 64
    approval_path.write_text(json.dumps(altered, indent=2) + "\n", encoding="utf-8")
    blocked = service.tag_execute(actor="pedro", actor_roles=["owner"], workspace_scopes=["devpilot-local"], plan_id=plan["plan_id"], plan_hash=plan["plan_hash"], approval_id=approval["approval_id"])
    assert not blocked.ok
    assert any(f.id == "GSDLC11D_APPROVAL_HASH_MISMATCH_BLOCK" for f in blocked.findings)
