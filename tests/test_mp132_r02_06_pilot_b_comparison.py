"""R02-06 focal: B0 binding, D/L real-route abstraction, failure modes, idempotency."""
from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from devpilot_core.generation import pilot_b_comparison as mod
from devpilot_core.generation.pilot_b_comparison import PilotBComparisonService, ComparisonBlock
from devpilot_core.interfaces.api.security import API_ROUTE_POLICIES

NEED='Necesitamos administrar ventas de productos de cuidado personal y controlar existencias locales.'


def fixture(tmp_path:Path,monkeypatch) -> tuple[Path,Path,PilotBComparisonService]:
    platform=tmp_path/'platform';platform.mkdir()
    workspace=tmp_path/'workspace'/'admon_empresa_unipersonal_con_agentes';meta=workspace/'.devpilot';meta.mkdir(parents=True)
    (meta/'project.yaml').write_text('schema_version: "1.0"\nproject_id: admon_empresa_unipersonal_con_agentes\nproject_name: "Pilot B"\n'
        'technology_decision_status: deferred-to-architecture\n'
        f'business_need: "{NEED}"\n',encoding='utf-8')
    (meta/'workspace-registration.json').write_text(json.dumps({'workspace_id':'admon_empresa_unipersonal_con_agentes',
        'project_id':'admon_empresa_unipersonal_con_agentes','root_path':str(workspace.resolve())}),encoding='utf-8')
    target=platform/'outputs/runtime/active_workspace_registry.json';target.parent.mkdir(parents=True)
    target.write_text(json.dumps({'active_workspace_id':'admon_empresa_unipersonal_con_agentes',
        'workspaces':[{'workspace_id':'admon_empresa_unipersonal_con_agentes','path':str(workspace.resolve())}]}),encoding='utf-8')
    monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS',str(tmp_path/'workspace'))
    cfg=SimpleNamespace(external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434')
    monkeypatch.setattr(mod.ProviderRegistry,'load',lambda *_:SimpleNamespace(semantic_valid=True,get=lambda _name:cfg))
    return platform,workspace,PilotBComparisonService(platform)

class LocalFake:
    calls:list[str]=[]
    wrong_ref=False
    def __init__(self,**_kwargs):pass
    def health(self):return SimpleNamespace(ok=True,data={'models':['qwen2.5:3b-instruct']})
    def _post_json(self,_path,payload,*,task):
        self.calls.append(payload['model'])
        import re
        ref=re.search(r'Ref exacta: (project\.yaml:sha256:[0-9a-f]{64})',payload['prompt']).group(1)
        ref='source:incorrect-ref' if self.wrong_ref else ref
        return SimpleNamespace(ok=True,metadata={'response':json.dumps({'title':'Visión Pilot B','content':'Propuesta basada en la necesidad Owner. La funcionalidad concreta requiere una decisión y validación de negocio.','evidence_refs':[ref]}),
          'prompt_eval_count':24,'eval_count':32})


def generate_two(tmp_path,monkeypatch,stage='vision'):
    p,w,s=fixture(tmp_path,monkeypatch);LocalFake.calls.clear();LocalFake.wrong_ref=False
    s=PilotBComparisonService(p,adapter_factory=LocalFake)
    d=s.generate(stage=stage,route='deterministic')
    l=s.generate(stage=stage,route='local-model',model='qwen2.5:3b-instruct',execute=True)
    return p,w,s,d,l


def test_vision_d_l_bound_to_same_pilot_b_without_source_writes(tmp_path,monkeypatch):
    p,w,s,d,l=generate_two(tmp_path,monkeypatch)
    assert d['source_sha256']==l['source_sha256']
    assert d['input_sha256']==l['input_sha256']
    assert d['candidate']['origin']['provider_class']=='deterministic'
    assert l['candidate']['origin']['provider_class']=='local-model'
    assert l['observed']['provider']=='ollama' and l['observed']['network_calls']==2
    assert LocalFake.calls==['qwen2.5:3b-instruct']
    assert not (w/'docs').exists() and not (w/'outputs').exists()
    assert s.status(stage='vision')['review'] is None


@pytest.mark.parametrize('stage',['vision','scope','requirements'])
def test_owner_review_persists_across_service_restart(tmp_path,monkeypatch,stage):
    p,w,s,d,l=generate_two(tmp_path,monkeypatch,stage=stage)
    reason='Comparé la referencia D y el texto L. D solo reproduce el contexto inicial, mientras L propone revisión humana pendiente.'
    outcome=s.select(stage=stage,candidate_id=l['candidate']['candidate_id'],classification='REDUCED',reason=reason,
        owner_id='owner-1',expected_input_sha256=d['input_sha256'])
    assert outcome['freeze_authority'] is False and outcome['approved_document'] is False
    assert PilotBComparisonService(p,adapter_factory=LocalFake).status(stage=stage)['review']['selected_candidate_id']==l['candidate']['candidate_id']
    assert s.select(stage=stage,candidate_id=l['candidate']['candidate_id'],classification='REDUCED',reason=reason,
        owner_id='owner-1',expected_input_sha256=d['input_sha256'])['replayed'] is True
    with pytest.raises(ComparisonBlock,match='OWNER_REVIEW_TERMINAL_CONFLICT'):
        s.select(stage=stage,candidate_id=d['candidate']['candidate_id'],classification='REDUCED',reason=reason,
            owner_id='owner-1',expected_input_sha256=d['input_sha256'])


def test_real_model_needs_explicit_authorization_no_silent_fallback(tmp_path,monkeypatch):
    p,w,s=fixture(tmp_path,monkeypatch)
    with pytest.raises(ComparisonBlock,match='LOCAL_INFERENCE_OWNER_OPT_IN_REQUIRED'):
        s.generate(stage='vision',route='local-model',model='qwen2.5:3b-instruct',execute=False)
    assert s.status(stage='vision')['candidates']=={}


def test_real_offline_fail_closed_and_no_candidate(tmp_path,monkeypatch):
    p,w,s=fixture(tmp_path,monkeypatch)
    class Offline(LocalFake):
        def health(self):return SimpleNamespace(ok=False,data={})
    s=PilotBComparisonService(p,adapter_factory=Offline)
    with pytest.raises(ComparisonBlock,match='OLLAMA_UNAVAILABLE'):
        s.generate(stage='vision',route='local-model',model='qwen2.5:3b-instruct',execute=True)
    assert s.status(stage='vision')['candidates']=={}


def test_wrong_evidence_ref_is_rejected(tmp_path,monkeypatch):
    p,w,s=fixture(tmp_path,monkeypatch)
    LocalFake.wrong_ref=True
    try:
        s=PilotBComparisonService(p,adapter_factory=LocalFake)
        with pytest.raises(ComparisonBlock,match='UNSUPPORTED_REFERENCE_BLOCK'):
            s.generate(stage='scope',route='local-model',model='qwen2.5:3b-instruct',execute=True)
        assert s.status(stage='scope')['candidates']=={}
    finally:LocalFake.wrong_ref=False


def test_source_drift_blocks_review_and_old_receipts_preserved(tmp_path,monkeypatch):
    p,w,s,d,l=generate_two(tmp_path,monkeypatch)
    path=w/'.devpilot/project.yaml';path.write_text(path.read_text()+"# source changed\n")
    with pytest.raises(ComparisonBlock,match='INPUT_DRIFT_PRESERVE_IMMUTABLE_CANDIDATE'):
        s.status(stage='vision')
    assert (p/'outputs/mp132_r02_06/admon_empresa_unipersonal_con_agentes/vision/deterministic.json').exists()


def test_other_workspace_without_allowlist_never_accepted(tmp_path,monkeypatch):
    p,w,s=fixture(tmp_path,monkeypatch)
    monkeypatch.setenv('DEVPILOT_ALLOWED_WORKSPACE_ROOTS',str(tmp_path/'non-authorized'))
    with pytest.raises(ComparisonBlock,match='ACTIVE_PILOT_PATHGUARD_BLOCK'):
        s.status(stage='vision')


def test_no_replay_inference_after_candidate_persisted(tmp_path,monkeypatch):
    p,w,s,d,l=generate_two(tmp_path,monkeypatch)
    before=len(LocalFake.calls)
    assert s.generate(stage='vision',route='local-model',model='qwen2.5:3b-instruct',execute=True)['replayed']
    assert len(LocalFake.calls)==before


def test_equivalence_justification_cannot_be_auto_granted(tmp_path,monkeypatch):
    p,w,s,d,l=generate_two(tmp_path,monkeypatch)
    with pytest.raises(ComparisonBlock,match='EQUIVALENCE_REQUIRES_EXPLICIT_HUMAN_JUSTIFICATION'):
        s.select(stage='vision',candidate_id=l['candidate']['candidate_id'],classification='EQUIVALENT',
            reason='Confirmo que me parece un buen documento para iniciar.',owner_id='owner-1',expected_input_sha256=d['input_sha256'])


def test_review_cannot_select_missing_real_candidate_or_unrelated_id(tmp_path,monkeypatch):
    p,w,s=fixture(tmp_path,monkeypatch);d=s.generate(stage='requirements',route='deterministic')
    with pytest.raises(ComparisonBlock,match='BOTH_D_AND_REAL_LOCAL_CANDIDATES_REQUIRED'):
        s.select(stage='requirements',candidate_id=d['candidate']['candidate_id'],classification='REDUCED',
          reason='Solo una referencia no acredita una comparación de dos rutas reales.',owner_id='owner-1',expected_input_sha256=d['input_sha256'])


def test_wrong_active_b0_project_is_not_pilot_b(tmp_path,monkeypatch):
    p,w,s=fixture(tmp_path,monkeypatch)
    registry=p/'outputs/runtime/active_workspace_registry.json'
    obj=json.loads(registry.read_text());obj['active_workspace_id']='another-project'
    registry.write_text(json.dumps(obj))
    with pytest.raises(ComparisonBlock,match='R02_06_WRONG_ACTIVE_PILOT_B_ID'):
        s.status(stage='vision')


def test_api_security_catalog_requires_owner_human_session():
    import json
    root=Path(__file__).resolve().parents[1]
    catalog=json.loads((root/'.devpilot/identity/server_rbac_policy_catalog.json').read_text())
    for method,path in [('GET','/api/v1/settings/pilot-b/comparison'),('POST','/api/v1/settings/pilot-b/comparison/candidate'),('POST','/api/v1/settings/pilot-b/comparison/review')]:
        assert (method,path) in API_ROUTE_POLICIES
        rows=[r for r in catalog['route_policies'] if (r['method'],r['path'])==(method,path)]
        assert len(rows)==1 and rows[0]['allowed_roles']==['owner'] and rows[0]['human_session_required']
        assert rows[0]['legacy_token_allowed'] is False and rows[0]['deny_by_default']
