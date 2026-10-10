from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _view() -> str:
    return (ROOT / "ui/web/src/pages/StoryCodeWorkbenchView.ts").read_text(encoding="utf-8")


def test_incremental_tree_exposes_source_and_proposal_variants_for_same_path() -> None:
    view = _view()
    assert "label:`${row.name} · SOURCE`" in view
    assert "label:`${row.target_path.split('/').pop()??row.target_path} · PROPOSAL ${row.operation}`" in view
    assert "if(!byPath.has(row.target_path))" not in view
    assert "SOURCE actual y PROPOSAL EDIT por separado" in view


def test_proposal_editor_is_read_only_and_reflects_real_operation() -> None:
    view = _view()
    assert "mode.value=row.operation" in view
    assert "mode.disabled=true" in view
    assert "editor.readOnly=true" in view
    assert "PROPOSAL ${row.operation}" in view
    assert "editable solo como override Manual; no es la propuesta" in view


def test_proposal_summary_explains_delta_counts_instead_of_implying_file_cap() -> None:
    view = _view()
    assert "editTotal=implementationProposal.files.filter((row)=>row.operation==='EDIT').length" in view
    assert "createTotal=implementationProposal.files.filter((row)=>row.operation==='CREATE').length" in view
    assert "files=${implementationProposal.files.length} (${editTotal} EDIT + ${createTotal} CREATE)" in view


def test_source_registry_tracks_cor108_review_contract() -> None:
    import json
    registry = json.loads((ROOT / ".devpilot/docs_governance/source_registry.json").read_text(encoding="utf-8"))
    assert registry["gsdlc_13_d_05_status"] == "ACTIVE-CORRECTIVE/COR-108-PENDING-WINDOWS"
    active = [row for row in registry["documents"] if row.get("path") == "docs/05_operations/DEVPL_GSDLC_13_D_STORY_CODE_WORKBENCH_OPERATIONAL_CONTRACT_v1_0_11.md"]
    assert len(active) == 1
    assert "tests/test_devpl_gsdlc_13_d_05_proposal_review_ux.py" in active[0]["required_tests"]
