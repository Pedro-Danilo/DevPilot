"""R02-09 negative fault matrix, without touching a real Pilot B workspace."""
from __future__ import annotations
import json
from types import SimpleNamespace
import pytest
from devpilot_core.application import r02_09_resilience as durable
from devpilot_core.application import r02_07_segmented as seg
from devpilot_core.modeling.local_endpoint_policy import evaluate_loopback_endpoint
from test_mp132_r02_07_segmented import args


def _execute(root, context, adapter, record):
    return seg.execute_one(root,"case-other-domain",context,adapter,None,"gemma3:4b",None,
        lambda body:(body,{"content_safety":"PASS"}),record)


def test_crash_inside_provider_unknown_outcome_blocks_double_submit(tmp_path):
    ctx, original, calls, failures, record = args(tmp_path)
    class Crash:
        def _post_json(self,*a,**kw):
            calls.append('sent')
            raise ConnectionResetError('loopback connection interrupted')
    with pytest.raises(ValueError,match='R0209_LOCAL_CALL_OUTCOME_UNKNOWN'):
        _execute(tmp_path,ctx,Crash(),record)
    receipt=next(tmp_path.rglob('model_call_receipts/SC-AC-01.attempt-01.json'))
    assert json.loads(receipt.read_text())['status']=='UNKNOWN'
    with pytest.raises(ValueError,match='R0209_UNCERTAIN_MODEL_CALL_BLOCK'):
        _execute(tmp_path,ctx,original,record)
    assert calls==['sent']
    assert not list(tmp_path.rglob('cand-*.md'))
    assert not list(tmp_path.rglob('SC-AC-01.json'))


def test_replay_cannot_overwrite_an_inflight_receipt(tmp_path):
    folder=tmp_path/'p';folder.mkdir()
    first=durable.begin_call(folder,plan_hash='e'*64,unit_id='SC-AC-01',model='gemma3:4b',attempt=1)
    with pytest.raises(ValueError,match='ATTEMPT_ALREADY_CONSUMED'):
        durable.begin_call(folder,plan_hash='e'*64,unit_id='SC-AC-01',model='gemma3:4b',attempt=1)
    with pytest.raises(ValueError,match='UNCERTAIN_MODEL_CALL_BLOCK'):
        durable.guard_replay(folder,'SC-AC-01','e'*64,'gemma3:4b')
    durable.transition(first,'UNKNOWN')
    with pytest.raises(ValueError,match='RECEIPT_TRANSITION_DENY'):
        durable.transition(first,'COMPLETED')


def test_truncated_or_malformed_response_has_bounded_explicit_retry(tmp_path):
    ctx, adapter, calls, failures, record=args(tmp_path)
    class BadOnce:
        called=0
        def _post_json(self, endpoint, payload, task):
            self.called+=1
            if self.called==1:
                return SimpleNamespace(ok=True,metadata={'response':'{ invalid }','done_reason':'stop'})
            return adapter._post_json(endpoint,payload,task)
    fake=BadOnce()
    with pytest.raises(ValueError,match='NOT_CONFORMANT'):
        _execute(tmp_path,ctx,fake,record)
    first=next(tmp_path.rglob('model_call_receipts/SC-AC-01.attempt-01.json'))
    assert json.loads(first.read_text())['status']=='FAILED'
    result=_execute(tmp_path,ctx,fake,record)
    assert result['partial'] is True
    second=next(tmp_path.rglob('model_call_receipts/SC-AC-01.attempt-02.json'))
    assert json.loads(second.read_text())['status']=='COMPLETED'
    assert fake.called==2


def test_corrupted_receipt_blocks_and_preserves_checkpoint(tmp_path):
    ctx,adapter,calls,failures,record=args(tmp_path)
    _execute(tmp_path,ctx,adapter,record)
    # First checkpoint remains valid; corruption on the next obligation cannot erase it.
    record_path=next(tmp_path.rglob('model_call_receipts/SC-AC-01.attempt-01.json'))
    data=json.loads(record_path.read_text());data['plan_hash']='f'*64
    record_path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='R0209_RECEIPT_DRIFT'):
        _execute(tmp_path,ctx,adapter,record)
    assert len(calls)==1


def test_successful_call_without_checkpoint_cannot_repeat(tmp_path):
    ctx,adapter,calls,failures,record=args(tmp_path)
    _execute(tmp_path,ctx,adapter,record)
    checkpoint=next(tmp_path.rglob('SC-AC-01.json'))
    checkpoint.unlink()  # simulate crash/lost checkpoint; never repeat inference
    with pytest.raises(ValueError,match='R0209_COMPLETED_CALL_CHECKPOINT_MISSING'):
        _execute(tmp_path,ctx,adapter,record)
    assert len(calls)==1


def test_project_docs_outside_operator_scope_remain_unchanged(tmp_path):
    workspace=tmp_path/'project';workspace.mkdir()
    frozen=workspace/'frozen.md';frozen.write_bytes(b'SOURCE FROZEN\r\n')
    ctx,adapter,calls,failures,record=args(tmp_path)
    _execute(tmp_path,ctx,adapter,record)
    assert frozen.read_bytes()==b'SOURCE FROZEN\r\n'


def test_egress_policy_denies_external_ollama_endpoint():
    denied=evaluate_loopback_endpoint(provider_id='ollama',endpoint='https://example.org:443')
    assert not denied.ok


