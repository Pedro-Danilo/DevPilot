from __future__ import annotations
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
import pytest
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validation.project_profile import ProjectFacts, Waiver, project_hash, successor_of

ROOT=Path(__file__).resolve().parents[1]


def facts(ai=False, scopes=()):
    return ProjectFacts('web-test',1,ai,tuple(scopes),('intake-001',),devtool_uses_llm=True)


def result(f):
    return ArtifactProfileRegistry(ROOT).evaluate_project_applicability(f)


def test_conventional_web_mip_required_and_miasi_na_with_rationale():
    value=result(facts())
    assert value['standards'][0]['applicability']=='REQUIRED'
    assert value['standards'][1]['applicability']=='NOT_APPLICABLE'
    assert all(a['applicability']=='NOT_APPLICABLE' and a['rationale'] for a in value['artifacts'])
    assert value['owner_approval_granted'] is False
    assert value['catalog_fallback_used'] is False


def test_ai_agent_tool_write_needs_tool_agent_human_approval_cards():
    value=result(facts(True, ('agent','tool_write','model_runtime')))
    m={a['artifact_type']:a['applicability'] for a in value['artifacts']}
    assert value['standards'][1]['applicability']=='REQUIRED'
    assert m['miasi-agent-card']==m['miasi-tool-card']==m['miasi-human-approval-card']=='REQUIRED'
    assert m['miasi-policy-card']=='REQUIRED'
    assert value['external_egress']=='DENIED'


def test_agent_without_write_human_approval_not_required():
    m={a['artifact_type']:a['applicability'] for a in result(facts(True,('agent',)))['artifacts']}
    assert m['miasi-human-approval-card']=='NOT_APPLICABLE'
    assert m['miasi-agent-card']=='REQUIRED'


def test_unknown_never_automatic_na():
    f=ProjectFacts('web',1,None)
    value=result(f)
    assert value['standards'][1]['applicability']=='REVIEW_REQUIRED'
    assert all(a['applicability']=='REVIEW_REQUIRED' for a in value['artifacts'])


def test_llm_used_by_developer_does_not_make_product_agentic():
    a=result(facts(False));b=result(replace(facts(False),devtool_uses_llm=False))
    assert a['standards'][1]['applicability']==b['standards'][1]['applicability']=='NOT_APPLICABLE'


@pytest.mark.parametrize('kwargs,error',[
    ({'product_has_ai':True,'confirmed_scopes':()},'EVIDENCE_REQUIRED'),
    ({'product_has_ai':False,'confirmed_scopes':('agent',)},'CONTRADICTORY'),
    ({'product_has_ai':None,'confirmed_scopes':('tool',)},'UNCONFIRMED'),
    ({'product_has_ai':True,'confirmed_scopes':('invented',)},'UNKNOWN_COMPONENT'),
])
def test_inconsistent_facts_rejected(kwargs,error):
    with pytest.raises(ValueError,match=error):
        ProjectFacts('a',1,kwargs['product_has_ai'],kwargs['confirmed_scopes'],('e',))


def waiver(control='recommended-diagram', days=10):
    return Waiver(control,'Reason','Low risk',('manual review',),'owner',(date.today()+timedelta(days=days)).isoformat(),'risk-change','waiver-1')


def test_waiver_is_review_only_not_automatic_exemption():
    value=ArtifactProfileRegistry(ROOT).evaluate_project_applicability(facts(), waivers=(waiver(),))
    assert value['waiver_reviews'][0]['decision']=='REVIEW_REQUIRED'


@pytest.mark.parametrize('control',['security-threat-model','human-approval','privacy','legal-terms','policy-card','mipsoftware','miasi'])
def test_waiver_cannot_bypass_security_or_legal(control):
    with pytest.raises(ValueError,match='NON_WAIVABLE'): result_with_waiver(waiver(control))


def result_with_waiver(w):
    return ArtifactProfileRegistry(ROOT).evaluate_project_applicability(facts(), waivers=(w,))


def test_expired_waiver_rejected():
    with pytest.raises(ValueError,match='EXPIRED'):result_with_waiver(waiver(days=-1))


def test_frozen_successor_preserves_snapshot_and_lineage():
    prior=replace(facts(), state='FROZEN')
    before=project_hash(prior)
    newer=replace(prior,revision=2,state='DRAFT',supersedes_revision=1,previous_frozen_sha256=before)
    assert successor_of(prior,newer).revision==2
    assert project_hash(prior)==before


def test_frozen_in_place_rejected():
    prior=replace(facts(), state='FROZEN')
    with pytest.raises(ValueError, match='FROZEN_REVISION_REUSED'):
        successor_of(prior,replace(prior,state='DRAFT',supersedes_revision=None))


def test_frozen_forged_parent_rejected():
    prior=replace(facts(),state='FROZEN')
    newer=replace(prior,revision=2,state='DRAFT',supersedes_revision=1,previous_frozen_sha256='a'*64)
    with pytest.raises(ValueError,match='FROZEN_LINEAGE_INVALID'):successor_of(prior,newer)


def test_existing_profile_selection_unchanged():
    r=ArtifactProfileRegistry(ROOT)
    assert r.select(ROOT/'docs/00_product/product_vision.md').id=='product-vision'
    assert r.status().ok
