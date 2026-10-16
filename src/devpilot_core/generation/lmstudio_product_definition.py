"""R02-04: optional bounded LM Studio Product Definition parity; no implicit enablement.

Uses existing adapter and R02-03 dataset/schema. Optional real calls are strictly
Owner-opt-in; unknown/missing provider yields explicit BLOCK, never fake PASS.
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Any, Callable
from devpilot_core.generation.ollama_product_definition import (load_case, _prompt,
    parse_model_json, MODEL_RE, REQUEST_RE, MAX_DURATION, MAX_RESPONSE, LocalCandidateBlock)
from devpilot_core.generation.contracts import (GenerationRequest, CandidateOrigin,
    CandidateOriginKind, ProviderClass, GenerationProvenance, CandidateStatus,
    create_candidate)
from devpilot_core.modeling.providers import ProviderRegistry
from devpilot_core.modeling.lmstudio_adapter import LMStudioAdapter
from devpilot_core.modeling.local_endpoint_policy import evaluate_loopback_endpoint
from devpilot_core.modeling.local_model_readiness import host_resources
from devpilot_core.modeling.contracts import ModelTask

def _extract_content(payload: dict[str, Any]) -> str:
    choices=payload.get('choices') if isinstance(payload,dict) else None
    if not isinstance(choices,list) or not choices or not isinstance(choices[0],dict):
        raise LocalCandidateBlock('LMSTUDIO_CONTENT_INVALID')
    message=choices[0].get('message')
    content=message.get('content') if isinstance(message,dict) else None
    if not isinstance(content,str):raise LocalCandidateBlock('LMSTUDIO_CONTENT_INVALID')
    return content

def _usage(payload: dict[str, Any], key: str) -> int | None:
    usage=payload.get('usage') if isinstance(payload,dict) else None
    value=usage.get(key) if isinstance(usage,dict) else None
    return value if isinstance(value,int) and value>=0 else None

class LMStudioProductDefinitionEvaluation:
    def __init__(self, root: Path, *, adapter_factory: Callable[...,Any] = LMStudioAdapter):
        self.root=Path(root).resolve();self.adapter_factory=adapter_factory
    def run(self, *, case_id: str, model: str, request_id: str, execute: bool = False) -> dict[str,Any]:
        case,fixture_hash=load_case(self.root,case_id)
        if not MODEL_RE.fullmatch(model) or not REQUEST_RE.fullmatch(request_id):
            raise LocalCandidateBlock('MODEL_OR_REQUEST_ID_INVALID')
        registry=ProviderRegistry.load(self.root); cfg=registry.get('lmstudio')
        if not registry.semantic_valid or cfg is None or cfg.external_api or cfg.requires_api_key or cfg.kind.value!='local':
            raise LocalCandidateBlock('LMSTUDIO_CONFIG_NOT_LOCAL')
        decision=evaluate_loopback_endpoint(provider_id='lmstudio',endpoint=cfg.endpoint)
        if not decision.ok:raise LocalCandidateBlock('LOOPBACK_POLICY_BLOCK')
        output_dir=self.root/'outputs'/'mp132_r02_04'/'candidates'
        target=output_dir/(request_id+'.json')
        req=GenerationRequest(request_id=request_id,artifact_type=case['artifact_type'],
            profile_version='product-definition-lmstudio-eval/v1',dependency_profile_version='product-definition/draft-v1',
            upstream_hashes={'fixture':fixture_hash},owner_inputs={'case_id':case_id,'model':model},
            preferred_route='local-model',allowed_routes=('local-model',),
            policy_snapshot={'external_api':False,'network':'loopback-only','owner_one_shot_opt_in':execute},
            budget_snapshot={'max_remote_cost_usd':0,'max_duration_seconds':MAX_DURATION},
            context_reference=case['evidence_ref'])
        spec={'schema':'MP132.R02.04.evaluation.v1','case_id':case_id,'stage':case['stage'],
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
            if not health.ok:raise LocalCandidateBlock('LMSTUDIO_UNAVAILABLE')
            names=health.data.get('models') or []
            if model not in names:raise LocalCandidateBlock('MODEL_NOT_INSTALLED')
            adapter=self.adapter_factory(provider_config=cfg,timeout_seconds=MAX_DURATION,max_response_bytes=MAX_RESPONSE)
            started=time.monotonic()
            response=adapter._post_json('/v1/chat/completions',{'model':model,
                'messages':[{'role':'user','content':_prompt(case)}],
                'stream':False,'temperature':0,'max_tokens':700,
                'response_format':{'type':'json_object'}}, task=ModelTask.GENERATE)
            elapsed=round((time.monotonic()-started)*1000)
            if not response.ok:raise LocalCandidateBlock('LMSTUDIO_GENERATION_FAILED')
            payload=parse_model_json(_extract_content(response.metadata),expected_ref=case['evidence_ref'])
            provenance=GenerationProvenance(prompt_ref='r02-04-synthetic-v1',profile_ref=req.profile_version,
                context_ref=case['evidence_ref'],network_used=True,external_api_used=False,
                latency_ms=elapsed,evidence_refs=(case['evidence_ref'],))
            candidate=create_candidate(request=req,payload={'stage_id':case['stage'],'content':payload['content'],
                'title':payload['title'],'evidence_refs':payload['evidence_refs']},
                origin=CandidateOrigin(kind=CandidateOriginKind.PROVIDER,provider_class=ProviderClass.LOCAL_MODEL,
                    provider_id='lmstudio',model_id=model),provenance=provenance,status=CandidateStatus.GENERATED,
                evaluation_summary={'source_write':False,'freeze_authority':False,
                    'human_review_required':True,'quality_evaluated':False})
            receipt={**spec,'status':'REAL_CANDIDATE_GENERATED_UNREVIEWED','network_calls':2,
                'latency_ms':elapsed,'candidate':candidate.to_dict(),
                'candidate_sha256':candidate.content_sha256,
                'token_count_observed':{'prompt':_usage(response.metadata, 'prompt_tokens'),
                    'output':_usage(response.metadata, 'completion_tokens')},'replayed':False}
            temporary=output_dir/(request_id+'.tmp')
            with temporary.open('x',encoding='utf-8') as stream:
                json.dump(receipt,stream,indent=2,ensure_ascii=False)
            os.replace(temporary,target)
            return receipt
        finally:
            lock.unlink(missing_ok=True)
