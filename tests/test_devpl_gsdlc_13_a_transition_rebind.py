from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def j(p): return json.loads((ROOT/p).read_text(encoding="utf-8"))
def test_13a_current_authority_and_parent_are_exact():
 s=j(".devpilot/project_state.json")
 assert s["current_phase"]=="DEVPL-GSDLC-13"
 assert s["current_micro_sprint"]=="DEVPL-GSDLC-13-A"
 assert s["next_micro_sprint"]=="DEVPL-GSDLC-13-B"
 assert s["gsdlc_13_a_execution_source_commit"]=="423e99fa38df3114328b555aff8f859740a49a01"
 assert s["gsdlc_13_a_full_regression_runs"]==0
 assert s["gsdlc_13_a_greenfield_project_writes"]==0
 assert s["ux_p0_status"]=="CLOSED/PASS/WINDOWS-VALIDATED"
def test_13a_authority_pack_and_acceptance_mode_are_materialized():
 required=[
 "docs/00_product/DEVPL_GSDLC_13_OWNER_DEVPL_CHATGPT_OPERATING_MODEL_v1_0_0_APPROVED.md",
 "docs/05_operations/DEVPL_GSDLC_13_GREENFIELD_USER_JOURNEY_RUNBOOK_v1_0_0_APPROVED.md",
 "docs/validation/DEVPL_GSDLC_13_ACCEPTANCE_CHECKPOINT_PROTOCOL_v1_0_0_APPROVED.md",
 "docs/validation/DEVPL_GREENFIELD_E2E_PRODUCT_ACCEPTANCE_CHARTER_v1_1_0_APPROVED.md",
 "docs/backlogs/DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_REBASELINE_v2_1_0_APPROVED.md",
 "docs/00_product/DEVPL_GSDLC_13_GREENFIELD_REAL_PRODUCT_ACCEPTANCE_ROADMAP_v1_1_0_APPROVED.md",
 "docs/backlogs/DEVPL_GSDLC_13_REAL_PRODUCT_ACCEPTANCE_BACKLOG_v1_1_0_APPROVED.md"]
 for p in required:
  text=(ROOT/p).read_text(encoding="utf-8"); assert "status:" in text
 model=(ROOT/required[0]).read_text(encoding="utf-8")
 lower=model.lower(); assert "owner-driven" in lower and "devpilot-executed" in lower and "chatgpt" in lower
def test_13a_roots_are_registered_but_greenfield_not_materialized():
 r=j(".devpilot/gsdlc/gsdlc13_acceptance_roots.json")
 assert r["greenfield_project_materialized"] is False
 assert r["greenfield_project_writes"]==0
 assert r["greenfield_workspace_root"].endswith("inventory-sales-local-greenfield")
 assert not (ROOT/"inventory-sales-local-greenfield").exists()
def test_13a_current_metadata_is_coherent():
 s=j(".devpilot/project_state.json"); c=j(".devpilot/release/local_release_candidate_criteria.json"); p=j("ui/web/package.json")
 assert c["expected_current_micro_sprint"]==s["current_micro_sprint"]
 assert c["expected_next_micro_sprint"]==s["next_micro_sprint"]
 assert c["expected_current_repo"]==s["current_repo"]
 assert p["devpilot"]["currentSprint"]==s["current_micro_sprint"]
 assert p["devpilot"]["gsdlc13GreenfieldProjectMaterialized"] is False
def test_13a_source_registry_points_to_successor_and_authorities():
 s=j(".devpilot/project_state.json"); r=j(".devpilot/docs_governance/source_registry.json")
 assert r["current_repo"]==s["current_repo"]
 ids={x["doc_id"] for x in r["documents"]}
 for i in {"DEVPL-GSDLC-13-OWNER-DEVPL-CHATGPT-OPERATING-MODEL","DEVPL-GSDLC-13-GREENFIELD-USER-JOURNEY-RUNBOOK","DEVPL-GSDLC-13-ACCEPTANCE-CHECKPOINT-PROTOCOL","DEVPL-GSDLC-13-REBASELINE","DEVPL-GSDLC-13-ACCEPTANCE-ROOTS"}: assert i in ids
