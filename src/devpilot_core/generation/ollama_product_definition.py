"""R02-03 bounded Ollama *evaluation* of synthetic Product Definition candidates.

Only an explicit Owner action can execute one local inference. No endpoint from
clients, no arbitrary prompt, no provider enablement, no FROZEN/approval writes.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable
from devpilot_core.generation.contracts import (GenerationRequest, CandidateOrigin,
    CandidateOriginKind, ProviderClass, GenerationProvenance, CandidateStatus,
    create_candidate, canonical_sha256)
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.modeling.ollama_adapter import OllamaAdapter
from devpilot_core.modeling.local_endpoint_policy import evaluate_loopback_endpoint
from devpilot_core.modeling.local_model_readiness import host_resources
from devpilot_core.modeling.contracts import ModelTask

DATASET = Path('evals/fixtures/r02_03_product_definition.json')
MODEL_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,99}$')
REQUEST_RE = re.compile(r'^[a-f0-9]{32}$')
MAX_DURATION = 75
MAX_RESPONSE = 65536

class LocalCandidateBlock(ValueError):
    def __init__(self, code: str): super().__init__(code);self.code=code

def parse_model_json(raw: str, *, expected_ref: str) -> dict[str,str]:
    if not isinstance(raw,str) or len(raw)>16000: raise LocalCandidateBlock('RESPONSE_BOUNDS_BLOCK')
    try: obj=json.loads(raw.strip())
    except (ValueError,TypeError) as exc: raise LocalCandidateBlock('PARSE_BLOCKED') from exc
    if not isinstance(obj,dict) or set(obj)!={'title','content','evidence_refs'}:
        raise LocalCandidateBlock('SCHEMA_BLOCKED')
    if not isinstance(obj['title'],str) or not 3 <= len(obj['title'].strip()) <= 160:
        raise LocalCandidateBlock('TITLE_INVALID')
    if not isinstance(obj['content'],str) or not 40 <= len(obj['content'].strip()) <= 12000:
        raise LocalCandidateBlock('CONTENT_INVALID')
    if obj['evidence_refs'] != [expected_ref]: raise LocalCandidateBlock('UNSUPPORTED_REFERENCE_BLOCK')
    return {'title':obj['title'].strip(),'content':obj['content'].strip(),'evidence_refs':[expected_ref]}

def load_case(root: Path, case_id: str) -> tuple[dict[str,Any],str]:
    dataset=json.loads((root/DATASET).read_text(encoding='utf-8'))
    if dataset.get('schema') != 'MP132.R02.03.dataset.v1':raise LocalCandidateBlock('DATASET_SCHEMA_BLOCK')
    matching=[x for x in dataset['cases'] if x['id']==case_id]
    if len(matching)!=1:raise LocalCandidateBlock('CASE_NOT_ALLOWLISTED')
    return matching[0],canonical_sha256(dataset)

def _prompt(case: dict[str,Any]) -> str:
    return ('Eres un asistente de redacción de Product Definition. Usa SOLAMENTE este contexto '
        'sintético, sin inventar entidades, integraciones ni leyes. Devuelve SOLAMENTE '
        'un JSON objeto con exactamente tres campos: "title" (string), "content" (Markdown en español '
        'de al menos 80 caracteres con encabezado y criterios pertinentes), "evidence_refs" '
        f'(array con exactamente ["{case["evidence_ref"]}"]). '
        'Si faltan decisiones, decláralas pendientes, no las inventes. '
        f'Etapa: {case["stage"]}. Contexto: {case["context"]}')

class OllamaProductDefinitionEvaluation:
    def __init__(self, root: Path, *, adapter_factory: Callable[...,Any] = OllamaAdapter):
        self.root=Path(root).resolve();self.adapter_factory=adapter_factory
    def run(self, *, case_id: str, model: str, request_id: str, execute: bool = False) -> dict[str,Any]:
        case,fixture_hash=load_case(self.root,case_id)
        if not MODEL_RE.fullmatch(model) or not REQUEST_RE.fullmatch(request_id):
            raise LocalCandidateBlock('MODEL_OR_REQUEST_ID_INVALID')
        registry=ProviderRegistry.load(self.root); cfg=registry.get('ollama')
        if not registry.semantic_valid or cfg is None or cfg.external_api or cfg.requires_api_key or cfg.kind.value!='local':
            raise LocalCandidateBlock('OLLAMA_CONFIG_NOT_LOCAL')
        decision=evaluate_loopback_endpoint(provider_id='ollama',endpoint=cfg.endpoint)
        if not decision.ok:raise LocalCandidateBlock('LOOPBACK_POLICY_BLOCK')
        output_dir=self.root/'outputs'/'mp132_r02_03'/'candidates'
        target=output_dir/(request_id+'.json')
        req=GenerationRequest(request_id=request_id,artifact_type=case['artifact_type'],
            profile_version='product-definition-local-eval/v1',dependency_profile_version='product-definition/draft-v1',
            upstream_hashes={'fixture':fixture_hash},owner_inputs={'case_id':case_id,'model':model},
            preferred_route='local-model',allowed_routes=('local-model',),
            policy_snapshot={'external_api':False,'network':'loopback-only','owner_one_shot_opt_in':execute},
            budget_snapshot={'max_remote_cost_usd':0,'max_duration_seconds':MAX_DURATION},
            context_reference=case['evidence_ref'])
        spec={'schema':'MP132.R02.03.evaluation.v1','case_id':case_id,'stage':case['stage'],
              'request_id':request_id,'model':model,'fixture_sha256':fixture_hash,
              'request_sha256':req.canonical_input_sha256,'endpoint_class':'loopback-only',
              'source_writes':0,'provider_enablement_changed':False,'external_api_calls':0,
              'cost_remote_usd':0.0,'hardware':host_resources()}
        if not execute:return {**spec,'status':'DRY_RUN','network_calls':0,'candidate':None}
        if target.exists():
            try: saved=json.loads(target.read_text(encoding='utf-8'))
            except (OSError,ValueError) as exc:raise LocalCandidateBlock('PERSISTED_RECEIPT_INVALID') from exc
            if saved.get('request_sha256')!=spec['request_sha256'] or saved.get('model')!=model:
                raise LocalCandidateBlock('REQUEST_ID_CONFLICT')
            return {**saved,'replayed':True}
        output_dir.mkdir(parents=True,exist_ok=True)
        lock=output_dir/(request_id+'.lock')
        try:
            fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        except FileExistsError as exc:raise LocalCandidateBlock('REQUEST_ALREADY_IN_PROGRESS') from exc
        os.close(fd)
        try:
            # No global enablement. This adapter is instantiated for exactly one
            # Owner-authorized local evaluation; existing config stays untouched.
            health_adapter=self.adapter_factory(provider_config=cfg,timeout_seconds=2.0,max_response_bytes=MAX_RESPONSE)
            health=health_adapter.health()
            if not health.ok:raise LocalCandidateBlock('OLLAMA_UNAVAILABLE')
            names=health.data.get('models') or []
            if model not in names:raise LocalCandidateBlock('MODEL_NOT_INSTALLED')
            adapter=self.adapter_factory(provider_config=cfg,timeout_seconds=MAX_DURATION,max_response_bytes=MAX_RESPONSE)
            started=time.monotonic()
            response=adapter._post_json('/api/generate',{'model':model,'prompt':_prompt(case),
                'format':'json','stream':False,'options':{'temperature':0,'num_predict':700}},
                task=ModelTask.GENERATE)
            elapsed=round((time.monotonic()-started)*1000)
            if not response.ok:raise LocalCandidateBlock('OLLAMA_GENERATION_FAILED')
            payload=parse_model_json(response.metadata.get('response'),expected_ref=case['evidence_ref'])
            provenance=GenerationProvenance(prompt_ref='r02-03-synthetic-v1',profile_ref=req.profile_version,
                context_ref=case['evidence_ref'],network_used=True,external_api_used=False,
                latency_ms=elapsed,evidence_refs=(case['evidence_ref'],))
            candidate=create_candidate(request=req,payload={'stage_id':case['stage'],'content':payload['content'],
                'title':payload['title'],'evidence_refs':payload['evidence_refs']},
                origin=CandidateOrigin(kind=CandidateOriginKind.PROVIDER,provider_class=ProviderClass.LOCAL_MODEL,
                    provider_id='ollama',model_id=model),provenance=provenance,status=CandidateStatus.GENERATED,
                evaluation_summary={'source_write':False,'freeze_authority':False,
                    'human_review_required':True,'quality_evaluated':False})
            receipt={**spec,'status':'REAL_CANDIDATE_GENERATED_UNREVIEWED','network_calls':2,
                'latency_ms':elapsed,'candidate':candidate.to_dict(),
                'candidate_sha256':candidate.content_sha256,
                'token_count_observed':{'prompt':response.metadata.get('prompt_eval_count'),
                    'output':response.metadata.get('eval_count')},'replayed':False}
            temporary=output_dir/(request_id+'.tmp')
            with temporary.open('x',encoding='utf-8') as stream:
                json.dump(receipt,stream,indent=2,ensure_ascii=False)
            os.replace(temporary,target)
            return receipt
        finally:
            lock.unlink(missing_ok=True)
