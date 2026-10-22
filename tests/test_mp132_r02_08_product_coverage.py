"""R02-08 bounded quality coverage: Pilot B and distinct non-retail domain."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import pytest
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validation.product_definition_coverage import (
    FrozenProof, GroundedLink, ProductDefinitionInput, _hash,
)

ROOT = Path(__file__).resolve().parents[1]


def documents(root: Path, *, domain: str = 'clinic'):
    spec = {
        'product-vision': ('docs/00_product/product_vision.md', '# Visión\n## Resumen ejecutivo\nEl problema del centro de turnos requiere una agenda.\n## Problema\nLa agenda manual falla.\n## Visión\nTurnos claros.\n## MVP\nAgendar citas.\n## Indicadores\nNúmero de citas.\n'),
        'mvp-scope': ('docs/00_product/mvp_scope.md', '# Scope\n## MVP\nSC-IN-01 Agendar citas.\n## MVP+\nNotificaciones futuras.\n## Out of scope\nPagos no incluidos.\n## Criterios\nRegistrar un turno.\n'),
        'requirements-specification': ('docs/01_requirements/requirements_specification.md', '# Requisitos\n## Propósito\nRegistrar turnos.\n## Alcance\nAgenda MVP.\n## Requerimientos funcionales del MVP\n### RF-001\nOrigen SC-IN-01. Dado usuario, cuando reserva, entonces se registra el turno.\n## Requerimientos no funcionales\nRegistro íntegro.\n## Criterios de bloqueo\nNo duplicar reserva.\n'),
    }
    if domain != 'clinic':
        raise ValueError('invalid domain')
    frozen = {}
    for typ,(rel,content) in spec.items():
        dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content,encoding='utf-8')
        frozen[typ] = FrozenProof(_hash(content), 'runtime-approval-' + typ)
    return frozen


def check(root: Path, proofs, **kwargs):
    return ArtifactProfileRegistry(ROOT).evaluate_product_definition(root, ProductDefinitionInput(
        frozen=proofs,
        semantic_acceptance={k: ('owner-reviewed-'+k,) for k in proofs},
        product_has_ai=False, ai_fact_evidence=('scope-excludes-model-runtime',), **kwargs))


def test_second_domain_only_grounding_pending(tmp_path):
    out=check(tmp_path,documents(tmp_path))
    assert out['result']=='REVIEW_REQUIRED'
    assert out['untraced_scope_ids']==[]
    assert any(x['rule_id']=='CROSS_ARTIFACT_SEMANTICS_UNPROVEN' for x in out['findings'])


def test_grounded_links_are_presence_not_semantic_equivalence(tmp_path):
    proofs=documents(tmp_path)
    link=GroundedLink('product-vision','mvp-scope','un fragmento que no existe','SC-IN-01','review-001')
    out=check(tmp_path,proofs,links=(link,))
    assert out['result']=='BLOCK'  # case-sensitive missing citation must fail
    link=replace(link,source_excerpt='La agenda manual falla.')
    out=check(tmp_path,proofs,links=(link,))
    assert out['result']=='REVIEW_REQUIRED'
    assert out['cross_artifact_links'][0]['source_present']


def test_semantic_verified_links_can_pass_without_auto_approval(tmp_path):
    proofs=documents(tmp_path)
    links=(GroundedLink('product-vision','mvp-scope','La agenda manual falla.','SC-IN-01','human-review-1','PASS'),
           GroundedLink('mvp-scope','requirements-specification','SC-IN-01','SC-IN-01','human-review-2','PASS'))
    out=check(tmp_path,proofs,links=links)
    assert out['result']=='PASS'
    assert out['automatic_semantic_approval'] is False
    assert out['evaluation_only'] and out['writes_performed'] is False


def test_missing_scope_trace_is_material_block(tmp_path):
    proofs=documents(tmp_path)
    scope=tmp_path/'docs/00_product/mvp_scope.md';scope.write_text(scope.read_text()+'\nSC-IN-02 Configurar turnos.\n')
    proofs['mvp-scope']=FrozenProof(_hash(scope.read_text()),'runtime-approval-new')
    out=check(tmp_path,proofs)
    assert out['result']=='BLOCK'
    assert out['untraced_scope_ids']==['SC-IN-02']


def test_hash_drift_blocks(tmp_path):
    p=documents(tmp_path)
    p['product-vision']=FrozenProof('0'*64,'runtime-approval')
    out=check(tmp_path,p)
    assert any(x['rule_id']=='FROZEN_HASH_OR_STATE_DRIFT' for x in out['findings'])


def test_no_lifecycle_proof_remains_review(tmp_path):
    proofs=documents(tmp_path)
    del proofs['product-vision']
    out=check(tmp_path,proofs)
    assert any(x['rule_id']=='FROZEN_AUTHORITY_UNVERIFIED' for x in out['findings'])


def test_miasi_unknown_cannot_be_automatic_na(tmp_path):
    proofs=documents(tmp_path)
    out=ArtifactProfileRegistry(ROOT).evaluate_product_definition(tmp_path, ProductDefinitionInput(frozen=proofs, semantic_acceptance={k: ('owner-reviewed-'+k,) for k in proofs}))
    assert out['miasi_applicability']=='REVIEW_REQUIRED'
    assert out['result']=='REVIEW_REQUIRED'


def test_miasi_not_required_for_developer_tool_llm(tmp_path):
    proofs=documents(tmp_path)
    out=check(tmp_path,proofs)
    assert out['miasi_applicability']=='NOT_APPLICABLE'


def test_no_waiver_bypass_existing_control(tmp_path):
    from devpilot_core.validation.project_profile import Waiver, assess_waiver
    with pytest.raises(ValueError,match='NON_WAIVABLE'):
        assess_waiver(Waiver('privacy','reason','medium',('review',),'owner','2029-01-01','change','waiver-001'))


def test_evaluation_does_not_modify_business_files(tmp_path):
    proofs=documents(tmp_path)
    before={p: p.read_bytes() for p in tmp_path.rglob('*.md')}
    check(tmp_path,proofs)
    assert before == {p:p.read_bytes() for p in before}


def test_grounding_link_direction_rejected_without_special_filesystem_permissions(tmp_path):
    documents(tmp_path)
    with pytest.raises(ValueError,match='R0208_LINK_DIRECTION_INVALID'):
        GroundedLink('mvp-scope','mvp-scope','a','b','review')


def test_pre_code_projection_uses_authoritative_runtime_receipts(tmp_path):
    from devpilot_core.application.pre_code_wizard_service import PreCodeWizardApplicationService
    proofs=documents(tmp_path)
    service=PreCodeWizardApplicationService.__new__(PreCodeWizardApplicationService)
    service.profiles=ArtifactProfileRegistry(ROOT)
    service._stage_by_id={k:{'relative_path':relative} for k,relative in (
        ('product-vision','docs/00_product/product_vision.md'),
        ('scope','docs/00_product/mvp_scope.md'),
        ('requirements','docs/01_requirements/requirements_specification.md'))}
    state={'stages':{k:{'status':'FROZEN','approved_sha256':None,'approval_id':'APP-001','review_id':'rev-001','execution_id':'exec-001'} for k in service._stage_by_id}}
    service._stage_state=lambda current,stage_id:current['stages'][stage_id]
    for stage_id,typ in (('product-vision','product-vision'),('scope','mvp-scope'),('requirements','requirements-specification')):
        path=tmp_path/service._stage_by_id[stage_id]['relative_path']
        from hashlib import sha256
        state['stages'][stage_id]['approved_sha256']=sha256(path.read_bytes()).hexdigest()
    out=service._product_definition_coverage(state,tmp_path)
    assert out['result']=='REVIEW_REQUIRED'
    assert not any(f['rule_id']=='FROZEN_HASH_OR_STATE_DRIFT' for f in out['findings'])
    state['stages']['scope']['approved_sha256']='0'*64
    out=service._product_definition_coverage(state,tmp_path)
    assert out['result']=='BLOCK'


def test_scope_mention_in_overview_is_not_rf_origin(tmp_path):
    proofs=documents(tmp_path)
    req=tmp_path/'docs/01_requirements/requirements_specification.md'
    text=req.read_text(encoding='utf-8')
    text=text.replace('Origen SC-IN-01.', 'Origen SC-AC-01.')
    text=text.replace('## Alcance\nAgenda MVP.', '## Alcance\nAgenda MVP; SC-IN-01.')
    req.write_text(text,encoding='utf-8')
    proofs['requirements-specification']=FrozenProof(_hash(text),'runtime-updated')
    out=check(tmp_path,proofs)
    assert out['untraced_scope_ids']==['SC-IN-01']
    assert out['result']=='BLOCK'


def test_reference_evidence_contains_exact_source_and_rf_behavior(tmp_path):
    proofs=documents(tmp_path)
    out=check(tmp_path,proofs)
    evidence=out['reference_evidence']
    assert len(evidence)==1
    row=evidence[0]
    assert row['capability_id']=='SC-IN-01'
    assert row['requirement_rf']=='RF-001'
    assert row['origin_verified'] is True
    assert row['semantic_verified'] is False
    assert row['scope_excerpt'] in (tmp_path/'docs/00_product/mvp_scope.md').read_text()
    assert row['requirement_excerpt'] in (tmp_path/'docs/01_requirements/requirements_specification.md').read_text()
