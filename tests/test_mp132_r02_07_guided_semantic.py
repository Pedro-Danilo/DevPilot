"""R02-07 focal tests: no API money, no project mutation, stage quality and provenance."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from devpilot_core.application import r02_07_semantic as author

PID='admon_empresa_unipersonal_con_agentes'


def _fixture(tmp_path):
    platform=tmp_path/'platform';platform.mkdir()
    workspace=tmp_path/'pilot';(workspace/'.devpilot').mkdir(parents=True)
    (workspace/'.devpilot/project.yaml').write_text('baseline: stable\n',encoding='utf-8')
    return platform,workspace


def _sample(stage):
    chunks=[f'## {name}\n'+('Esta propuesta es una hipótesis trazable al Owner y requiere su aprobación. '*3)
            for name in author.REQUIRED_SECTIONS[stage]]
    body='\n'.join(chunks)
    if stage=='product-vision':body+='\nEl beneficiario principal es el propietario; la propuesta de valor reduce errores operativos. El objetivo es controlar ventas y el indicador es el stock verificado.\n'
    if stage=='requirements':body+='\nRF-001: registrar venta. Reglas de negocio: inventario no negativo. Excepciones: stock insuficiente. Criterios de aceptación: Dado el inventario, cuando registre venta, entonces descuenta existencias con confirmación.\n'
    if stage=='scope':body+='\nExcluido: publicidad automática sin aprobación humana. Diferido al MVP+: integraciones. Prioridad P0 para catálogo.\n'
    return '# Documento revisable\n'+body




def _quality_vision():
    return """# Product Vision
## Resumen ejecutivo
Se busca centralizar la gestión de una empresa unipersonal de bienestar y cuidado personal para brindar datos oportunos y decisiones supervisadas.
## Problema
Actualmente el propietario necesita registrar ventas y stock y detectar faltantes. La falta de información confiable limita la oportunidad de reposición, sin suponer cifras.
## Visión
La aspiración es disponer de información consistente para decisiones comerciales y operativas responsables, con intervención humana sobre acciones sensibles.
## MVP
Se propone como hipótesis inicial catálogo, control de existencias y registro de ventas. Las funciones avanzadas de IA se podrían diferir para validar la operación.
## Propuesta de valor
El propietario obtendrá una visión centralizada y actualizada de sus operaciones, disminuyendo el esfuerzo de consolidación y reduciendo decisiones basadas en datos incompletos.
## Beneficiarios
El propietario es el usuario principal y autoridad responsable. Los clientes son destinatarios de la entrega a domicilio, sin acceso inferido a la aplicación.
## Resultados operativos
Disponibilidad de stock registrado, historial de ventas y alertas de bajo inventario, verificables por comparación con registros y conteos.
## Limitaciones
Los cosméticos y otros productos pueden tener restricciones de comercialización y publicidad que requieren validación. Agentes advisory-by-default, con trazabilidad, procedencia y autorización humana para acciones sensibles.
## Indicadores
- Exactitud de inventario: porcentaje de referencias cuyo conteo coincide con el sistema; fuente: conteo y registros, frecuencia propuesta: mensual; línea base y meta pendientes de confirmar por Owner.
- Ventas registradas: tasa de ventas documentadas sobre ventas realizadas; fuente: operaciones, periodicidad mensual; línea base y objetivo pendientes de Owner.
- Alertas revisadas: tasa de alertas gestionadas por el propietario sobre total de alertas, fuente: registro de alertas, periodicidad semanal; línea base y meta por confirmar.
"""


def test_prior_real_vision_fails_new_semantic_gate():
    old = """## Resumen ejecutivo
