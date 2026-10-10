from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
VIEW_PATH = ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts"


def _view() -> str:
    return VIEW_PATH.read_text(encoding="utf-8")


def _function_source(name: str) -> str:
    view = _view()
    marker = f"function {name}("
    if marker not in view:
        marker = f"async function {name}("
    start = view.index(marker)
    next_plain = view.find("\n  function ", start + len(marker))
    next_async = view.find("\n  async function ", start + len(marker))
    candidates = [x for x in (next_plain, next_async) if x != -1]
    end = min(candidates) if candidates else len(view)
    return view[start:end]


def test_navigation_does_not_clear_active_source_change_plan() -> None:
    for name in ("openSource", "openProposalFile", "selectDraft"):
        assert "clearPlan()" not in _function_source(name), name


def test_owner_review_must_precede_predryrun_recheck() -> None:
    view = _view()
    assert "if(plan&&!dryRunPassed&&!approvalInput.value.trim()){planRecheckPassed=false;finalRecheckPassed=false;}" in view
    assert "planRecheck.disabled=!canAuthor||!plan||(!approvalInput.value.trim()&&!ownerReviewCheck.checked)" in view
    recheck = _function_source("recheckPlan")
    assert "!approvalInput.value.trim()&&!ownerReviewCheck.checked" in recheck
    assert "confirma primero la revisión Owner" in recheck


def test_active_plan_locks_draft_revision_mutations() -> None:
    view = _view()
    assert "const activePlanLocksDraft=Boolean(plan)" in view
    assert "selectedPreimagePass" in view
    assert "recheck.disabled=" in view and "activePlanLocksDraft||selectedPreimagePass" in view
    assert "discard.disabled=" in view and "activePlanLocksDraft" in view
    assert "save.disabled=" in view and "activePlanLocksDraft" in view
    for name in ("saveDraft", "recheckDraft", "discardDraft"):
        fn = _function_source(name)
        assert "if(plan)" in fn, name
        assert "BLOCK · existe un SourceChangePlan activo" in fn, name


def test_sequence_exposes_single_next_governed_action() -> None:
    seq = _function_source("renderPlanSequence")
    for text in (
        "SIGUIENTE: marca la confirmación Owner",
        "SIGUIENTE: pulsa Revalidar plan",
        "SIGUIENTE: pulsa Dry-run",
        "SIGUIENTE: solicita approval Owner",
        "SIGUIENTE: pulsa Revalidar plan para el recheck final",
        "SIGUIENTE: aplica el plan aprobado",
    ):
        assert text in seq


def test_registry_promotes_cor108_contract_without_mutating_history() -> None:
    registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    assert registry["gsdlc_13_d_05_status"] == "ACTIVE-CORRECTIVE/COR-108-PENDING-WINDOWS"
    by_path = {row.get("path"): row for row in registry["documents"]}
    old = by_path["docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_10.md"]
    new = by_path["docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_11.md"]
    assert old["classification"] == "historical" and old["lifecycle"] == "historical"
    assert new["classification"] == "source-of-truth" and new["lifecycle"] == "active"
    assert "tests/test_devpl_gsdlc_13_d_05_source_change_review_state.py" in new["required_tests"]
