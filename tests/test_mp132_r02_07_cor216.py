"""COR216: exact post-assembly checks without new model calls or quality-gate bypass."""
from __future__ import annotations
from types import SimpleNamespace
from pathlib import Path
import re

from devpilot_core.application import r02_07_segmented as seg
from devpilot_core.application import r02_07_semantic as sem
from test_mp132_r02_07_segmented import SCOPE, VISION, args


def generated_document(tmp_path):
    ctx,adapter,calls,errors,record=args(tmp_path)
    result=None
    for _ in seg.plan_from_scope(SCOPE,VISION):
        result=seg.execute_one(tmp_path,'project-X',ctx,adapter,None,'gemma3:4b',None,
                                lambda c:(c,{'content_safety':'PASS'}),record)
    assert not result['partial']
    return result['body'], ctx, adapter, calls


def test_canonical_profile_headings_and_block_policy(tmp_path):
    document,_,_,_=generated_document(tmp_path)
    assert '## Requerimientos no funcionales' in document
    assert '## Requisitos no funcionales' not in document
    assert '## Criterios de bloqueo' in document
    assert sem.requirements_output_findings(document,SCOPE)==[]
    assert '## Trazabilidad' in document


def test_approved_segment_headers_are_not_mutated(tmp_path):
    document,ctx,_,_=generated_document(tmp_path)
    folder=tmp_path/'outputs/mp132_r02_07/project-X/requirements_segments'
    plan=next(folder.iterdir())
    checkpoint=seg.read_json(plan/'GLOBAL.json')
    assert checkpoint['body'].startswith('## Requisitos no funcionales')
    assert checkpoint['sha256']==seg.sha(checkpoint['body'])
    assert '## Requerimientos no funcionales' in document


def test_legitimate_plural_exception_accepted_not_missing(tmp_path):
    document,_,_,_=generated_document(tmp_path)
    variant=document.replace('- Excepción:', '- Excepciones:')
    assert sem.requirements_output_findings(variant,SCOPE)==[]


def test_missing_exception_remains_blocked(tmp_path):
    document,_,_,_=generated_document(tmp_path)
    variant=re.sub(r'(?im)^- Excepción:.*$', '- Error: Se rechaza la solicitud.',document,count=1)
    codes={row['id'] for row in sem.requirements_output_findings(variant,SCOPE)}
    assert 'R0207_REQUIREMENTS_RF_INCOMPLETE' in codes


def test_commentary_and_missing_rf_not_laundered():
    bad='# Commentary\n## Propósito\nEsto es una reseña, sin requisitos funcionales.\n## Alcance\nSin control.\n'
    ids={row['id'] for row in sem.requirements_output_findings(bad,SCOPE)}
    assert 'R0207_REQUIREMENTS_PER_RF' in ids
    assert 'R0207_REQUIREMENTS_NOT_A_DOCUMENT' in ids


def test_complete_replay_requires_zero_inferences(tmp_path):
    document,ctx,adapter,calls=generated_document(tmp_path)
    before=len(calls)
    repeat=seg.execute_one(tmp_path,'project-X',ctx,adapter,None,'gemma3:4b',None,
                           lambda c:(c,{'content_safety':'PASS'}),lambda *args:None)
    assert repeat['partial']==False
    assert repeat['body']==document
    assert len(calls)==before


def test_candidate_receipt_can_be_made_without_model_request(tmp_path):
    document,_,_,_=generated_document(tmp_path)
    folder=tmp_path/'outputs/mp132_r02_07/project-X/requirements'
    target=folder/('1'*64+'.json')
    context={'project_id':'project-X','stage':'requirements','model':'gemma3:4b',
             'need':'Inventario','source_sha256':'project.yaml:sha256:'+'a'*64,
             'predecessor_sha256':'','upstream_hashes':{},'upstream':[('scope',SCOPE)],
             'prompt_revision':'r0207-segmented-v2'}
    class NoModel:
        def _post_json(self,*args,**kwargs):
            raise AssertionError('A complete checkpoint plan must not invoke a model')
    result=sem._run_locked(tmp_path,'requirements','gemma3:4b',target,NoModel(),None,
                           context,'source-ref','unused','1'*64,'',0.0,
                           pre_generated_body=document)
    assert result['candidate_path'].startswith('cand-')
    assert result['provenance']['model_execution_used']
    assert sem.requirements_output_findings(result['content'],SCOPE)==[]
    assert target.is_file()
