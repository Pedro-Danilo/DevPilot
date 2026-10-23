"""R03-01: current-active audit, successor invariants and negative fixtures."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from devpilot_core.docs_governance.active_reconciliation import CURRENT, NEXT, PROGRAM, audit_repo


ROOT = Path(__file__).resolve().parents[1]


def test_reconciled_registry_and_program() -> None:
    report = audit_repo(ROOT)
    assert report["disposition"] == "PASS", report["findings"]
    assert report["documents_checked"] >= 1755
    assert report["active_duplicate_doc_ids"] == 0
    assert (ROOT / PROGRAM / "2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md").exists()


def test_owner_approval_does_not_authorize_future_sprints() -> None:
    base = ROOT / PROGRAM / "7_ Execution_packages-sprints_prompts/BACKLOG_R03"
    assert "status: SPRINT_EXECUTION_APPROVED" in (base / "02_sprints/R03_01_DOC_RECONCILIATION_SPRINT.md").read_text(encoding="utf-8")
    assert "status: OWNER_APPROVED" in (base / "03_prompts/R03_01_DOC_RECONCILIATION_PROMPT.md").read_text(encoding="utf-8")
    assert "status: DRAFT_EXECUTION_GATED" in (base / "02_sprints/R03_02_TECH_CONTEXT_PROFILE_SPRINT.md").read_text(encoding="utf-8")
    assert "status: DRAFT_AWAITING_OWNER_INCREMENT_APPROVAL" in (base / "03_prompts/R03_02_TECH_CONTEXT_PROFILE_PROMPT.md").read_text(encoding="utf-8")
    state = json.loads((ROOT / ".devpilot/project_state.json").read_text(encoding="utf-8"))
    assert state["current_micro_sprint"] == CURRENT
    assert state["next_micro_sprint"] == NEXT
    assert state["external_api_allowed"] is False
    assert state["connector_write_enabled"] is False


def _isolated_governance(tmp_path: Path) -> Path:
    dest = tmp_path / "repo"
    (dest / ".devpilot/docs_governance").mkdir(parents=True)
    (dest / ".devpilot/project_state.json").write_bytes((ROOT / ".devpilot/project_state.json").read_bytes())
    # Fixture keeps registry entries, but does not copy thousands of files: deliberately
    # verifies negative outcomes rather than attempting a full clean PASS.
    (dest / ".devpilot/docs_governance/source_registry.json").write_bytes(
        (ROOT / ".devpilot/docs_governance/source_registry.json").read_bytes()
    )
    return dest


def test_negative_pointer_mismatch_fails_closed(tmp_path: Path) -> None:
    dest = _isolated_governance(tmp_path)
    state_path = dest / ".devpilot/project_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["next_micro_sprint"] = "R03_02_EXECUTED_WITHOUT_APPROVAL"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    report = audit_repo(dest)
    assert report["disposition"] == "BLOCK"
    assert any(x["code"] == "POINTER_DRIFT" for x in report["findings"])


def test_negative_derived_count_and_duplicate_authority(tmp_path: Path) -> None:
    dest = _isolated_governance(tmp_path)
    path = dest / ".devpilot/docs_governance/source_registry.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["summary"]["documents_total"] += 1
    first = next(x for x in registry["documents"] if x.get("lifecycle") == "historical")
    first["lifecycle"] = "active"
    path.write_text(json.dumps(registry), encoding="utf-8")
    report = audit_repo(dest)
    assert any(x["code"] == "DERIVED_COUNT_DRIFT" for x in report["findings"])


def test_no_copy_or_mutation_by_audit(tmp_path: Path) -> None:
    dest = _isolated_governance(tmp_path)
    path = dest / ".devpilot/docs_governance/source_registry.json"
    before = path.read_bytes()
    audit_repo(dest)
    assert path.read_bytes() == before