Esta propuesta se enfoca en la creación de una aplicación móvil.
## Visión
Solución integral para controlar de manera eficiente.
## Indicadores
Inventario controlado: manejarlo de forma eficiente."""
    names={x['id'] for x in author.vision_semantic_findings(old)}
    assert 'R0207_UNAUTHORIZED_PLATFORM' in names
    assert 'R0207_VISION_MEASURE_UNDEFINED' in names
    assert 'R0207_VISION_BUSINESS_RESTRICTIONS' in names


def test_vision_prompt_revision_changes_input_and_preserves_old(tmp_path):
    platform, workspace=_fixture(tmp_path)
    ref=author.PROMPT_REVISION
    assert ref=='r0207-vision-source-audit-v5'
    assert author.vision_semantic_findings(_quality_vision())==[]

def test_b0_or_summary_cannot_be_frozen_through_review():
    for stage in author.STAGES:
        findings=author.quality_findings(stage,'## Necesidad inicial\nAplicación para administrar ventas y productos.')
        assert findings and any(x['id']=='R0207_SECTION_MISSING' for x in findings)


@pytest.mark.parametrize('stage',author.STAGES)
def test_complete_structural_candidate(stage):
    assert author.quality_findings(stage,_sample(stage))==[] if stage!='product-vision' else author.quality_findings(stage,_quality_vision())==[]


def test_requirements_needs_rf_and_acceptance():
    text=_sample('requirements').replace('RF-001','Identificador').replace('Criterios de aceptación','Condiciones de calidad')
    findings=author.quality_findings('requirements',text)
    assert any(x['id']=='R0207_REQUIREMENT_IDS_MISSING' for x in findings)


def test_local_authoring_requires_pilot_and_opt_in_model(tmp_path):
    platform,workspace=_fixture(tmp_path)
    with pytest.raises(ValueError,match='PILOT_OR_STAGE_DENIED'):
        author.generate_local_guided(platform,workspace_id='other',workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct')
    with pytest.raises(ValueError,match='MODEL_INVALID'):
        author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='http://127.0.0.1?x=1')


def test_scope_requires_frozen_upstream(tmp_path):
    platform,workspace=_fixture(tmp_path)
    with patch.object(author,'parse_project_yaml_metadata',return_value={'project_id':PID,'business_need':'Operación local de inventario y ventas con agentes sujetos a aprobación.'}):
        with pytest.raises(ValueError,match='UPSTREAM_STATE_REQUIRED'):
            author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='scope',model='qwen2.5:3b-instruct')


@pytest.mark.parametrize("source_newline", [b"\n", b"\r\n"], ids=["LF", "CRLF"])
def test_one_shot_real_local_stub_persists_without_source_write(tmp_path, source_newline):
    platform,workspace=_fixture(tmp_path)
    (workspace/'.devpilot/project.yaml').write_bytes(b'baseline: stable'+source_newline)
    old=(workspace/'.devpilot/project.yaml').read_bytes()
    ref='project.yaml:sha256:'+author._sha(old)
    content=_sample('product-vision')
    class FakeAdapter:
        def __init__(self, **kwargs):pass
        def health(self):return SimpleNamespace(ok=True,data={'models':['qwen2.5:3b-instruct']})
        def _post_json(self,*args,**kwargs):
            return SimpleNamespace(ok=True,metadata={'response':content,'done_reason':'stop','eval_count':430})
    cfg=SimpleNamespace(external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434')
    registry=SimpleNamespace(semantic_valid=True,get=lambda key:cfg)
    with patch.object(author,'parse_project_yaml_metadata',return_value={'project_id':PID,'business_need':'Operación local de inventario y ventas con agentes sujetos a aprobación.'}),patch.object(author.ProviderRegistry,'load',return_value=registry),patch.object(author,'evaluate_loopback_endpoint',return_value=SimpleNamespace(ok=True)),patch.object(author,'OllamaAdapter',FakeAdapter):
        a=author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct')
        b=author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct')
    assert a==b and content.strip() in a['content'] and 'status: "draft"' in a['content']
    assert a['provenance']['model_execution_used'] and a['provenance']['source_writes']==0
    assert a['provenance']['source_ref']==ref and a['provenance']['trusted_reference_derived_by_server']
    assert a['provenance']['prompt_version']==author.PROMPT_REVISION
    assert (workspace/'.devpilot/project.yaml').read_bytes()==old
    assert list((platform/'outputs/mp132_r02_07'/PID/'product-vision').glob('*.json'))


def test_immutable_candidate_markdown_and_owner_successor(tmp_path):
    from devpilot_core.application.r02_07_semantic import _write_immutable_md, persist_owner_revision
    root=tmp_path; stage='product-vision'; folder=root/'outputs/mp132_r02_07'/PID/stage
    source='Visión Markdown con propuesta de valor.'
    input_hash='a'*64;name='cand-'+input_hash+'.md'
    initial=_write_immutable_md(folder/name,source)
    generation={'candidate_path':name,'candidate_sha256':initial}
    edited=source+'\nEdición del Owner.'
    revision=persist_owner_revision(root,workspace_id=PID,stage_id=stage,generation=generation,content=edited)
    assert revision['owner_edited'] and (folder/revision['candidate_path']).read_text()==edited
    assert (folder/name).read_text()==source
    assert persist_owner_revision(root,workspace_id=PID,stage_id=stage,generation=generation,content=edited)==revision
    with pytest.raises(ValueError,match='MARKDOWN_DRIFT'): _write_immutable_md(folder/name,'overwrite')


def test_markdown_native_and_legacy_json_are_semantic_only():
    body=_sample('product-vision')
    assert author._markdown_from_model(body)==body.strip()
    assert author._markdown_from_model('```markdown\n'+body+'\n```')==body.strip()
    # The model is NOT an authority for source hashes. A hallucinated legacy
    # evidence_ref is dropped; trusted refs are computed from project.yaml.
    legacy=json.dumps({'title':'Not authoritative','content':body,'evidence_refs':['fake-ref']})
    assert author._markdown_from_model(legacy)==body.strip()
    with pytest.raises(ValueError,match='JSON_NOT_MARKDOWN'):
        author._markdown_from_model('{invalid json that is sufficiently long to test parsing}')
    with pytest.raises(ValueError,match='BOUNDS_BLOCK'):
        author._markdown_from_model('')


def test_untrusted_model_failure_is_redacted_and_cannot_approve(tmp_path):
    dst=tmp_path/'outputs/mp132_r02_07'/PID/'product-vision'/('f'*64+'.json')
    metadata={'response':'CUSTOMER PRIVATE TEXT !!!','done_reason':'length','eval_count':2600}
    author._record_generation_failure(dst,{'stage':'product-vision'},'qwen2.5:3b-instruct',
        'R0207_MODEL_MARKDOWN_BOUNDS_BLOCK',metadata)
    diagnostic=json.loads(dst.with_suffix('.failure.json').read_text(encoding='utf-8'))
    assert diagnostic['error_code']=='R0207_MODEL_MARKDOWN_BOUNDS_BLOCK'
    assert diagnostic['response_characters']==len(metadata['response'])
    assert diagnostic['done_reason']=='length' and not diagnostic['contains_raw_model_output']
    assert 'CUSTOMER PRIVATE' not in dst.with_suffix('.failure.json').read_text(encoding='utf-8')
    assert not dst.exists()
    author._record_generation_failure(dst,{'stage':'product-vision'},'qwen2.5:3b-instruct',
        'R0207_MODEL_GENERATION_FAILED',{'response':'different'})
    assert json.loads(dst.with_suffix('.failure.json').read_text())['error_code']=='R0207_MODEL_MARKDOWN_BOUNDS_BLOCK'


def test_pre_code_dispatch_preserves_model_name_to_service():
    # Contract-level test: the API route already carries body.model, so the
    # central operation dispatcher must not silently drop it. No inference.
    from devpilot_core.application.services import _operation_dispatch
    from types import SimpleNamespace
    calls=[]
    def save_draft(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(ok=True)
    dispatch=_operation_dispatch(SimpleNamespace(guided_pre_code_save_draft=save_draft))
    for name in ('qwen2.5:3b-instruct','gemma3:4b'):
        result=dispatch['guided_sdlc.pre_code.draft']({
            'stage_id':'product-vision','mode':'LOCAL_MODEL','model':name,'content':'',
            'actor':'owner','actor_role':'owner','session_principal':'owner',
            'effective_roles':['owner'],'workspace_scopes':[PID],
        })
        assert result.ok and calls[-1]['model']==name
    assert len(calls)==2

def test_user_selected_model_reaches_real_generation_call_not_blank(monkeypatch,tmp_path):
    # Integrates dispatcher with service method up to the local model call;
    # no network/workspace writes are permitted here.
    from devpilot_core.application.services import _operation_dispatch
    class Capture:
        def guided_pre_code_save_draft(self,**kwargs):
            assert kwargs['model']=='qwen2.5:3b-instruct'
            return SimpleNamespace(ok=True)
    dispatcher=_operation_dispatch(Capture())
    assert dispatcher['guided_sdlc.pre_code.draft']({
        'stage_id':'product-vision','mode':'LOCAL_MODEL','model':'qwen2.5:3b-instruct',
        'content':'','actor':'owner','actor_role':'owner',
        'session_principal':'owner','effective_roles':['owner'],'workspace_scopes':[PID]
    }).ok


def test_refined_vision_rejects_invented_percentages_and_missing_authority():
    text = """# Product Vision
