"""UX01-C additive read projection: no FROZEN writes or new authority."""
from pathlib import Path
import hashlib
from copy import deepcopy
import pytest

from devpilot_core.application.architecture_workbench_projection import project_documents


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture
def projection(tmp_path):
    arch={'status':'DRAFT','content':'# Architecture\nContenido completo.\n', 'derivation':{'generation_epoch':'e1'}}
    arch['content_sha256']=digest(arch['content'])
    auth={'technology':{'content':'# Opciones\nT1 y T2.','candidate_sha256':'a'*64},
          'adr':{'content':'# ADR\nDecisión T2.','candidate_sha256':'b'*64}}
    def render(**changes):
        args=dict(workspace_root=tmp_path,arch=arch,authoring=auth,bundle={},
                  architecture_path='docs/architecture.md',current=True,owner=True,
                  candidate_reader=lambda record:record['content'])
        args.update(changes)
        return project_documents(**args)
    return tmp_path,arch,auth,render


def test_three_distinct_complete_candidates_and_no_mutation(projection):
    root,arch,auth,render=projection
    before=deepcopy((arch,auth)); docs=render()
    assert set(docs)=={'architecture','technology_options','adr'}
    assert len(set(d['content'] for d in docs.values()))==3
    assert all(d['can_edit'] for d in docs.values())
    assert (arch,auth)==before and list(root.iterdir())==[]


@pytest.mark.parametrize('settings',[{'owner':False},{'current':False}])
def test_projection_cannot_grant_editing_without_owner_or_current_stage(projection,settings):
    *_,render=projection
    assert not any(d['can_edit'] for d in render(**settings).values())


def test_frozen_architecture_reads_verified_source_not_runtime_draft(projection):
    root,arch,auth,render=projection
    file=root/'docs/architecture.md';file.parent.mkdir();file.write_bytes(b'# Approved\nFull source.\n')
    arch.update(status='FROZEN',approved_sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    before=file.read_bytes(); result=render()['architecture']
    assert result['content']==before.decode() and result['source']=='docs/architecture.md'
    assert not result['can_edit'] and result['status']=='FROZEN' and file.read_bytes()==before


def test_frozen_source_drift_exposes_block_without_stale_content(projection):
    root,arch,auth,render=projection
    file=root/'docs/architecture.md';file.parent.mkdir();file.write_text('Changed')
    arch.update(status='FROZEN',approved_sha256='0'*64)
    result=render()['architecture']
    assert result['status']=='BLOCK' and result['content']=='' and not result['can_edit']


def test_materialized_companions_need_trusted_bundle_and_exact_hashes(projection):
    root,arch,auth,render=projection
    folder=root/'docs';folder.mkdir()
    for name,body in [('architecture.md','Approved arch'),('technology.md','Approved options'),('adr.md','Approved ADR')]:
        (folder/name).write_text(body,encoding='utf-8')
    arch.update(status='FROZEN',approved_sha256=digest('Approved arch'))
    bundle={'ready':True,'adrs':[{'adr_id':'TECH-OPTIONS','relative_path':'docs/technology.md','proposed_sha256':digest('Approved options')},
                                {'adr_id':'ADR-001','relative_path':'docs/adr.md','proposed_sha256':digest('Approved ADR')}]}
    docs=render(bundle=bundle)
    assert docs['adr']['content']=='Approved ADR' and docs['technology_options']['content']=='Approved options'
    assert all(d['status']=='FROZEN' and not d['can_edit'] for d in docs.values())
    bundle['adrs'][1]['proposed_sha256']='0'*64
    assert render(bundle=bundle)['adr']['status']=='BLOCK'
    assert render(bundle={'ready':False})['adr']['status']=='REVIEW_REQUIRED'


def test_missing_documents_and_bad_candidate_receipt_are_explicit(projection):
    root,arch,auth,render=projection
    auth.clear(); arch.update(status='MISSING',content='')
    assert all(d['status']=='SIN_GENERAR' for d in render().values())
    auth['technology']={'candidate_sha256':'0'*64}
    def broken(_): raise ValueError('CANDIDATE_HASH_DRIFT')
    assert render(candidate_reader=broken)['technology_options']['content']==''
    assert render(candidate_reader=broken)['technology_options']['status']=='BLOCK'


def test_read_projection_rejects_path_outside_workspace(projection):
    root,arch,auth,render=projection
    arch.update(status='FROZEN',approved_sha256='0'*64)
    assert render(architecture_path='../outside.md')['architecture']['status']=='BLOCK'


def test_status_exposes_new_document_read_projection_only_in_authenticated_workspace_scope(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from devpilot_core.application.pre_code_wizard_service import PreCodeWizardApplicationService
    svc=object.__new__(PreCodeWizardApplicationService)
    svc.root=tmp_path
    svc._stage_by_id={'architecture':{'relative_path':'docs/architecture.md'}}
    svc.technology_authoring=SimpleNamespace(activity=lambda workspace:[],bound_candidate=lambda *args:'')
    state={'stages':{'architecture':{'status':'MISSING','derivation':{}}}}
    monkeypatch.setattr(type(svc),'_context',lambda self:('isolated',tmp_path))
    monkeypatch.setattr(type(svc),'_load_state',lambda *args:state)
    monkeypatch.setattr(type(svc),'_projection',lambda *args:{'current_stage_id':'architecture','architecture_adr_bundle':{}})
    allowed=svc.status(effective_roles=['viewer'],workspace_scopes=['isolated'])
    docs=allowed.data['pre_code']['architecture_workbench_documents']
    assert len(docs)==3 and not any(d['can_edit'] for d in docs.values())
    denied=svc.status(effective_roles=['owner'],workspace_scopes=['other'])
    assert 'architecture_workbench_documents' not in denied.data['pre_code']
