from __future__ import annotations
import hashlib, json
from datetime import date
from pathlib import Path
import pytest
from devpilot_core.rag.context_pack_v2 import ContextPackV2Builder, ContextPackV2Options, _freshness
from devpilot_core.application.services import ApplicationService
from devpilot_core.schemas.validator import SchemaValidator

ROOT=Path(__file__).resolve().parents[1]

def test_context_pack_v2_grounded_hash_citation_budget_and_local_only():
    result=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="requirements",as_of_date=date(2026,8,29))).build()
    assert result.ok is True, result.to_dict()
    summary=result.data["summary"]; pack=result.data["context_pack"]
    assert summary["status"] == "grounded"
    assert summary["sources_total"] >= 1
    assert summary["citations_total"] == summary["sources_total"]
    assert summary["source_hash_parity"] is True and summary["citation_source_parity"] is True
    assert pack["safety"]["network_used"] is False and pack["safety"]["external_api_used"] is False and pack["safety"]["embeddings_used"] is False
    for source in pack["sources"]:
        assert hashlib.sha256((ROOT/source["path"]).read_bytes()).hexdigest()==source["content_sha256"]
        assert source["trust_tag"] == "approved-local"
        assert "#L" in source["citation_ref"]
    assert SchemaValidator(ROOT).validate_payload(schema="ContextPackV2",payload=pack,instance_label="test").ok is True

def test_context_pack_v2_diff_first_and_top_k_are_bounded():
    baseline=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="architecture",top_k=3,as_of_date=date(2026,8,29))).build()
    assert baseline.ok
    path=baseline.data["context_pack"]["sources"][0]["path"]
    result=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="architecture",top_k=3,changed_paths=(path,),as_of_date=date(2026,8,29))).build()
    assert result.ok
    pack=result.data["context_pack"]
    assert len(pack["sources"]) <= 3
    assert any(x["diff_priority"] for x in pack["candidate_sources"])
    assert pack["budget"]["plan"]["allowed"] is True

def test_context_pack_v2_runtime_and_unregistered_sources_are_excluded():
    result=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="security-plan",query="auth devpilot security",as_of_date=date(2026,8,29))).build()
    assert result.ok
    paths=[x["path"] for x in result.data["context_pack"]["candidate_sources"]]
    assert all("auth.db" not in p and "devpilot.db" not in p and "outputs/" not in p and "node_modules/" not in p for p in paths)
    registry=json.loads((ROOT/'.devpilot/docs_governance/source_registry.json').read_text(encoding='utf-8'))
    registered={x['path'] for x in registry['documents']}
    assert all(p in registered for p in paths)

def test_context_pack_v2_missing_or_irrelevant_query_returns_insufficient_evidence_without_claims():
    result=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="requirements",query="zzzzuniquetermthatdoesnotexist",as_of_date=date(2026,8,29))).build()
    assert result.ok is True
    assert result.data["summary"]["status"] == "insufficient-evidence"
    assert result.data["summary"]["sources_total"] == 0
    assert result.data["context_pack"]["citations"] == []

def test_context_pack_v2_stale_source_is_excluded(tmp_path):
    policy=json.loads((ROOT/'.devpilot/rag/context_pack_v2_policy.json').read_text(encoding='utf-8'))
    assert policy['selection']['stale_source_action']=='exclude'
    synthetic=tmp_path/'stale.md'; synthetic.write_text('updated: "2020-01-01"\nold evidence',encoding='utf-8')
    freshness=_freshness(synthetic,{"fragment":'updated: "2020-01-01"\nold evidence'},date(2026,8,29),730)
    assert freshness['status']=='stale' and freshness['age_days']>730
    result=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="requirements",as_of_date=date(2026,8,29))).build()
    assert result.ok
    assert all(x['freshness']['status'] != 'stale' for x in result.data['context_pack']['sources'])

def test_context_pack_v2_step_binding_and_model_authority_remain_separate():
    result=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="requirements",as_of_date=date(2026,8,29))).build()
    pack=result.data['context_pack']
    assert pack['agent']['role_id']=='requirements'
    assert pack['agent']['runtime_agent_id']=='requirements.agent'
    boundary=json.loads((ROOT/'.devpilot/agents/agent_runtime_boundary.json').read_text(encoding='utf-8'))
    assert boundary['tool_authority']['model_route_can_grant_tool_permission'] is False
    assert boundary['tool_authority']['agent_role_can_approve'] is False


def test_context_pack_v2_application_service_and_secret_redaction():
    service=ApplicationService(ROOT)
    result=service.settings_rag_context(step_id="requirements")
    assert result.ok is True and result.data["summary"]["sources_total"] >= 1
    secretish=ContextPackV2Builder(ROOT,ContextPackV2Options(step_id="requirements",query="api_key=" + "sk-" + "test-" + "should-not-survive",as_of_date=date(2026,8,29))).build()
    assert secretish.ok is True
    serialized=json.dumps(secretish.data,ensure_ascii=False)
    redacted_marker="sk-" + "test-" + "should-" + "not-" + "survive"
    assert redacted_marker not in serialized
