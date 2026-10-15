"""R01-06 focal project-scoped gate tests. No project-wide artificial coverage."""
from __future__ import annotations
from pathlib import Path
from dataclasses import replace
import pytest
from devpilot_core.validation.artifact_coverage_gate import CoverageRule
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def audit(tmp_path):
    r=ArtifactProfileRegistry(ROOT)
    def check(*rules,stage='ARCHITECTURE'):
        return r.evaluate_coverage(tuple(rules),stage=stage,documents_root=tmp_path)
    return tmp_path,check

def rule(**kw):
    defaults=dict(artifact_type='architecture-description',path='docs/02_architecture/design.md',stage='ARCHITECTURE',obligation='REQUIRED',semantic_review='PASS',semantic_evidence=('owner-review-007',))
    defaults.update(kw)
    return CoverageRule(**defaults)

def put(root,rel='docs/02_architecture/design.md',text='# Diseño\n\n## Contexto\nLa solución tiene dos componentes documentados.\n'):
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8');return p

def test_required_missing_blocks(audit):
    _,check=audit;out=check(rule());assert out['result']=='BLOCK';assert 'REQUIRED_MISSING' in out['items'][0]['reasons']

def test_recommended_missing_warns(audit):
    _,check=audit;assert check(rule(obligation='RECOMMENDED'))['result']=='WARN'

def test_conditional_unknown_review(audit):
    _,check=audit;out=check(rule(obligation='CONDITIONAL'));assert out['result']=='REVIEW_REQUIRED';assert 'CONDITION_FACTS_UNVERIFIED' in out['items'][0]['reasons']

def test_conditional_negative_evidenced_na(audit):
    _,check=audit;assert check(rule(obligation='CONDITIONAL',applicability=False,applicability_evidence=('scope-08',)))['items'][0]['result']=='NOT_APPLICABLE'

def test_conditional_true_missing_blocks(audit):
    _,check=audit;assert check(rule(obligation='CONDITIONAL',applicability=True,applicability_evidence=('scope-08',)))['result']=='BLOCK'

def test_na_without_rationale_review(audit):
    _,check=audit;assert check(rule(obligation='NOT_APPLICABLE'))['result']=='REVIEW_REQUIRED'

def test_na_with_rationale_evidence(audit):
    _,check=audit;assert check(rule(obligation='NOT_APPLICABLE',na_reason='No AI components',applicability_evidence=('architecture-absence-evidence',)))['items'][0]['result']=='NOT_APPLICABLE'

def test_placeholder_template_does_not_pass(audit):
    root,check=audit;put(root,text='# Design\n## Contexto\nTODO\n');assert 'EMPTY_OR_PLACEHOLDER_CONTENT' in check(rule())['items'][0]['reasons']

def test_existing_doc_semantic_pending_blocks(audit):
    root,check=audit;put(root);out=check(rule(semantic_review='PENDING',semantic_evidence=()));assert out['result']=='BLOCK';assert 'SEMANTIC_ACCEPTANCE_NOT_EVIDENCED' in out['items'][0]['reasons']

def test_attested_semantic_valid_pass(audit):
    root,check=audit;put(root);out=check(rule());assert out['result']=='PASS';assert out['automatic_semantic_approval'] is False

def test_failed_semantic_block(audit):
    root,check=audit;put(root);assert check(rule(semantic_review='FAIL'))['result']=='BLOCK'

def test_stage_deferred_not_global_missing(audit):
    _,check=audit;assert check(rule(),stage='INTAKE')['items'][0]['result']=='NOT_DUE'

def test_missing_dependency_blocks(audit):
    root,check=audit;put(root);r=rule(dependencies=('docs/02_architecture/data.md',),dependency_freshness={'docs/02_architecture/data.md':'CURRENT'});assert check(r)['result']=='BLOCK'

def test_unproven_dependency_freshness_review(audit):
    root,check=audit;put(root);put(root,'docs/02_architecture/data.md');r=rule(dependencies=('docs/02_architecture/data.md',));assert check(r)['result']=='REVIEW_REQUIRED'

def test_evidenced_dependency_pass(audit):
    root,check=audit;put(root);put(root,'docs/02_architecture/data.md');r=rule(dependencies=('docs/02_architecture/data.md',),dependency_freshness={'docs/02_architecture/data.md':'CURRENT'},dependency_evidence={'docs/02_architecture/data.md':'review-007'});assert check(r)['result']=='PASS'

def test_bounded_rules_only_no_universal_catalog(audit):
    root,check=audit;put(root);out=check(rule());assert len(out['items'])==1;assert out['result']=='PASS'

def test_no_rules_cannot_claim_pass(audit):
    _,check=audit;assert check()['result']=='REVIEW_REQUIRED'

def test_duplicate_block(audit):
    _,check=audit;with_rule=rule();
    with pytest.raises(ValueError,match='DUPLICATE'):check(with_rule,with_rule)

def test_no_path_escape(audit):
    _,check=audit
    with pytest.raises(ValueError,match='UNSAFE'):check(rule(path='../secret.md'))

def test_profile_required_headings_enforced(audit):
    root,check=audit;put(root,'docs/00_product/product_vision.md','# Vision\n## Contexto\nHechos observables.\n')
    out=check(rule(path='docs/00_product/product_vision.md',artifact_type='product-vision'))
    assert out['result']=='BLOCK' and any('MISSING_REQUIRED_SECTIONS' in s for s in out['items'][0]['reasons'])

def test_readonly(audit):
    root,check=audit;f=put(root);before=f.read_bytes();check(rule());assert f.read_bytes()==before


def test_current_dependency_without_evidence_requires_review(audit):
    root,check=audit;put(root);put(root,'docs/02_architecture/data.md')
    r=rule(dependencies=('docs/02_architecture/data.md',),dependency_freshness={'docs/02_architecture/data.md':'CURRENT'})
    assert check(r)['result']=='REVIEW_REQUIRED'

def test_required_heading_with_todo_only_blocks(audit):
    root,check=audit
    put(root,'docs/00_product/product_vision.md', '# Visión\n## Resumen ejecutivo\nTODO\n## Problema\nHay un problema real.\n## Visión\nEl producto resolverá el problema.\n## MVP\nPrimera versión.\n## Indicadores\nSe medirán resultados.\n')
    out=check(rule(path='docs/00_product/product_vision.md',artifact_type='product-vision'))
    assert out['result']=='BLOCK' and any('EMPTY_REQUIRED_SECTION' in s for s in out['items'][0]['reasons'])