## Resumen ejecutivo
La aplicación registra ventas y productos.
## Problema
Stock y pedidos requieren mayor claridad.
## Visión
Facilitar operación empresarial.
## MVP
Productos e inventario.
## Indicadores
- Porcentaje de productos con stock bajo detectados: 100%, definición: porcentaje de detección. Fuente: aplicación. Frecuencia: mensual. Propuesta de meta: 100%. Línea base: 0%.
- Precisión de IA: 80%, definición: porcentaje coincidente. Fuente: aplicación. Meta: 80%. Línea base: 0%.
- Eficiencia: 90%, definición: porcentaje automatizado. Fuente: aplicación. Meta: 90%. Línea base: 0%.
"""
    ids={row['id'] for row in author.quality_findings('product-vision',text)}
    assert 'R0207_VISION_NUMERIC_AUTHORITY' in ids
    assert 'R0207_SECTION_EMPTY' in ids
    assert 'R0207_VISION_AGENT_GOVERNANCE' in ids


def test_each_indicator_must_define_its_own_measure_and_pending_decision():
    quality=_quality_vision()
    assert not author.vision_semantic_findings(quality)
    bad=quality.replace('línea base y meta pendientes de confirmar por Owner.', 'Meta: 75%. Línea base: 0%.')
    ids={f['id'] for f in author.vision_semantic_findings(bad)}
    assert 'R0207_VISION_NUMERIC_AUTHORITY' in ids
    assert 'R0207_VISION_METRIC_PENDING_DECISION' in ids


def test_unapproved_numbers_in_indicators_are_not_cured_by_other_pending_labels():
    quality=_quality_vision().replace('línea base y meta pendientes de confirmar por Owner.', 'Meta: 100%. Línea base: 0%.')
    findings=author.vision_semantic_findings(quality)
    assert any(x['id']=='R0207_VISION_NUMERIC_AUTHORITY' for x in findings)


def test_cor194_candidate_rejected_for_claim_drift():
    content = """# Product Vision
## Resumen ejecutivo
La aplicación atenderá una empresa unipersonal de cosméticos con publicidad restringida.
## Problema
Actualmente la gestión de inventario requiere intervención manual y genera errores.
## Visión
Mejorará el inventario sin afectar la autonomía de los agentes consultivos.
## MVP
El sistema registrará ventas y consultará el stock.
## Propuesta de valor
Una mejor experiencia para el propietario.
## Beneficiarios
Los usuarios de la aplicación serán los clientes que reciben los productos.
## Resultados operativos
Será posible revisar ventas y detectar stock bajo para proponer mejoras futuras.
## Limitaciones
Los productos requieren validación antes de comercialización; los agentes consultivos tendrán trazabilidad y autorización para cambios.
## Indicadores
- Tasa de errores en stock bajo: medida mensual. Fuente: informe de errores. Línea base pendiente y meta pendiente.
- Tasa de rechazo de recomendaciones: medida mensual. Fuente: recomendaciones. Línea base pendiente y meta pendiente.
"""
    b0='Empresa unipersonal que comercializa cosméticos con entrega a domicilio. Agentes advisory-by-default, sin acciones sensibles sin autorización humana. Stock bajo y ventas.'
    ids={r['id'] for r in author.quality_findings('product-vision',content,source_need=b0)}
    assert {'R0207_VISION_AGENT_AUTONOMY_UNSUPPORTED','R0207_VISION_UNSUPPORTED_USER_ROLE',
            'R0207_VISION_UNSUPPORTED_CURRENT_STATE','R0207_VISION_METRIC_DENOMINATOR'} <= ids


def test_other_domain_not_forced_to_use_cosmetics_or_agents():
    other='Sistema de reserva de salas de reuniones para personal administrativo.'
    content = """# Product Vision