def test_receipts_store_no_output_prompt_or_pii(tmp_path):
    ctx,adapter,calls,failures,record=args(tmp_path)
    _execute(tmp_path,ctx,adapter,record)
    receipt=next(tmp_path.rglob('model_call_receipts/*.json')).read_text()
    assert 'prompt' not in receipt and '"response":' not in receipt
    assert 'source_row' not in receipt and 'business_need' not in receipt
    assert '"workspace_writes": 0' in receipt


def test_real_loopback_transport_refused_without_touching_ollama():
    """REAL socket failure, not an Ollama outage claim. No API key or egress."""
    import socket
    import urllib.request
    import urllib.error
    sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
    sock.close()
    with pytest.raises((urllib.error.URLError,ConnectionError,TimeoutError,OSError)):
        urllib.request.urlopen(f'http://127.0.0.1:{port}/api/tags',timeout=0.8)


def test_plan_or_model_drift_blocks_without_model_call(tmp_path):
    folder=tmp_path/'plan'; folder.mkdir()
    path=durable.begin_call(folder,plan_hash='a'*64,unit_id='GLOBAL',model='gemma3:4b',attempt=1)
    durable.transition(path,'FAILED')
    with pytest.raises(ValueError,match='RECEIPT_DRIFT'):
        durable.guard_replay(folder,'GLOBAL','b'*64,'gemma3:4b')
    with pytest.raises(ValueError,match='RECEIPT_DRIFT'):
        durable.guard_replay(folder,'GLOBAL','a'*64,'other-model')


def test_failed_transport_response_consumes_attempt_without_candidate(tmp_path):
    ctx,adapter,calls,failures,record=args(tmp_path)
    class ProviderDown:
        def _post_json(self,*a,**kwargs):
            return SimpleNamespace(ok=False,metadata={'error_type':'connection_refused'})
    with pytest.raises(ValueError,match='SEGMENT_PROVIDER_FAILED'):
        _execute(tmp_path,ctx,ProviderDown(),record)
    receipt=next(tmp_path.rglob('model_call_receipts/SC-AC-01.attempt-01.json'))
    assert json.loads(receipt.read_text())['status']=='FAILED'
    assert not list(tmp_path.rglob('SC-AC-01.json'))
    # Explicit separate user action, not an autonomous retry
    _execute(tmp_path,ctx,adapter,record)
    assert len(calls)==1


def test_incomplete_response_receipt_does_not_claim_success(tmp_path):
    folder=tmp_path/'segment'; folder.mkdir()
    started=durable.begin_call(folder,plan_hash='e'*64,unit_id='GLOBAL',model='gemma3:4b',attempt=1)
    durable.transition(started,'RESPONSE_RECEIVED')
    with pytest.raises(ValueError,match='UNCERTAIN_MODEL_CALL_BLOCK'):
        durable.guard_replay(folder,'GLOBAL','e'*64,'gemma3:4b')
    assert not (folder/'GLOBAL.json').exists()


def _direct_case(tmp_path, fake, payload_hash='a'*64):
    from devpilot_core.application import r02_07_semantic as author
    from unittest.mock import patch
    destination=tmp_path/'outputs/mp132_r02_07/proj/product-vision'/f'{payload_hash}.json'
    context={'stage':'product-vision','project_id':'proj','need':'Gestionar documentos',
        'upstream_hashes':{},'prompt_revision':'test','predecessor_sha256':''}
    with patch.object(author.OllamaAdapter,'health',return_value=SimpleNamespace(ok=True,data={'models':['gemma3:4b']})), \
         patch.object(author,'protect_generated_markdown',side_effect=lambda root,body:(body,{'content_safety':'PASS'})):
        return author._run_locked(tmp_path,'product-vision','gemma3:4b',destination,fake,SimpleNamespace(),
            context,'project.yaml:sha256:aaa','prompt',payload_hash,'',0)


def test_vision_direct_call_known_failure_then_explicit_success(tmp_path):
    class Fake:
        calls=0
        def _post_json(self, *args, **kw):
            self.calls+=1
            if self.calls==1:return SimpleNamespace(ok=False,metadata={'error_type':'connection_refused'})
            return SimpleNamespace(ok=True,metadata={'response':'## Visión\n'+'Visión del proyecto. '*7,'done_reason':'stop'})
    fake=Fake()
    with pytest.raises(ValueError,match='R0207_MODEL_GENERATION_FAILED'):
        _direct_case(tmp_path,fake)
    assert fake.calls==1
    saved=_direct_case(tmp_path,fake)
    assert saved['candidate_sha256'] and fake.calls==2
    direct=list(tmp_path.rglob('direct_model_calls/*/model_call_receipts/*.json'))
    assert [json.loads(p.read_text())['status'] for p in sorted(direct)] == ['FAILED','COMPLETED']
    assert _direct_case(tmp_path,fake)['candidate_sha256']==saved['candidate_sha256']
    assert fake.calls==2


def test_vision_direct_crash_does_not_retry_unknown(tmp_path):
    class Failing:
        calls=0
        def _post_json(self,*a,**k):
            self.calls+=1
            raise TimeoutError('transport lost')
    f=Failing()
    with pytest.raises(ValueError,match='R0209_LOCAL_CALL_OUTCOME_UNKNOWN'):
        _direct_case(tmp_path,f)
    with pytest.raises(ValueError,match='R0209_UNCERTAIN_MODEL_CALL_BLOCK'):
        _direct_case(tmp_path,f)
    assert f.calls==1
