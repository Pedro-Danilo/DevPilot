"""P7: Owner successor and preservation tests; no real model or network access."""
from __future__ import annotations

from pathlib import Path

import pytest

from devpilot_core.application import pre_code_wizard_service as pre
from devpilot_core.application.r03_04_local_authoring import (
    R0304LocalAuthoring, compose_architecture, technology_prompt, validate_technology,
)
from test_mp132_r03_04_c02_p5_flow import ARCH, ADR, TECH, LocalModel


def test_owner_revision_is_immutable_no_model_and_rejects_tampered_parent(tmp_path: Path):
    writer = R0304LocalAuthoring(tmp_path)
    calls = LocalModel(TECH)
    parent = writer.infer(workspace_id="pilot-b",kind="technology",
        input_binding={"arch_sha":"a"*64},prompt="bounded",model="gemma3:4b",adapter=calls)
    original = writer.bound_candidate("pilot-b",parent)
    improved = TECH.replace("API local y SQLite","Python modular y SQLite") if "API local y SQLite" in TECH else TECH.replace("SQLite local","Python modular y SQLite")
    assert improved!=TECH
    updated = writer.owner_revision(workspace_id="pilot-b",kind="technology",
                                  content=improved,parent=parent,actor="owner-pilot-b")
    assert updated["origin"]=="OWNER_REVISION"
    assert updated["revision_of_sha256"]==parent["candidate_sha256"]
    assert updated["created_by"]=="owner-pilot-b"
    assert writer.bound_candidate("pilot-b",updated)==improved.strip()
    assert writer.bound_candidate("pilot-b",parent)==original
    assert writer.owner_revision(workspace_id="pilot-b",kind="technology",
                                content=improved,parent=updated,actor="owner-pilot-b")["candidate_sha256"]==updated["candidate_sha256"]
    assert updated["network_scope"]=="none" and updated["source_mutations_performed"] is False
    assert not (tmp_path/"docs").exists()
    with pytest.raises(ValueError,match="R0304_OWNER_STRUCTURE_BLOCK"):
        writer.owner_revision(workspace_id="pilot-b",kind="technology",
                              content="# Technology Options\nIncompleto.",parent=updated,actor="owner-pilot-b")
    forged={**parent,"candidate_sha256":"0"*64}
    with pytest.raises(ValueError,match="R0304_CANDIDATE_SOURCE_DRIFT"):
        writer.owner_revision(workspace_id="pilot-b",kind="technology",
                              content=improved,parent=forged,actor="owner-pilot-b")


def test_owner_review_rejects_missing_prerequisites_and_resets_selection(tmp_path:Path,monkeypatch):
    project=tmp_path/"pilot-b"
    (project/".devpilot").mkdir(parents=True)
    (project/".devpilot/project.yaml").write_text("project_name: Pilot B\n",encoding="utf-8")
    from test_mp132_r03_04_c02_p5_flow import hashlib
    row={"mode":"LOCAL_MODEL","status":"DRAFT","approval_id":None,"content":ARCH,
         "content_sha256":hashlib.sha256(ARCH.encode()).hexdigest(),
         "derivation":{"model":"gemma3:4b"}}
    state={"stages":{"architecture":row},"r03_04_authoring":{}}
    service=object.__new__(pre.PreCodeWizardApplicationService)
    service.root=tmp_path
    service.technology_authoring=R0304LocalAuthoring(tmp_path)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_context",lambda self:("pilot-b",project))
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_load_state",lambda self,*args:state)
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_write_state",lambda self,*args:state.update(args[-1]))
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_current_stage",lambda self,*args:{"stage_id":"architecture"})
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_stage_state",lambda self,data,name:data["stages"][name])
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_r0304_frozen_context",
        lambda self,*args:{"product-vision":"Visión aprobada","scope":"Agentes diferidos, inventario",
                           "requirements":"RF-006 coherencia"})
    monkeypatch.setattr(pre,"parse_project_yaml_metadata",lambda *args:{"project_name":"Pilot B"})
    monkeypatch.setattr(pre.PreCodeWizardApplicationService,"_append_trace",lambda *args,**kwargs:None)
    def adapter(self,adapter,model,*,explicit_owner_action=False):
        assert explicit_owner_action
        return LocalModel(TECH)
    monkeypatch.setattr(R0304LocalAuthoring,"_local_adapter",adapter)
    common=dict(actor="owner-pilot-b",session_principal="owner-pilot-b",actor_role="owner",
                effective_roles=["owner"],workspace_scopes=["pilot-b"],model="gemma3:4b")
    rejected=service.technology_action(action="owner_revise_options",content=TECH,**common)
    assert not rejected.ok  # no source candidate to revise
    assert service.technology_action(action="generate_options",**common).ok
    assert service.technology_action(action="select_option",option_id="T1",**common).ok
    revised=TECH.replace("SQLite local","SQLite transaccional local")
    unauthorized=service.technology_action(action="owner_revise_options",content=revised,
        **{**common,"actor_role":"viewer","effective_roles":["viewer"]})
    assert not unauthorized.ok
    result=service.technology_action(action="owner_revise_options",content=revised,**common)
    assert result.ok,result.message
    auth=state["r03_04_authoring"]
    assert auth["technology"]["origin"]=="OWNER_REVISION"
    assert auth["selected_option_id"] is None and auth["adr"] is None
    assert auth["status"]=="TECH_OPTIONS_DRAFT"
    assert not (project/"docs").exists()
    row["status"]="FROZEN"
    assert not service.technology_action(action="owner_revise_options",content=TECH,**common).ok


def test_architecture_reconciliation_preserves_owner_sections():
    arch=ARCH.replace("Texto viejo.","ADR-PB-01 pendiente.\n") if "Texto viejo." in ARCH else ARCH
    technology=TECH
    chosen=compose_architecture(arch,technology,"T1",ADR,"a"*64,"b"*64)
    assert "Propuesta inicial por reconciliar" in chosen
    assert "Todavía no reconciliadas" in chosen
    assert "<!-- R0304-TECH-BEGIN -->" in chosen
    assert "<!-- R0304-ADR-BEGIN -->" in chosen
    assert compose_architecture(chosen,technology,"T1",ADR,"a"*64,"b"*64)==chosen
    assert validate_technology(technology)==[]


def test_prompt_references_frozen_boundaries_and_python_with_conditions():
    prompt=technology_prompt("Pilot B","# Architecture\n## Contexto\nUna persona",
       {"product-vision":"venta y cuidado personal",
        "scope":"SC-IN-01 inventario; SC-DEF-01 agentes diferidos",
        "requirements":"RF-006 consistencia; RNF-004 controles"})
    for phrase in ("SC-DEF","Python","SQLite","PostgreSQL","complejidad proporcional","No impongas"):
        assert phrase in prompt


def test_p7_ui_does_not_hide_pending_status_below_full_markdown():
    base=Path(__file__).resolve().parents[1]
    ui=(base/"ui/web/src/pages/PreCodeWizardView.ts").read_text(encoding="utf-8")
    css=(base/"ui/web/src/styles.css").read_text(encoding="utf-8")
    assert "workflow.append(heading,feedback)" in ui
    assert "Guardar revisión Owner de Technology Options" in ui
    assert "white-space:pre-wrap; overflow-wrap:anywhere" in css