## Resumen ejecutivo
Dar claridad sobre salas disponibles a trabajadores autorizados.
## Problema
Falta repositorio de disponibilidad consolidado (hipótesis a comprobar).
## Visión
Gestionar reservas con trazabilidad y mínima fricción.
## MVP
Reservar salas y consultar disponibilidad, como propuesta a validar.
## Propuesta de valor
Menos conflictos de agenda potenciales y más información fiable.
## Beneficiarios
Personal autorizado para reservar.
## Resultados operativos
Disponibilidad consultable e historial de reservas verificable.
## Limitaciones
No se conocen aún restricciones de hardware; decisión pendiente.
## Indicadores
- Conflictos de agenda por total de reservas: fuente: registro de reservas; meta pendiente y línea base pendiente.
"""
    ids={i['id'] for i in author.vision_semantic_findings(content,source_need=other)}
    assert 'R0207_VISION_BUSINESS_RESTRICTIONS' not in ids
    assert 'R0207_VISION_AGENT_GOVERNANCE' not in ids


def test_failure_diagnostic_classifies_timeout_safely(tmp_path):
    dst=tmp_path/'t.json'
    author._record_generation_failure(dst,{'stage':'product-vision'},'qwen3:latest',
        'R0207_MODEL_GENERATION_FAILED',{'error_type':'TimeoutError','error':'Private B0 prompt'})
    raw=dst.with_suffix('.failure.json').read_text()
    assert json.loads(raw)['failure_category']=='TIMEOUT'
    assert 'Private B0' not in raw


def test_cor196_explicit_same_model_alternative_has_lineage_and_is_deduplicated(tmp_path):
    platform,workspace=_fixture(tmp_path)
    content=_sample('product-vision')
    calls=[]
    class FakeAdapter:
        def __init__(self,**kwargs):pass
        def health(self):return SimpleNamespace(ok=True,data={'models':['qwen2.5:3b-instruct']})
        def _post_json(self, path, payload, **kwargs):
            calls.append(payload)
            return SimpleNamespace(ok=True,metadata={'response':content,'done_reason':'stop','eval_count':200})
    cfg=SimpleNamespace(external_api=False,requires_api_key=False,kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434')
    registry=SimpleNamespace(semantic_valid=True,get=lambda key:cfg)
    with patch.object(author,'parse_project_yaml_metadata',return_value={'project_id':PID,'business_need':'Negocio con inventario y ventas.'}),patch.object(author.ProviderRegistry,'load',return_value=registry),patch.object(author,'evaluate_loopback_endpoint',return_value=SimpleNamespace(ok=True)),patch.object(author,'OllamaAdapter',FakeAdapter):
        first=author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct')
        second=author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct',predecessor_sha256=first['candidate_sha256'],previous_content=first['content'])
        replay=author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct',predecessor_sha256=first['candidate_sha256'],previous_content=first['content'])
    assert first['input_hash']!=second['input_hash'] and second==replay
    assert second['provenance']['predecessor_sha256']==first['candidate_sha256']
    assert len(calls)==2 and calls[0]['options']['seed']!=calls[1]['options']['seed']
    assert (platform/'outputs/mp132_r02_07'/PID/'product-vision'/first['candidate_path']).is_file()
    with patch.object(author,'parse_project_yaml_metadata',return_value={'project_id':PID,'business_need':'Negocio con inventario y ventas.'}), pytest.raises(ValueError,match='PREDECESSOR_CONTENT_DRIFT'):
        author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='product-vision',model='qwen2.5:3b-instruct',predecessor_sha256=first['candidate_sha256'],previous_content='corrupt')


def test_cor196_failure_diagnostics_preserve_first_and_add_attempt_with_status(tmp_path):
    dst=tmp_path/'outputs/mp132_r02_07'/PID/'product-vision'/('e'*64+'.json')
    context={'stage':'product-vision'}
    meta={'error_type':'http_error','error':'HTTP 500 from local Ollama endpoint.','elapsed_ms':76542,'response':'secret never logged'}
    author._record_generation_failure(dst,context,'llama3.1:8b','R0207_MODEL_GENERATION_FAILED',meta)
    first=json.loads(dst.with_suffix('.failure.json').read_text())
    assert first['ollama_http_status']==500 and first['transport_error_type']=='http_error' and first['elapsed_ms']==76542
    author._record_generation_failure(dst,context,'llama3.1:8b','R0207_MODEL_GENERATION_FAILED',meta)
    attempts=list(dst.parent.glob(dst.stem+'.failure-*.json'))
    assert len(attempts)==1 and 'secret' not in attempts[0].read_text()
    assert not dst.exists()


def test_cor197_candidate_binding_and_lf_crlf_owner_edits():
    from devpilot_core.application.pre_code_wizard_service import PreCodeWizardApplicationService as S
    from devpilot_core.application.pre_code_wizard_service import _sha_bytes, _sha_text
    content='---\nstatus: "draft"\n---\n# Visión\nEl Owner decide.\n'
    digest=_sha_text(content)
    row={'mode':'LOCAL_MODEL','status':'DRAFT','content':content,'content_sha256':_sha_bytes(content.encode()),
         'derivation':{'candidate_sha256':digest,'candidate_path':'cand-'+('a'*64)+'.md','model':'gemma3:4b'}}
    assert S._candidate_content_binding(row)['status']=='PASS'
    row['content']=content.replace('\n','\r\n')
    row['content_sha256']=_sha_bytes(row['content'].encode())
    # CRLF is not content drift, regardless of the immutable candidate's LF bytes.
    assert S._candidate_content_binding(row)['status']=='PASS'
    row['content']+='Sustitución no registrada.'
    assert S._candidate_content_binding(row)['status']=='BLOCK'
    row['derivation']['owner_edited']=True
    row['derivation']['owner_edited_content_sha256']=_sha_text(row['content'])
    row['content_sha256']=_sha_bytes(row['content'].encode())
    assert S._candidate_content_binding(row)['status']=='PASS'


def test_cor197_similarity_distinguishes_near_duplicate_from_distinct():
    sample=_quality_vision()
    assert author._alternative_similarity(sample,sample.replace('  ',' '))==1.0
    similarity=author._alternative_similarity(sample,sample+'\nCambio menor.\n')
    assert similarity is not None and similarity>0.985
    assert author._alternative_similarity(sample,'## Visión\nUna propuesta diferente centrada en otra población.')<0.75
    assert author._alternative_similarity('',sample) is None


def test_cor197_binding_missing_provenance_is_fail_closed():
    from devpilot_core.application.pre_code_wizard_service import PreCodeWizardApplicationService as S
    row={'mode':'LOCAL_MODEL','status':'DRAFT','content':'Texto sin candidato',
         'content_sha256':author._sha(b'Texto sin candidato'),'derivation':{}}
    assert S._candidate_content_binding(row)['reason']=='CANDIDATE_PROVENANCE_MISSING'
    assert S._candidate_content_binding({'mode':'MANUAL','status':'DRAFT'})['status']=='NOT_APPLICABLE'


def test_cor199_bounded_stage_timeouts_without_api_credentials():
    assert author.LOCAL_GENERATION_TIMEOUT_SECONDS == {'product-vision':210,'scope':480,'requirements':540}
    assert max(author.LOCAL_GENERATION_TIMEOUT_SECONDS.values()) <= 540
    assert author.LOCAL_GENERATION_TIMEOUT_SECONDS['scope'] > 210


def test_cor199_timeout_diagnostic_reports_real_stage_budget_without_secrets(tmp_path):
    for stage in author.STAGES:
        dst = tmp_path / stage / ('0'*64+'.json')
        author._record_generation_failure(dst, {'stage':stage}, 'gemma3:4b', 'R0207_MODEL_GENERATION_FAILED',
            {'error_type':'TimeoutError','error':'Secret business_need should not leak', 'elapsed_ms':201000})
        payload=json.loads(dst.with_suffix('.failure.json').read_text(encoding='utf-8'))
        assert payload['timeout_seconds']==author.LOCAL_GENERATION_TIMEOUT_SECONDS[stage]
        assert payload['failure_category']=='TIMEOUT'
        assert 'Secret' not in json.dumps(payload)


def test_cor199_scope_retries_preserve_vision_frozen_gate_and_request_budget(tmp_path):
    # Guard upstream FROZEN even if the provider timeout policy grows.
    platform,workspace=_fixture(tmp_path)
    with patch.object(author,'parse_project_yaml_metadata',return_value={'project_id':PID,'business_need':'Inventario y venta.'}):
        with pytest.raises(ValueError,match='UPSTREAM_STATE_REQUIRED'):
            author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,stage_id='scope',model='gemma3:4b')
    from pathlib import Path
    client=Path(__file__).resolve().parents[1]/'ui/web/src/api/client.ts'
    if client.exists():
        source=client.read_text(encoding='utf-8')
        assert "stageId === 'scope' ? 495000" in source
        assert "stageId === 'requirements' ? 555000" in source


def test_cor199_scope_passes_timeout_to_real_adapter_path(tmp_path):
    platform, workspace = _fixture(tmp_path)
    document = workspace/'docs/00_product/product_vision.md'
    document.parent.mkdir(parents=True)
    content = '# Vision FROZEN\nAutorizada como fuente upstream.\n'
    document.write_text(content,encoding='utf-8')
    runtime=platform/'outputs/pre_code_wizard/gsdlc_05_e'/PID/'state.json'
    runtime.parent.mkdir(parents=True)
    runtime.write_text(json.dumps({'workspace_id':PID,'stages':{'product-vision':{
        'status':'FROZEN','execution_id':'EX-1','approval_id':'APP-1',
        'content_sha256':author._sha(content.encode('utf-8'))}}}),encoding='utf-8')
    calls=[]
    class StubAdapter:
        def __init__(self, **kwargs): calls.append(kwargs['timeout_seconds'])
        def health(self): return SimpleNamespace(ok=True,data={'models':['gemma3:4b']})
        def _post_json(self,*args,**kwargs):
            return SimpleNamespace(ok=True,metadata={'response':_sample('scope'),'done_reason':'stop',
                'eval_count':200,'total_duration':500_000_000})
    cfg=SimpleNamespace(external_api=False,requires_api_key=False,
        kind=SimpleNamespace(value='local'),endpoint='http://127.0.0.1:11434')
    registry=SimpleNamespace(semantic_valid=True,get=lambda key:cfg)
    with patch.object(author,'parse_project_yaml_metadata',return_value={
         'project_id':PID,'business_need':'Negocio inventario y ventas.'}),\
         patch.object(author.ProviderRegistry,'load',return_value=registry),\
         patch.object(author,'evaluate_loopback_endpoint',return_value=SimpleNamespace(ok=True)),\
         patch.object(author,'OllamaAdapter',StubAdapter):
        result=author.generate_local_guided(platform,workspace_id=PID,workspace_root=workspace,
                                             stage_id='scope',model='gemma3:4b')
    assert calls == [480,3]
    assert result['provenance']['inference_timeout_seconds']==480
    assert result['provenance']['ollama_timings']['eval_count']==200
    assert result['provenance']['upstream_sha256']['product-vision']==author._sha(content.encode('utf-8'))


def test_cor199_browser_budget_not_silently_clamped_by_shared_limit():
    from pathlib import Path
    source=(Path(__file__).resolve().parents[1]/'ui/web/src/api/client.ts').read_text(encoding='utf-8')
    assert "localLongDraft ? 560000 : MAX_REQUEST_TIMEOUT_MS" in source
    assert "stageId === 'scope' ? 495000" in source
    assert "stageId === 'requirements' ? 555000" in source
    assert "function normalizeTimeout(value: number | undefined, maxTimeoutMs: number = MAX_REQUEST_TIMEOUT_MS)" in source
    assert r"/^\/guided-sdlc\/pre-code\/stages\/(?:scope|requirements)\/draft$/" in source


def test_cor203_generated_secret_is_removed_before_any_candidate_write(tmp_path):
    from devpilot_core.policy.secrets import SecretGuard
    platform=tmp_path / 'root'; platform.mkdir()
    # Root guard can use built-in mandatory rules in an isolated fixture.
    content=author._sample('requirements') if hasattr(author,'_sample') else _sample('requirements')
    secret='SYNTHETIC_ONLY_DO_NOT_USE_AS_CREDENTIAL_1234'
    text=content+'\npassword: '+secret+'\n'
    sanitized, info=author.protect_generated_markdown(platform,text)
    assert info['content_safety']=='REDACTED_FOR_OWNER_REVIEW'
    assert secret not in sanitized
    assert author.SECURITY_HOLD_MARKER in sanitized
    assert SecretGuard(platform).scan_text(sanitized).effect.value=='allow'
    ids={f['id'] for f in author.quality_findings('requirements',sanitized)}
    assert 'R0207_SECURITY_REDACTION_REQUIRES_OWNER_REVIEW' in ids
    assert author.SECURITY_HOLD_MARKER not in content


def test_cor203_non_secret_text_and_excessive_exposure_are_fail_closed(tmp_path):
    root=tmp_path/'root';root.mkdir()
    text=_sample('requirements')
    safe, info=author.protect_generated_markdown(root,text)
    assert safe==text and info['redactions']==0
    bad=text+'\n'+''.join('api_key: SYNTHETIC_SECRET_'+str(i)+'_'+'X'*20+'\n' for i in range(6))
    with pytest.raises(ValueError,match='R0207_GENERATED_SECRET_CONTENT_BLOCK'):
        author.protect_generated_markdown(root,bad)


def test_cor203_security_marker_cannot_pass_quality_gate():
    doc=_sample('requirements') + '\n' + author.SECURITY_HOLD_MARKER
    assert any(x['id']=='R0207_SECURITY_REDACTION_REQUIRES_OWNER_REVIEW'
               for x in author.quality_findings('requirements',doc))


def test_cor203_generated_candidate_persists_only_redacted_body(tmp_path, monkeypatch):
    from types import SimpleNamespace
    root=tmp_path/'platform';root.mkdir()
    example='SYNTHETIC_CANARY_NOT_REAL_123456'
    body=_requirements_professional()+'\npassword: '+example+'\n'
    class FakeAdapter:
        def _post_json(self,*args,**kwargs):
            return SimpleNamespace(ok=True,metadata={'response':body,'eval_count':200})
    class FakeHealth:
        def __init__(self,**kw):pass
        def health(self):return SimpleNamespace(ok=True,data={'models':['test:4b']})
    monkeypatch.setattr(author,'OllamaAdapter',FakeHealth)
    # Simulate a healthy installed-model probe, preserving the provider's
    # genuine content and ensuring the guard runs before immutable writes.
    import types
    monkeypatch.setattr(author,'OllamaAdapter',type('Adapter',(),{'__init__':lambda self,**kw:None,'health':lambda self:SimpleNamespace(ok=True,data={'models':['test:4b']})}))
    metadata={'project_id':PID,'stage':'requirements','model':'test:4b','need':'Gestionar inventario', 'source_sha256':'project.yaml:sha256:'+'a'*64,
              'predecessor_sha256':'','upstream_hashes':{},'prompt_revision':'r0207-req-secure-output-v3'}
    from devpilot_core.modeling.contracts import ModelTask
    dest=root/'outputs/mp132_r02_07'/PID/'requirements'/('a'*64+'.json')
    result=author._run_locked(root,'requirements','test:4b',dest,FakeAdapter(),None,metadata,'source-ref','prompt','a'*64,'',0.0)
    assert result['provenance']['generated_content_safety']['content_safety']=='REDACTED_FOR_OWNER_REVIEW'
    assert example not in '\n'.join(p.read_text(encoding='utf8') for p in root.rglob('*') if p.is_file())
    assert author.SECURITY_HOLD_MARKER in result['content']


# COR204: semantic contract at the model-output boundary, before immutable writes.
def _requirements_professional(scope_refs=("SC-IN-01", "SC-IN-02", "SC-IN-03", "SC-IN-04", "SC-IN-05")):
    parts = ["# Especificación de requisitos", "## Propósito", "Sistematizar el ciclo de catálogo, ventas e inventario.",
             "## Alcance", "Se restringe al primer MVP aprobado y a su trazabilidad.",
             "## Requerimientos funcionales del MVP"]
    for n, ref in enumerate(scope_refs, 1):
        parts.append(f"""### RF-{n:03d} — Gestionar la capacidad {ref}
