"""UX01-B: real authoring/storage boundary with offline model transport only."""
from copy import deepcopy
import json
from pathlib import Path
import threading

import pytest

from devpilot_core.application import pre_code_wizard_service as pre
from devpilot_core.application.r03_04_local_authoring import R0304LocalAuthoring
from devpilot_core.application.r03_04_quality_contract import (
    candidate_quality, export_candidate_handoff, offline_section_proposal,
    logical_sha256, markdown_sections,
)
from test_mp132_r03_04_c02_p5_flow import TECH, ADR, ARCH, LocalModel

SOURCES = {
    'product-vision': 'Empresa unipersonal de cuidado personal, ventas locales.',
    'scope': 'Inventario y ventas MVP; agentes advisory-only. Sin publicación autónoma.',
    'requirements': 'RF-001 venta y stock atómicos. RNF-001 local-first; aprobación humana.',
}

@pytest.fixture
def pipeline(tmp_path, monkeypatch):
    project = tmp_path/'isolated-project'
    (project/'.devpilot').mkdir(parents=True)
    (project/'.devpilot/project.yaml').write_text(
        'project_name: Anonymized fixture\nbusiness_need: Inventario y ventas locales.\n',encoding='utf-8')
    row = {'mode':'LOCAL_MODEL','status':'DRAFT','approval_id':None,'content':ARCH,
           'content_sha256':logical_sha256(ARCH),'derivation':{'model':'gemma3:4b','generation_epoch':'epoch-1'}}
    state = {'stages':{'architecture':row},'r03_04_authoring':{}}
    svc = object.__new__(pre.PreCodeWizardApplicationService)
    svc.root = tmp_path
    svc.technology_authoring = R0304LocalAuthoring(tmp_path)
    svc._stage_by_id = {}
    for key,text in SOURCES.items():
        path = project/'docs'/f'{key}.md'
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(text.encode())
        state['stages'][key] = {'status':'FROZEN','approved_sha256':logical_sha256(text)}
        svc._stage_by_id[key] = {'relative_path':f'docs/{key}.md'}
    monkeypatch.setattr(type(svc),'_context',lambda self:('isolated',project))
    monkeypatch.setattr(type(svc),'_load_state',lambda self,*args:state)
    monkeypatch.setattr(type(svc),'_write_state',lambda self,*args:state.update(args[-1]))
    monkeypatch.setattr(type(svc),'_current_stage',lambda self,*args:{'stage_id':'architecture'})
    monkeypatch.setattr(type(svc),'_append_trace',lambda *a,**k:None)
    def save(self,**kwargs):
        row['content'] = kwargs['content']
        row['content_sha256'] = logical_sha256(kwargs['content'])
        return self._pass('save','PASS','Fixture lifecycle boundary',{'plan_invalidated':True})
    monkeypatch.setattr(type(svc),'save_draft',save)
    responses = [TECH,ADR]
    calls = []
    def adapter(self,adapter,model,**kwargs):
        calls.append(model)
        return LocalModel(responses.pop(0))
    monkeypatch.setattr(R0304LocalAuthoring,'_local_adapter',adapter)
    def action(name,**kwargs):
        return svc.technology_action(action=name,actor='owner',actor_role='owner',
            session_principal='owner',effective_roles=['owner'],workspace_scopes=['isolated'],
            model='gemma3:4b',**kwargs)
    return svc,state,row,action,responses,calls,project


def test_generation_quality_export_offline_and_restart(pipeline):
    svc,state,row,action,responses,calls,project = pipeline
    original_sources = {p:p.read_bytes() for p in (project/'docs').glob('*.md')}
    assert action('generate_options').ok
    first = deepcopy(state['r03_04_authoring']['technology'])
    assert action('generate_options').ok and len(calls)==1
    assert first['quality']['current']['quality_level']=='REVIEW_REQUIRED'
    result = action('export_handoff',artifact_kind='technology_options')
    assert result.ok, result.message
    packet = result.data['handoff']
    proposal = offline_section_proposal(packet,section_id='recomendacion-razonada',
        replacement='Comparar mantenimiento y rollback con RF-001; costos UNKNOWN, decisión pendiente del Owner.')
    before = {s['section_id']:s['body_sha256'] for s in packet['section_map']}
    after = {s['section_id']:s['body_sha256'] for s in markdown_sections(proposal['markdown'])}
    assert [key for key in before if before[key]!=after[key]]==['recomendacion-razonada']
    assert proposal['generation_epoch']=='epoch-1'
    assert proposal['parent_candidate_id']==first['candidate_id']
    assert not proposal['external_api_used'] and not proposal['professional_reviewed']
    assert R0304LocalAuthoring(svc.root).bound_candidate('isolated',first)==TECH.strip()
    assert all(p.read_bytes()==blob for p,blob in original_sources.items())