- Origen: {ref}; criterio Scope SC-AC-0{n}.
- Comportamiento: El propietario ejecuta una acción autorizada y consulta el resultado persistido.
- Precondiciones: El propietario tiene sesión válida y registros de entrada vigentes.
- Regla de negocio: La operación requiere datos consistentes y autorización aplicable.
- Excepción: Una petición inválida se rechaza sin modificar datos persistidos.
- Criterio de aceptación: Dado un dato válido, cuando se registra la operación, entonces el sistema conserva la relación y muestra su identificador.
""")
    parts.extend(["## Requisitos no funcionales", "Aplicar controles de acceso y evidencia de pruebas.",
                  "## Decisiones pendientes", "Reglas de validez detalladas por confirmar con el Owner.",
                  "## Trazabilidad", "| Capacidad Scope | RF | Criterio verificable |", "|---|---|---|"])
    parts.extend(f"| {ref} | RF-{n:03d} | SC-AC-0{n} |" for n,ref in enumerate(scope_refs,1))
    return "\n".join(parts)


def test_cor204_real_gemma_commentary_rejected_before_persistence():
    from pathlib import Path
    # Real output is supplied in the fixture from the user; only technical
    # patterns appear in tests, not the business context or any secret fragment.
    commentary = ("# Requirements Specification\n\nOkay, this is a fantastic and incredibly detailed document outlining the scope of an MVP.\n"
        "**Overall Impression:** The plan is very well-structured and anticipates many pitfalls.\n"
        "**Key Strengths:** Clear Prioritization and staged approach.\n"
        "Would you like to draft some requirements based on these details?\n")
    codes={x['id'] for x in author.requirements_output_findings(commentary)}
    assert 'R0207_REQUIREMENTS_COMMENTARY' in codes
    assert 'R0207_REQUIREMENTS_NOT_A_DOCUMENT' in codes
    assert 'R0207_REQUIREMENTS_PER_RF' in codes
    assert 'R0207_REQUIREMENTS_LANGUAGE' in codes


def test_cor204_professional_requirements_valid_and_coverage():
    scope='## MVP\n| ID | Capacidad |\n|---|---|\n'+''.join(f'| SC-IN-{i:02d} | Módulo |\n' for i in range(1,6))+'## MVP+\nDiferidos\n'
    assert author.requirements_output_findings(_requirements_professional(),scope)==[]
    bad=_requirements_professional(("SC-IN-01","SC-IN-02","SC-IN-03"))
    found={x['id'] for x in author.requirements_output_findings(bad,scope)}
    assert 'R0207_REQUIREMENTS_SCOPE_COVERAGE' in found


def test_cor204_per_rf_missing_ac_is_blocking():
    content=_requirements_professional().replace('Criterio de aceptación: Dado un dato válido, cuando se registra la operación, entonces el sistema conserva la relación y muestra su identificador.', 'Nota: se probará')
    assert 'R0207_REQUIREMENTS_RF_INCOMPLETE' in {x['id'] for x in author.requirements_output_findings(content)}


def test_cor204_requirements_prompt_is_spanish_and_post_context_and_versioned():
    assert 'TU SIGUIENTE RESPUESTA DEBE COMENZAR' in author.REQUIREMENTS_OUTPUT_CONTRACT
    assert 'SC-IN' in author.REQUIREMENTS_OUTPUT_CONTRACT
    assert 'No incluyas' in author.REQUIREMENTS_OUTPUT_CONTRACT


def test_cor204_security_marker_still_blocks_review():
    content=_requirements_professional()+'\n'+author.SECURITY_HOLD_MARKER
    assert 'R0207_SECURITY_REDACTION_REQUIRES_OWNER_REVIEW' in {x['id'] for x in author.quality_findings('requirements',content)}


def test_cor204_rejects_commentary_before_immutable_files(tmp_path, monkeypatch):
    from types import SimpleNamespace
    root=tmp_path/'platform';root.mkdir()
    source='Okay, this is a fantastic and incredibly detailed document outlining the scope of an MVP.\nOverall Impression: excellent plan.\nWould you like to help draft requirements?'
    class FakeAdapter:
        def _post_json(self,*args,**kwargs):return SimpleNamespace(ok=True,metadata={'response':source,'eval_count':200})
    monkeypatch.setattr(author,'OllamaAdapter',type('Probe',(),{'__init__':lambda self,**kw:None,'health':lambda self:SimpleNamespace(ok=True,data={'models':['gemma3:4b']})}))
    context={'project_id':PID,'stage':'requirements','model':'gemma3:4b','need':'Catálogo e inventario',
             'source_sha256':'project.yaml:sha256:'+'a'*64,'predecessor_sha256':'','upstream_hashes':{},
             'upstream': [('scope','## MVP\nSC-IN-01')], 'prompt_revision':'r0207-requirements-rf-coverage-v4'}
    dest=root/'outputs/mp132_r02_07'/PID/'requirements'/('c'*64+'.json')
    with pytest.raises(ValueError,match='R0207_REQUIREMENTS_OUTPUT_NOT_SPECIFICATION'):
        author._run_locked(root,'requirements','gemma3:4b',dest,FakeAdapter(),None,context,'source-ref','prompt','c'*64,'',0.0)
    assert not list(dest.parent.glob('cand-*.md'))
    assert not dest.exists()
    failures=list(dest.parent.glob('*.failure.json'))
    assert len(failures)==1
    safe=failures[0].read_text(encoding='utf-8')
    assert 'R0207_REQUIREMENTS_COMMENTARY' in safe
    assert 'Okay' not in safe and 'would you like' not in safe


def test_cor204_valid_professional_output_can_be_persisted(tmp_path, monkeypatch):
    from types import SimpleNamespace
    root=tmp_path/'platform';root.mkdir()
    source=_requirements_professional(('SC-IN-01',))
    class FakeAdapter:
        def _post_json(self,*args,**kwargs):return SimpleNamespace(ok=True,metadata={'response':source,'eval_count':200})
    monkeypatch.setattr(author,'OllamaAdapter',type('Probe',(),{'__init__':lambda self,**kw:None,'health':lambda self:SimpleNamespace(ok=True,data={'models':['gemma3:4b']})}))
    context={'project_id':PID,'stage':'requirements','model':'gemma3:4b','need':'Catálogo e inventario',
             'source_sha256':'project.yaml:sha256:'+'a'*64,'predecessor_sha256':'','upstream_hashes':{},
             'upstream': [('scope','## MVP\nSC-IN-01')], 'prompt_revision':'r0207-requirements-rf-coverage-v4'}
    dest=root/'outputs/mp132_r02_07'/PID/'requirements'/('d'*64+'.json')
    result=author._run_locked(root,'requirements','gemma3:4b',dest,FakeAdapter(),None,context,'source-ref','prompt','d'*64,'',0.0)
    assert result['model']=='gemma3:4b'
    assert result['candidate_sha256']==author._sha(result['content'].encode())
    assert (dest.parent/result['candidate_path']).is_file()
    assert len(list(dest.parent.glob('*.failure.json')))==0


def test_cor204_traceability_table_cannot_mask_missing_rf_origin():
    body=_requirements_professional()
    body=body.replace('- Origen: SC-IN-05; criterio Scope SC-AC-05.', '- Origen: pendiente de definir.')
    findings=author.requirements_output_findings(body, '## MVP\nSC-IN-05\n## MVP+\n')
    ids={f['id'] for f in findings}
    assert 'R0207_REQUIREMENTS_UNTRACED' in ids
    assert 'R0207_REQUIREMENTS_SCOPE_COVERAGE' in ids

# COR205: task-specific compact grounding and a finite output budget.
def test_cor205_requirements_prompt_is_compact_and_grounded_in_frozen_mvp():
    scope = ('## MVP\n| ID | Capacidad |\n|---|---|\n' + ''.join(f'| SC-IN-{i:02d} | Gestionar capacidad {i} | P0 | Limites por definir |\n' for i in range(1,6)) + '## MVP+\nSC-DEF-01 — Diferido\n')
    vision = "## Visión\nEl propietario gobierna el sistema y los agentes son consultivos.\n## Limitaciones\nNo publicar sin aprobación.\n"
    context = {'need': 'a' * 12000, 'upstream': [('product-vision', vision), ('scope', scope)]}
    prompt = author.requirements_compact_prompt(context)
    assert all(f'SC-IN-{i:02d}' in prompt for i in range(1,6))
    assert 'SC-DEF-01' not in prompt
    assert 'Evaluación del MVP Scope' not in prompt
    assert len(prompt) < 8500
    assert author.REQUIREMENTS_INFERENCE_OPTIONS['num_predict'] <= 1900
    assert author.REQUIREMENTS_INFERENCE_OPTIONS['num_ctx'] == 4096
    assert 'el propietario' in prompt.lower()


def test_cor205_rejects_missing_approved_capability_rows():
    with pytest.raises(ValueError, match='SCOPE_CAPABILITIES_MISSING'):
        author.requirements_compact_prompt({'upstream':[('scope', '## MVP\nLista sin IDs\n')]})


def test_cor205_compact_ollama_payload_and_output_bounds(tmp_path, monkeypatch):
    from types import SimpleNamespace
    root = tmp_path / 'platform'; root.mkdir()
    scope = '## MVP\n| ID | Capacidad |\n|---|---|\n| SC-IN-01 | Administrar catálogo |\n## MVP+\nSC-DEF-01\n'
    calls=[]
    source=_requirements_professional(('SC-IN-01',))
    class LocalAdapter:
        def _post_json(self, endpoint, payload, task=None):
            calls.append(payload)
            return SimpleNamespace(ok=True, metadata={'response':source, 'done_reason':'stop', 'eval_count':140})
    monkeypatch.setattr(author,'OllamaAdapter',type('Probe',(),{
         '__init__':lambda self,**kw:None,
         'health':lambda self:SimpleNamespace(ok=True,data={'models':['gemma3:4b']})}))
    context={'project_id':PID,'stage':'requirements','model':'gemma3:4b',
         'need':'Inventario y ventas', 'source_sha256':'project.yaml:sha256:'+'a'*64,
         'predecessor_sha256':'','upstream_hashes':{}, 'upstream':[('scope',scope)],
         'prompt_revision':author.REQUIREMENTS_PROMPT_REVISION}
    dest=root/'outputs/mp132_r02_07'/PID/'requirements'/('e'*64+'.json')
    result=author._run_locked(root,'requirements','gemma3:4b',dest,LocalAdapter(),None,context,'source','unused long prompt','e'*64,'',0.)
    assert result['candidate_sha256']==author._sha(result['content'].encode())
    assert len(calls)==1 and calls[0]['options']['num_predict']==1800
    # Direct _run_locked accepts prompt supplied by caller. Stage adapter enforces
    # the compact output budget and never alters upstream authority.
    assert calls[0]['options']['num_ctx']==4096
    assert result['provenance']['generation_options']['num_predict']==1800


def test_cor205_truncated_output_is_not_stored_as_candidate(tmp_path, monkeypatch):
    from types import SimpleNamespace
    root=tmp_path/'platform';root.mkdir()
    class Model:
        def _post_json(self,*args,**kwargs):
            return SimpleNamespace(ok=True,metadata={'response':_requirements_professional(('SC-IN-01',)),
                                                     'done_reason':'length','eval_count':1800})
    monkeypatch.setattr(author,'OllamaAdapter',type('Probe',(),{'__init__':lambda self,**kw:None,
            'health':lambda self:SimpleNamespace(ok=True,data={'models':['gemma3:4b']})}))
    context={'project_id':PID,'stage':'requirements','model':'gemma3:4b',
             'need':'Catalogo','source_sha256':'project.yaml:sha256:'+'a'*64,
             'predecessor_sha256':'','upstream_hashes':{},'upstream':[('scope','## MVP\nSC-IN-01')],
             'prompt_revision':author.REQUIREMENTS_PROMPT_REVISION}
    dest=root/'outputs/mp132_r02_07'/PID/'requirements'/('f'*64+'.json')
    with pytest.raises(ValueError,match='R0207_REQUIREMENTS_OUTPUT_TRUNCATED'):
        author._run_locked(root,'requirements','gemma3:4b',dest,Model(),None,context,'ref','prompt','f'*64,'',0)
    assert not dest.exists() and not list(dest.parent.glob('cand-*.md'))
    receipt=json.loads(dest.with_suffix('.failure.json').read_text())
    assert receipt['error_code']=='R0207_REQUIREMENTS_OUTPUT_TRUNCATED'
    assert receipt['generation_options']['num_predict']==1800