def test_incomplete_options_preserved_for_repair_not_fabricated(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    responses[0]='# Technology Options\n## Opción T1 — Única\nSolo Python.\n'
    assert action('generate_options').ok
    tech=state['r03_04_authoring']['technology']
    assert tech['content'].count('## Opción')==1
    assert tech['quality']['current']['quality_level']=='REVIEW_REQUIRED'
    assert action('export_handoff',artifact_kind='technology_options').ok
    assert not action('select_option',option_id='T1').ok
    assert len(calls)==1


@pytest.mark.parametrize('mutation',['source','sha','epoch','architecture'])
def test_stale_inputs_fail_before_inference(pipeline,mutation):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    kwargs={}
    if mutation=='source': (project/'docs/scope.md').write_text('Drift',encoding='utf-8')
    elif mutation=='sha': kwargs['expected_sha256']='0'*64
    elif mutation=='epoch': kwargs['generation_epoch']='old-epoch'
    else:
        row['content']+='\nOwner update.\n'
        row['content_sha256']=logical_sha256(row['content'])
    result=action('select_option',option_id='T1',**kwargs)
    assert not result.ok and len(calls)==1


def test_t2_with_t1_adr_is_preserved_but_cannot_reconcile(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    assert action('select_option',option_id='T2').ok
    assert action('generate_adr').ok
    original=row['content']
    assert not action('reconcile').ok
    assert row['content']==original and len(calls)==2
    assert state['r03_04_authoring']['adr']['quality']['current']['structural_disposition']=='BLOCK'


def test_owner_revision_keeps_before_owner_and_requires_new_selection(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    before=deepcopy(state['r03_04_authoring']['technology']['quality']['before_owner'])
    assert action('select_option',option_id='T1').ok
    assert not action('select_option',option_id='T2').ok
    assert action('owner_revise_options',content=TECH.replace('SQLite local','SQLite revisado')).ok
    tech=state['r03_04_authoring']['technology']
    assert tech['quality']['before_owner']==before
    assert tech['quality']['current']['owner_phase']=='after_owner'
    assert state['r03_04_authoring']['selected_option_id'] is None
    assert not action('generate_adr').ok and len(calls)==1


def test_explicit_t2_successor_and_adr_exact_lineage(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    assert action('select_option',option_id='T1').ok
    assert action('select_option',option_id='T2',successor=True).ok
    responses[0]=ADR.replace('opción T1 elegida','opción T2 elegida')
    assert action('generate_adr').ok
    assert action('reconcile').ok
    assert action('reconcile').ok
    assert len(calls)==2


def test_concurrent_action_rejected_without_inference(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    with pre._TECH_ACTION_LOCK:
        denied=action('generate_options')
    assert not denied.ok and not calls
    assert 'UX01_B_ACTION_IN_PROGRESS' in [f.id for f in denied.findings]


@pytest.mark.parametrize('domain',['sales','training'])
def test_second_domain_and_eol_offline_contract(domain):
    sources=SOURCES if domain=='sales' else {
        'product-vision':'Centro local de formación.', 'scope':'Inscripción y cursos.',
        'requirements':'RF-001 inscripción consistente. RNF-001 uso local-first.'}
    hashes={key:logical_sha256(value) for key,value in sources.items()}
    q=candidate_quality('adr',ADR,frozen=sources,hashes=hashes,candidate_id='c1',epoch='e1',
        actor='offline-fixture',selected_option_id='T1',selected_option_sha256='a'*64)
    packet=export_candidate_handoff(q,ADR.replace('\n','\r\n'))
    assert packet['quality_level']=='REVIEW_REQUIRED' and not packet['professional_reviewed']
    with pytest.raises(ValueError,match='TARGET_DENY'):
        offline_section_proposal(packet,section_id='decision',replacement='Elige T2.')


def test_duplicate_stack_names_and_shallow_adr_have_section_findings():
    hashes={k:logical_sha256(v) for k,v in SOURCES.items()}
    duplicate=TECH.replace('Python, PostgreSQL e interfaz web.','SQLite, Python, interfaz web móvil.')
    q=candidate_quality('technology_options',duplicate,frozen=SOURCES,hashes=hashes,
                        candidate_id='dup',epoch='e',actor='fixture')
    assert 'UX01_A_TECH_DUPLICATE_STACK' in {f['id'] for f in q['current']['findings']}
    q=candidate_quality('adr',ADR,frozen=SOURCES,hashes=hashes,candidate_id='adr',epoch='e',actor='fixture')
    assert any(f['section_id']=='reversibilidad' for f in q['current']['findings'])


def test_handoff_api_dto_and_dispatch():
    from test_r03_04_p8_action_dispatch import _PreCodeSpy,_facade_with_spy
    from devpilot_core.application.services import _operation_dispatch
    from devpilot_core.interfaces.api.routers.guided_sdlc import TechnologyActionBody
    request=TechnologyActionBody(action='export_handoff',artifact_kind='adr',
                                expected_sha256='a'*64,generation_epoch='epoch-1')
    spy=_PreCodeSpy()
    _operation_dispatch(_facade_with_spy(spy))['guided_sdlc.pre_code.technology_action'](request.model_dump())
    assert spy.calls[0]['artifact_kind']=='adr'
    assert spy.calls[0]['generation_epoch']=='epoch-1'
    assert spy.calls[0]['expected_sha256']=='a'*64


def test_not_applicable_requires_owner_reason_and_no_selection(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert not action('adr_not_applicable',content='No aplica').ok
    assert action('adr_not_applicable',content='No existe una decisión técnica material nueva; se conserva la operación local sin elegir un stack.').ok
    assert svc._technology_binding_valid(state,row)
    assert not calls and not state['r03_04_authoring'].get('adr')
    row['content_sha256']='0'*64
    assert not svc._technology_binding_valid(state,row)


def test_same_content_successor_has_new_identity_and_clears_decision(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    first=deepcopy(state['r03_04_authoring']['technology'])
    assert action('select_option',option_id='T1').ok
    responses[0]=TECH
    assert action('generate_options',successor=True).ok
    second=state['r03_04_authoring']['technology']
    assert second['candidate_sha256']==first['candidate_sha256']
    assert second['candidate_id']!=first['candidate_id']
    assert second['parent_candidate_id']==first['candidate_id']
    assert state['r03_04_authoring']['selected_option_id'] is None
    receipts=list((svc.root/'outputs/mp132_r03_04/isolated').glob('*attempt*.json'))
    assert len(receipts)==2


def test_export_records_the_actual_owner_choice(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    assert action('select_option',option_id='T2').ok
    packet=action('export_handoff',artifact_kind='technology_options').data['handoff']
    assert packet['owner_decision']['option_id']=='T2'
    assert packet['owner_decision']['sha256']==state['r03_04_authoring']['technology']['candidate_sha256']


def test_new_source_context_needs_explicit_successor(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    row['content']+='\nNueva revisión Owner.\n'
    row['content_sha256']=logical_sha256(row['content'])
    assert not action('generate_options').ok and len(calls)==1


def test_architecture_change_during_inference_never_overwrites_state(pipeline,monkeypatch):
    svc,state,row,action,responses,calls,project=pipeline
    class ConcurrentModel:
        def generate(self,request):
            row['content']+='\nConcurrent Owner edit.\n'
            row['content_sha256']=logical_sha256(row['content'])
            return LocalModel(TECH).generate(request)
    monkeypatch.setattr(R0304LocalAuthoring,'_local_adapter',lambda *a,**k:ConcurrentModel())
    result=action('generate_options')
    assert not result.ok and not state['r03_04_authoring']
    assert 'Concurrent Owner edit' in row['content']
    assert list((svc.root/'outputs/mp132_r03_04/isolated').glob('cand-*.md'))


def test_architecture_segment_successor_preserves_epoch_and_one_call_per_action(tmp_path):
    from test_mp132_r03_03_architecture import ROOT, sources, context, body, FakeAdapter
    from devpilot_core.application.r03_03_architecture import generate_local_architecture
    profile=tmp_path/'.devpilot/gsdlc/architecture_authoring_profile.json'
    profile.parent.mkdir(parents=True)
    profile.write_bytes((ROOT/'.devpilot/gsdlc/architecture_authoring_profile.json').read_bytes())
    facts=sources(); ctx=context(facts); ctx['truncated_stages']=['requirements']
    ctx['business_need']='Ventas locales con inventario transaccional.'
    model=FakeAdapter(body())
    args=dict(workspace_id='isolated',project_name='Fixture',context=ctx,upstream=facts,
              model='qwen2.5:3b-instruct',adapter=model)
    for number in range(10):
        result=generate_local_architecture(tmp_path,**args)
        assert model.calls==number+1
    quality=result['provenance']['ux01_quality']
    assert quality['before_owner']['owner_phase']=='before_owner'
    assert not quality['before_owner']['professional_reviewed']
    original=result['provenance']['candidate_sha256']
    ctx['generation_epoch']='epoch-successor'
    ctx['parent_candidate_id']=original
    for number in range(10):
        result=generate_local_architecture(tmp_path,allow_successor=True,**args)
        assert model.calls==number+11
    assert result['provenance']['ux01_quality']['current']['generation_epoch']=='epoch-successor'
    assert result['provenance']['ux01_quality']['current']['parent_candidate_id']==original
    folder=tmp_path/'outputs/mp132_r03_03/isolated'
    assert len(list(folder.glob('epoch-*.json')))==1
    assert len(list(folder.glob('seg-*/candidate.json')))==2


def test_b0_large_prompt_is_bounded_and_hash_traced():
    from devpilot_core.application.r03_04_local_authoring import technology_prompt
    b0='RF-001 ventas y stock; aprobación humana.\n'*100
    prompt=technology_prompt('Fixture',ARCH,SOURCES,business_need=b0)
    assert len(prompt)<=13000
    assert logical_sha256(b0) in prompt
    assert 'EXTRACTO' in prompt


def test_durable_activity_survives_reload(pipeline):
    svc,state,row,action,responses,calls,project=pipeline
    assert action('generate_options').ok
    activity=R0304LocalAuthoring(svc.root).activity('isolated')
    assert activity[0]['status']=='COMPLETE'
    assert activity[0]['calls_started']==1
    assert activity[0]['elapsed_ms']>=0
    assert 'content' not in activity[0]
