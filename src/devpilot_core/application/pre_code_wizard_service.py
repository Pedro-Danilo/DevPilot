from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
from copy import deepcopy
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devpilot_core.cli_models import CommandResult, ExitCode, Finding, Severity
from devpilot_core.guided_sdlc.step_action_advisor import AdvisorContext, ExecutionModeAdvisor
from devpilot_core.generation import DeterministicProductDefinitionProvider, GenerationRequest, artifact_type_for_stage, select_product_definition_dependency_profile
from devpilot_core.policy.path_guard import PathGuard
from devpilot_core.miasi.applicability import MIASIApplicabilityEvaluator
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validation.project_profile import ProjectFacts
from devpilot_core.rag.technical_context_profile import TechnicalSource, resolve_technical_context
from devpilot_core.validators.artifact import extract_headings, normalize_heading
from devpilot_core.validators.frontmatter import parse_frontmatter_text, validate_frontmatter_document
from devpilot_core.workspace.runtime_project_context import parse_project_yaml_metadata

from .artifact_lifecycle_service import ArtifactLifecycleService, ArtifactState
from .artifact_review_service import ArtifactReviewApplicationService
from .workspace_documents_service import WorkspaceDocumentsApplicationService
from .workspace_edit_plan_service import ZERO_SHA256
from .workspace_edit_execution_service import WorkspaceEditExecutionApplicationService
from .pre_code_technical_design import C02_STAGES, C02_MODEL, C02_SCHEMA, derive_technical_stage, validate_technical_artifact
from .pre_code_adr_bundle_service import ArchitectureAdrBundleService
from .r02_07_semantic import generate_local_guided, quality_findings, persist_owner_revision
from .r03_03_architecture import generate_local_architecture, persist_architecture_revision, architecture_quality
from .r03_04_quality_contract import candidate_quality, export_candidate_handoff
from .r03_04_tech_decision import inspect_technology_decisions
from .r03_04_local_authoring import (R0304LocalAuthoring, _OPTION, _sha as _r0304_sha,
    adr_prompt, compose_architecture, technology_prompt, validate_technology, validate_adr)
from .pre_code_semantic_model import (
    build_candidate_model,
    normalize_owner_model,
    prepare_draft_first_model,
    requirement_records,
    semantic_hash,
    unresolved_decisions_for_stage,
    validate_confirmed_model,
    validate_model_for_stage,
    validate_rendered_artifact,
)

CATALOG = Path('.devpilot/gsdlc/pre_code_wizard_catalog.json')
STORE_ROOT = Path('outputs/pre_code_wizard/gsdlc_05_e')
STRUCTURE_RECEIPT_ROOT = Path('outputs/pre_code_wizard/gsdlc_13_c_01')
REQUIRED_DOCUMENT_PARENTS = (
    Path('docs/00_product'),
    Path('docs/01_requirements'),
    Path('docs/02_architecture'),
    Path('docs/02_architecture/adrs'),
    Path('docs/03_security'),
    Path('docs/04_quality'),
)
DERIVATION_MODEL = 'deterministic-semantic-model-template-v3'
DERIVATION_SCHEMA = 'devpilot.gsdlc13c01.deterministic_derivation.v3'
_SHA = re.compile(r'^[0-9a-f]{64}$')


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_text(text: str) -> str:
    return str(text or '').replace('\r\n', '\n').replace('\r', '\n')


def _sha_text(text: str) -> str:
    return _sha_bytes(_canonical_text(text).encode('utf-8'))


def _require_current_business_need(record: dict[str, Any], current: dict[str, Any]) -> None:
    # Compare the parsed B0 field, not project.yaml bytes: comments, unrelated
    # metadata, EOL and prose whitespace do not change the business need.
    previous = record.get('business_need') or {}
    if not isinstance(previous.get('text'), str):
        raise ValueError('UX01_B_BUSINESS_NEED_UNVERIFIED')
    if ' '.join(previous['text'].split()) != ' '.join(current['text'].split()):
        raise ValueError('UX01_B_BUSINESS_NEED_DRIFT')


# Foreground service serialization prevents a completed inference from overwriting
# a concurrent Owner choice/revision made from an older state snapshot.
_TECH_ACTION_LOCK = threading.Lock()


def _serialized_technology_action(method):
    @wraps(method)
    def guarded(self, **kwargs):
        if not _TECH_ACTION_LOCK.acquire(blocking=False):
            return self._block('guided pre-code technology local authoring',
                               'UX01_B_ACTION_IN_PROGRESS', 'Operación en curso; consultar estado antes de continuar.')
        try:
            return method(self, **kwargs)
        finally:
            _TECH_ACTION_LOCK.release()
    return guarded


def _architecture_draft_quality(content: str, upstream: dict[str, str], required_headings: tuple[str, ...]) -> dict[str, Any]:
    """Advisory receipt for the *current* DRAFT, including the review profile.

    The ten model generation units are historical provenance, not the exact
    set of mandatory headings for the downstream ArtifactReview gate.
    """
    report = architecture_quality(content, upstream)
    headings = [normalize_heading(m.group(1)) for m in re.finditer(
        r'^##\s+(.+?)\s*$', _canonical_text(content), re.M)]
    missing = [item for item in required_headings
               if not any(normalize_heading(item) in name for name in headings)]
    for item in missing:
        report['checks'].append({'rule_id': 'ARTIFACT_PROFILE_REQUIRED_SECTION',
                                 'status': 'BLOCK',
                                 'message': f'Falta sección exigida por ArtifactReview: {item}.'})
    if missing:
        report['disposition'] = 'BLOCK'
    report['content_sha256'] = _sha_text(content)
    return report


class PreCodeWizardApplicationService:
    """Server-authoritative governed pre-code vertical slice.

    GSDLC-13-C extends the historical MANUAL/IMPORT surface with a deterministic
    local/no-API proposal mode for Vision/Scope/Requirements. Human review, diff,
    approval, apply and freeze remain unchanged and server-authoritative.

    Runtime drafts/state live under platform outputs and never write managed source
    until the inherited UOC-005 approval-bound apply executes. The service composes
    ArtifactLifecycle/ArtifactReview and StepActionAdvisor rather than bypassing
    their policies.
    """

    def __init__(self, platform_root: Path, *, documents: WorkspaceDocumentsApplicationService, reviews: ArtifactReviewApplicationService, executions: WorkspaceEditExecutionApplicationService, approval_auth_store=None) -> None:
        self.root = Path(platform_root).resolve()
        self.documents = documents
        self.reviews = reviews
        self.executions = executions
        self.adr_bundle = ArchitectureAdrBundleService(self.root, approval_auth_store=approval_auth_store)
        self.technology_authoring = R0304LocalAuthoring(self.root)
        self.lifecycle = ArtifactLifecycleService(self.root)
        self.profiles = ArtifactProfileRegistry(self.root)
        self.advisor = ExecutionModeAdvisor(self.root)
        self.miasi = MIASIApplicabilityEvaluator(self.root)
        self.catalog = self._load_catalog()
        self._stages = sorted((dict(x) for x in self.catalog['stages']), key=lambda x: int(x['order']))
        self._stage_by_id = {str(x['stage_id']): x for x in self._stages}
        self._lock = threading.RLock()

    def status(self, *, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        context = self._context()
        if isinstance(context, CommandResult): return context
        workspace_id, workspace_root = context
        state = self._load_state(workspace_id)
        projection = self._projection(state, workspace_id, workspace_root, effective_roles, workspace_scopes)
        if workspace_id in set(workspace_scopes):
            projection['r03_04_authoring'] = self._technology_public(state)
            try:
                projection['r03_04_authoring']['activity'] = self.technology_authoring.activity(workspace_id)
            except (ValueError,OSError,UnicodeError) as exc:
                projection['r03_04_authoring']['activity'] = [{'status':'BLOCK','error_code':str(exc)[:200]}]
        return self._pass('guided pre-code status', 'GSDLC05E_PRE_CODE_STATUS_PASS', 'Pre-code wizard state projected from server-authoritative runtime state.', {'pre_code': projection})

    def reconcile_structure(self, *, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        command='guided pre-code reconcile structure'
        context=self._context()
        if isinstance(context,CommandResult): return context
        workspace_id,workspace_root=context
        if 'owner' not in set(effective_roles):
            return self._block(command,'GSDLC13C01_STRUCTURE_OWNER_BLOCK','Owner role is required to reconcile governed document namespaces.')
        if workspace_id not in set(workspace_scopes):
            return self._block(command,'GSDLC13C01_STRUCTURE_SCOPE_BLOCK','Active workspace scope is required to reconcile governed document namespaces.',metadata={'workspace_id':workspace_id})
        return self._reconcile_governed_parents(workspace_id=workspace_id,workspace_root=workspace_root)

    def save_draft(self, *, stage_id: str, content: str, mode: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str], semantic_model: dict[str, Any] | None = None, model: str = "", regenerate: bool = False) -> CommandResult:
        command='guided pre-code save draft'
        context=self._context()
        if isinstance(context,CommandResult): return context
        workspace_id, workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        stage=self._stage_by_id.get(str(stage_id))
        if stage is None:return self._block(command,'GSDLC05E_STAGE_UNKNOWN_BLOCK','Unknown pre-code stage.')
        normalized_mode=str(mode or '').upper()
        if normalized_mode not in stage['allowed_modes']:
            return self._block(command,'GSDLC05E_MODE_POLICY_BLOCK','Selected authoring mode is not allowed for the current stage.',metadata={'stage_id':stage_id,'mode':normalized_mode})
        if normalized_mode not in {'MANUAL','IMPORT','DEVPL_MOCK','LOCAL_MODEL'}:
            return self._block(command,'GSDLC05E_MODE_BLOCK','Only governed MANUAL/IMPORT/DEVPL_MOCK/LOCAL_MODEL modes are available.')
        if regenerate and (normalized_mode!='LOCAL_MODEL' or stage_id!='architecture' or content.strip()):
            return self._block(command,'R0303_REGENERATION_SCOPE_DENY','Regeneración segmentada explícita solo para Architecture local sin contenido enviado.')
        state=self._load_state(workspace_id)
        adr_gate=self._adr_companion_gate(state=state,workspace_root=workspace_root,requested_stage_id=stage_id)
        if adr_gate is not None:return adr_gate
        current=self._current_stage(state)
        if current is None:
            return self._block(command,'GSDLC05E_ALREADY_READY_BLOCK','Pre-code wizard is already complete.')
        if current['stage_id'] != stage_id:
            return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Mandatory pre-code stages cannot be skipped.',metadata={'requested_stage':stage_id,'current_stage':current['stage_id']})
        row=self._stage_state(state,stage_id)
        derivation=None
        content=str(content or '')
        plan_invalidated=bool(row.get('plan_id') or row.get('approval_id'))
        if normalized_mode=='DEVPL_MOCK':
            if stage_id in C02_STAGES:
                semantic_result=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
                if semantic_model is not None and semantic_result is not None:
                    semantic_result=self._ensure_semantic_model(stage_id=stage_id,workspace_id=workspace_id,workspace_root=workspace_root,state=state,submitted=semantic_model)
                    if isinstance(semantic_result,CommandResult): return semantic_result
            else:
                semantic_result=self._ensure_semantic_model(stage_id=stage_id,workspace_id=workspace_id,workspace_root=workspace_root,state=state,submitted=semantic_model)
                if isinstance(semantic_result,CommandResult): return semantic_result
            owner_edit=bool(content.strip()) and str(row.get('mode') or '')=='DEVPL_MOCK' and row.get('status') in {'DRAFT','FINDINGS','APPROVAL_REQUIRED'} and semantic_model is None
            if owner_edit:
                content=_canonical_text(content)
                derivation=deepcopy(row.get('derivation') or {}) if isinstance(row.get('derivation'),dict) else {}
                generated_sha=str(derivation.get('generated_content_sha256') or row.get('content_sha256') or _sha_text(content))
                derivation.update({
                    'schema_id':str(derivation.get('schema_id') or (C02_SCHEMA if stage_id in C02_STAGES else DERIVATION_SCHEMA)),
                    'mode':'DEVPL_MOCK','provider':str(derivation.get('provider') or 'devpilot-local'),'model':str(derivation.get('model') or (C02_MODEL if stage_id in C02_STAGES else DERIVATION_MODEL)),
                    'network_used':False,'external_api_used':False,'cost_usd':0.0,
                    'generated_content_sha256':generated_sha,
                    'owner_edited':_sha_text(content)!=generated_sha,
                    'owner_edited_content_sha256':_sha_text(content),
                    'semantic_model_sha256':semantic_hash(semantic_result) if isinstance(semantic_result,dict) else derivation.get('semantic_model_sha256'),
                    'semantic_model_schema_id':semantic_result.get('schema_id') if isinstance(semantic_result,dict) else derivation.get('semantic_model_schema_id'),
                    'owner_semantic_reviewed':bool(semantic_result.get('owner_semantic_reviewed')) if isinstance(semantic_result,dict) else bool(derivation.get('owner_semantic_reviewed')),
                    'owner_review_required':True,'approval_required_before_source_write':True,
                })
            else:
                generated=self._derive_local_proposal(stage_id=stage_id,workspace_id=workspace_id,workspace_root=workspace_root,state=state)
                if isinstance(generated,CommandResult): return generated
                content,derivation=generated
        elif normalized_mode=='LOCAL_MODEL':
            if workspace_id not in set(workspace_scopes):
                return self._block(command,'R0207_WORKSPACE_SCOPE_DENY','Owner workspace scope required for local authoring.')
            if stage_id not in {'product-vision','scope','requirements','architecture'}:
                return self._block(command,'R0303_STAGE_DENY','Local model authoring is not enabled for this stage.')
            if row.get('status') in {'DRAFT','FINDINGS','APPROVAL_REQUIRED'} and content.strip() and str(row.get('mode'))=='LOCAL_MODEL':
                derivation=deepcopy(row.get('derivation') or {})
                derivation['owner_edited']=True
                derivation['owner_edited_content_sha256']=_sha_text(content)
                try:
                    if stage_id=='architecture':
                        derivation['owner_revision']=persist_architecture_revision(self.root,workspace_id=workspace_id,provenance=derivation,content=content)
                    else:
                        derivation['owner_revision']=persist_owner_revision(self.root,workspace_id=workspace_id,stage_id=stage_id,generation=derivation,content=content)
                except ValueError as exc:
                    return self._block(command,str(exc),'No se pudo conservar revisión Markdown inmutable.')
            elif row.get('status') in {'MISSING','DRAFT','FINDINGS'} and not content.strip():
                if stage_id=='architecture':
                    if row.get('status')!='MISSING':
                        if (not regenerate or row.get('status')!='DRAFT' or row.get('mode')!='LOCAL_MODEL'
                                or row.get('plan_id') or row.get('approval_id') or not str(row.get('content') or '').strip()):
                            return self._block(command,'R0303_ALTERNATIVE_POLICY_DENY','Solo se puede crear una alternativa explícita del DRAFT local no aprobado de Architecture; conserva la versión anterior.')
                    elif regenerate:
                        return self._block(command,'R0303_REGENERATION_MISSING_DENY','Una nueva generación inicial no es una regeneración.')
                    verified=[]; trusted_upstream={}
                    for source_id in ('product-vision','scope','requirements'):
                        source_row=self._stage_state(state,source_id)
                        source_path=workspace_root/str(self._stage_by_id[source_id]['relative_path'])
                        if source_row.get('status')!='FROZEN' or not source_path.is_file() or source_path.is_symlink():
                            return self._block(command,'R0303_UPSTREAM_NOT_FROZEN','Faltan artefactos upstream FROZEN verificados.')
                        source_bytes=source_path.read_bytes()
                        approved=str(source_row.get('approved_sha256') or '')
                        if not _SHA.fullmatch(approved) or _sha_bytes(source_bytes)!=approved:
                            return self._block(command,'R0303_UPSTREAM_HASH_DRIFT','El origen FROZEN cambió desde approval.')
                        verified.append(TechnicalSource(stage=source_id,path=str(self._stage_by_id[source_id]['relative_path']),raw_bytes=source_bytes,expected_sha256=approved,lifecycle='FROZEN'))
                        trusted_upstream[source_id]=_canonical_text(source_bytes.decode('utf-8-sig'))
                    project_yaml=workspace_root/'.devpilot/project.yaml'
                    if not project_yaml.is_file() or project_yaml.is_symlink():
                        return self._block(command,'R0303_PROJECT_CONTEXT_REQUIRED','No existe Project Context confiable.')
                    try:
                        metadata=parse_project_yaml_metadata(project_yaml)
                        context=resolve_technical_context(self.root,sources=tuple(verified),
                            facts=ProjectFacts(project_id=workspace_id,revision=1,product_has_ai=None))
                        context['actor'] = actor
                        context['business_need'] = str(metadata.get('business_need') or 'UNKNOWN')
                        context['business_need_source'] = {'source_id':'.devpilot/project.yaml',
                            'sha256':_sha_bytes(project_yaml.read_bytes())}
                        if regenerate:
                            import uuid
                            context['generation_epoch'] = (row.get('pending_generation_epoch') or uuid.uuid4().hex)
                            context['parent_candidate_id'] = row.get('content_sha256')
                        generated=generate_local_architecture(self.root,workspace_id=workspace_id,
                            project_name=str(metadata.get('project_name') or workspace_id),
                            context=context,upstream=trusted_upstream,model=model,
                            allow_successor=regenerate)
                    except (ValueError,OSError,UnicodeError,KeyError) as exc:
                        return self._block(command,'R0303_GENERATION_BLOCK',str(exc))
                    if generated.get('partial'):
                        if context.get('generation_epoch'):
                            row['pending_generation_epoch'] = context['generation_epoch']
                            self._write_state(workspace_id,state)
                        return self._pass(command,'R0303_SEGMENT_PROGRESS_PASS',
                            'Unidad Architecture conservada; continúa generación acotada sin escribir source.',
                            {'segmented_progress':generated['progress'],'source_mutations_performed':False})
                    content=generated['content'];derivation=generated['provenance']
                    row.pop('pending_generation_epoch',None)
                    derivation['generation_epoch'] = context.get('generation_epoch') or derivation.get('input_hash')
                    derivation['business_need_source'] = context['business_need_source']
                    if regenerate:
                        derivation['predecessor_content_sha256']=_sha_text(str(row.get('content') or ''))
                        derivation['owner_requested_alternative']=True
                else:
                # An explicit empty-body request on an unapproved local DRAFT is
                # a new semantic alternative; the previous Markdown and receipt
                # stay immutable. Never regenerate an approval-ready or FROZEN row.
                    if row.get('status')!='MISSING' and str(row.get('mode'))!='LOCAL_MODEL':
                        return self._block(command,'R0207_ALTERNATIVE_MODE_DENY','Solo se puede crear una alternativa de un DRAFT local existente.')
                    if row.get('plan_id') or row.get('approval_id'):
                        return self._block(command,'R0207_ALTERNATIVE_PLAN_DENY','El DRAFT tiene plan o approval; no regenerar.')
                    try:
                        predecessor_sha=str((row.get('derivation') or {}).get('candidate_sha256') or '') if row.get('status')!='MISSING' else ''
                        if predecessor_sha and (not re.fullmatch(r'[0-9a-f]{64}',predecessor_sha) or _sha_text(str(row.get('content') or ''))!=predecessor_sha):
                            predecessor_sha=''
                        generated=generate_local_guided(self.root,workspace_id=workspace_id,
                            workspace_root=workspace_root, stage_id=stage_id,model=model,
                            predecessor_sha256=predecessor_sha,
                            previous_content=str(row.get('content') or '') if predecessor_sha else '')
                    except ValueError as exc:
                        return self._block(command,str(exc),'Local model candidate could not be generated safely.')
                    if generated.get('partial'):
                        return self._pass(command,'R0207_SEGMENT_PROGRESS_PASS',
                            'Unidad de Requirements validada; continuar generación segmentada. No existe un nuevo DRAFT todavía.',
                            {'segmented_progress':generated['progress'],'source_mutations_performed':False})
                    content=generated['content']
                    derivation=generated['provenance']
                    if row.get('status')!='MISSING' and row.get('derivation',{}).get('candidate_sha256')==derivation.get('candidate_sha256'):
                        return self._block(command,'R0207_ALTERNATIVE_UNCHANGED','La propuesta ya existe; edita el Markdown o selecciona otro modelo. No se duplicó la inferencia.')
            else:
                return self._block(command,'R0207_GENERATION_RETRY_DENY','Use the existing local model DRAFT for review/edit; do not silently regenerate.')
        elif not content.strip():
            return self._block(command,'GSDLC05E_EMPTY_DRAFT_BLOCK','Draft content is required for MANUAL/IMPORT.')
        structure=self._reconcile_governed_parents(workspace_id=workspace_id,workspace_root=workspace_root)
        if not structure.ok:return structure
        target=(workspace_root/str(stage['relative_path'])).resolve()
        try: target.relative_to(workspace_root.resolve())
        except ValueError:return self._block(command,'GSDLC05E_TARGET_SCOPE_BLOCK','Pre-code artifact escaped the active workspace.')
        if not target.parent.is_dir() or target.parent.is_symlink():
            return self._block(command,'GSDLC05E_TARGET_PARENT_BLOCK','The project bootstrap must provide the governed document parent directory before authoring.',metadata={'relative_path':stage['relative_path']})
        base_sha=_sha_bytes(target.read_bytes()) if target.is_file() else ZERO_SHA256
        if normalized_mode=='LOCAL_MODEL' and stage_id=='architecture':
            # Recalculate after every Owner edit. Never display a BLOCK from a
            # previous Ollama candidate as if it described the saved revision.
            verified_sources: dict[str, str] = {}
            frozen_drift = False
            for source_id in ('product-vision','scope','requirements'):
                source_row=self._stage_state(state,source_id)
                source_path=workspace_root/str(self._stage_by_id[source_id]['relative_path'])
                try:
                    if source_row.get('status')!='FROZEN' or not source_path.is_file() or source_path.is_symlink():
                        frozen_drift=True; continue
                    source_bytes=source_path.read_bytes()
                    if _sha_bytes(source_bytes)!=source_row.get('approved_sha256'):
                        frozen_drift=True; continue
                    verified_sources[source_id]=_canonical_text(source_bytes.decode('utf-8-sig'))
                except (OSError,UnicodeError):
                    frozen_drift=True
            profile=self.profiles.select(Path(str(stage['relative_path'])))
            fresh=_architecture_draft_quality(content,verified_sources,profile.required_headings)
            if frozen_drift:
                fresh['checks'].append({'rule_id':'FROZEN_SOURCE_UNAVAILABLE',
                                        'status':'BLOCK',
                                        'message':'Una fuente FROZEN no coincide con su estado gobernado.'})
                fresh['disposition']='BLOCK'
            derivation=dict(derivation or {})
            epoch = str(derivation.get('generation_epoch') or derivation.get('input_hash') or _sha_text(content))
            derivation['generation_epoch'] = epoch
            previous_quality = derivation.get('ux01_quality') or {}
            derivation['ux01_quality'] = candidate_quality(
                'architecture',content,frozen=verified_sources,
                hashes={k:_sha_text(v) for k,v in verified_sources.items()},
                candidate_id=_sha_text(content),epoch=epoch,actor=actor,
                model=str(derivation.get('model') or 'UNKNOWN'),
                parent_id=(derivation.get('owner_revision') or {}).get('parent_candidate_sha256') or derivation.get('predecessor_content_sha256'),
                before_owner=previous_quality.get('before_owner') if derivation.get('owner_edited') else None)
            project_file = workspace_root/'.devpilot/project.yaml'
            if project_file.is_file() and not project_file.is_symlink():
                derivation['ux01_quality']['current']['business_need'] = {
                    'source_id':'.devpilot/project.yaml','sha256':_sha_bytes(project_file.read_bytes()),
                    'text':str(parse_project_yaml_metadata(project_file).get('business_need') or 'UNKNOWN')}
            derivation['quality_receipt']=fresh
            derivation['technology_decision_receipt']=inspect_technology_decisions(
                content,source_refs=derivation.get('upstream_refs') or derivation.get('source_refs') or [],
                lifecycle='DRAFT')
        artifact_id='precode_'+hashlib.sha256(f"{workspace_id}|{stage_id}|{_sha_bytes(content.encode())}".encode()).hexdigest()[:24]
        lifecycle_source='AGENT_ASSISTED' if normalized_mode in {'DEVPL_MOCK','LOCAL_MODEL'} else normalized_mode
        draft=self.lifecycle.create_draft(
            artifact_id=artifact_id,relative_path=str(stage['relative_path']),content=content,source_type=lifecycle_source,
            base_commit=self._base_commit(workspace_root),actor=actor,actor_role=actor_role,session_principal=session_principal,
            reviewer=actor,reviewer_role=actor_role,source_label='DevPilot local model candidate / Owner-reviewed' if normalized_mode=='LOCAL_MODEL' else ('DevPilot deterministic local proposal / Owner-reviewed' if normalized_mode=='DEVPL_MOCK' else f'GSDLC-05-E {normalized_mode} browser DRAFT'),
            source_reference=f'pre-code:{workspace_id}:{stage_id}:{normalized_mode.lower()}',
        )
        if not draft.ok:return draft
        row.update({'status':'DRAFT','mode':normalized_mode,'content':content,'content_sha256':_sha_bytes(content.encode()),'base_sha256':base_sha,'artifact':draft.data['artifact'],'derivation':derivation,'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':_now()})
        state['status']='IN_PROGRESS'; state['updated_at']=_now(); self._write_state(workspace_id,state)
        if plan_invalidated:
            self._append_trace(workspace_id,{'event':'DRAFT_REOPENED_AND_PLAN_INVALIDATED','stage_id':stage_id,'actor':actor,'at':_now()})
        return self._pass(command,'GSDLC05E_DRAFT_SAVED_PASS','Server-authoritative DRAFT persisted outside managed source; source mutation remains false.',{'stage':self._public_stage(row,stage),'semantic_model':deepcopy(state.get('semantic_model')) if isinstance(state.get('semantic_model'),dict) else None,'source_mutations_performed':False,'plan_invalidated':plan_invalidated,'structure_reconciliation':structure.data.get('structure_reconciliation')})

    def start_review(self, *, stage_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str]) -> CommandResult:
        command='guided pre-code review'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id)
        adr_gate=self._adr_companion_gate(state=state,workspace_root=workspace_root,requested_stage_id=stage_id)
        if adr_gate is not None:return adr_gate
        current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only the current mandatory stage can enter review.')
        row=self._stage_state(state,stage_id)
        if stage_id=='architecture' and row.get('mode')=='LOCAL_MODEL' and not self._technology_binding_valid(state,row):
            return self._block(command,'R0304_TECH_RECONCILIATION_REQUIRED',
                'Genera Technology Options con modelo local, selecciona una opción, genera ADR y concilia Architecture antes de validar.')
        # An existing approval must never be rebound to a newly generated plan.
        # An unapproved APPROVAL_REQUIRED stage may be re-reviewed explicitly
        # when its immutable edit plan has expired or vanished on API restart.
        status=str(row.get('status') or '')
        renewal=status=='APPROVAL_REQUIRED' and not row.get('approval_id')
        if (status not in {'DRAFT','FINDINGS'} and not renewal) or not isinstance(row.get('artifact'),dict):
            return self._block(command,'GSDLC05E_DRAFT_REQUIRED_BLOCK',
                'Only a DRAFT/FINDINGS or unapproved APPROVAL_REQUIRED stage can be reviewed.')
        if renewal and row['artifact'].get('state')!='DRAFT':
            return self._block(command,'GSDLC05E_RENEWAL_ARTIFACT_STATE_BLOCK',
                'Plan renewal requires the preserved server-authoritative DRAFT artifact.')
        if row.get('mode')=='LOCAL_MODEL' and self._candidate_content_binding(row)['status']!='PASS':
            return self._block(command,'R0207_CANDIDATE_CONTENT_BINDING_BLOCK',
                               'El Markdown visible no concuerda con el candidato/revisión y el hash persistido; detener antes del approval.')
        if row.get('mode')=='LOCAL_MODEL' and stage_id=='architecture':
            source_text={}
            for source_id in ('product-vision','scope','requirements'):
                frozen=self._stage_state(state,source_id)
                path=workspace_root/str(self._stage_by_id[source_id]['relative_path'])
                if (frozen.get('status')!='FROZEN' or not path.is_file() or path.is_symlink()
                        or _sha_bytes(path.read_bytes()) != frozen.get('approved_sha256')):
                    return self._block(command,'R0303_REVIEW_UPSTREAM_DRIFT','No se puede revisar Architecture con upstream cambiado.')
                source_text[source_id]=_canonical_text(path.read_text(encoding='utf-8-sig'))
            report=architecture_quality(str(row.get('content') or ''),source_text)
            if report['disposition']=='BLOCK':
                return self._block(command,'R0303_ARCH_QUALITY_BLOCK','Architecture tiene contradicciones o cobertura material faltante.',metadata={'quality_receipt':report})
            report['content_sha256']=_sha_text(str(row.get('content') or ''))
            row['derivation']['quality_receipt']=report
            decision_report=inspect_technology_decisions(
                str(row.get('content') or ''),
                source_refs=(row.get('derivation') or {}).get('upstream_refs') or
                            (row.get('derivation') or {}).get('source_refs') or [],
                lifecycle='DRAFT')
            row['derivation']['technology_decision_receipt']=decision_report
            if decision_report['status']=='BLOCK':
                return self._block(command,'R0304_TECH_DECISION_MATERIAL_BLOCK',
                    'Technology/ADR propone una acción material o una aprobación no fundada.',
                    metadata={'findings':[x for x in decision_report['findings'] if x['severity']=='BLOCK']})
        if workspace_id=='admon_empresa_unipersonal_con_agentes' and stage_id in {'product-vision','scope','requirements'}:
            # Derive review facts from the same trusted B0 as generation; never
            # trust claims of source authorization inside model Markdown.
            source_path=workspace_root/'.devpilot/project.yaml'
            if not source_path.is_file() or source_path.is_symlink():
                return self._block(command,'R0207_REVIEW_SOURCE_UNAVAILABLE','B0 confiable no disponible durante revisión.')
            try:
                source_need=str(parse_project_yaml_metadata(source_path).get('business_need') or '')
            except (OSError,ValueError,TypeError,KeyError):
                return self._block(command,'R0207_REVIEW_SOURCE_UNAVAILABLE','No se pudo recuperar B0 para validación.')
            if not source_need.strip():
                return self._block(command,'R0207_REVIEW_SOURCE_UNAVAILABLE','B0 vacío: revisión bloqueada.')
            quality_scope=''
            if stage_id=='requirements':
                # FROZEN is a runtime lifecycle authority, not the YAML status
                # string inside a versioned document. Validate both identity and
                # hash before using the source for the quality decision.
                from .r02_07_semantic import _read_frozen, _sha
                try:
                    scope_hash,_=_read_frozen(self.root,workspace_id,'scope')
                    scope_file=workspace_root/'docs/00_product/mvp_scope.md'
                    if scope_file.is_symlink() or not scope_file.is_file():raise ValueError('scope_unavailable')
                    scope_blob=scope_file.read_bytes()
                    if _sha(scope_blob)!=scope_hash:raise ValueError('scope_drift')
                    quality_scope=scope_blob.decode('utf-8-sig')
                except (OSError,UnicodeError,ValueError):
                    return self._block(command,'R0218_REVIEW_FROZEN_SCOPE_UNAVAILABLE',
                        'No se puede comprobar el Scope FROZEN para evaluar Requirements.')
            professional=quality_findings(stage_id,str(row.get('content') or ''),source_need=source_need,scope_text=quality_scope)
            if professional:
                findings=[Finding('R0207_DOCUMENT_QUALITY_BLOCK','El documento no cumple el perfil profesional de esta etapa.',Severity.BLOCK,metadata={'quality_findings':professional})]
                findings.extend(Finding(item['id'],item['message'],Severity.BLOCK) for item in professional)
                return CommandResult(command,False,ExitCode.BLOCK,'Revisión documental bloqueada; corregir el DRAFT sin modificar source.',data={},findings=findings)
        if str(row.get('mode') or '')=='DEVPL_MOCK':
            model=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
            if stage_id in C02_STAGES:
                req_stage=self._stage_by_id['requirements']; req_path=workspace_root/str(req_stage['relative_path'])
                requirements_text=_canonical_text(req_path.read_text(encoding='utf-8')) if req_path.is_file() else ''
                technical_findings=validate_technical_artifact(stage_id,str(row.get('content') or ''),requirements_text)
                if technical_findings:
                    findings=[Finding('GSDLC13C02_TECHNICAL_QUALITY_BLOCK','C-02 technical quality gate blocked review before an approval-ready plan could be created.',Severity.BLOCK,metadata={'technical_findings':technical_findings})]
                    findings.extend(Finding(str(item.get('id') or 'TECHNICAL_QUALITY_DETAIL_BLOCK'),str(item.get('message') or 'Technical quality finding.'),Severity.BLOCK,metadata={k:v for k,v in item.items() if k not in {'id','message'}}) for item in technical_findings)
                    return CommandResult(command,False,ExitCode.BLOCK,'C-02 technical quality gate blocked review before an approval-ready plan could be created.',data={},findings=findings)
            else:
                semantic_findings=validate_model_for_stage(model or {},stage_id) + validate_rendered_artifact(stage_id,str(row.get('content') or ''),model or {})
                if semantic_findings:
                    findings=[Finding('GSDLC13C01_SEMANTIC_QUALITY_BLOCK','Semantic quality gate blocked review before an approval-ready plan could be created.',Severity.BLOCK,metadata={'semantic_findings':semantic_findings})]
                    findings.extend(Finding(str(item.get('id') or 'SEMANTIC_QUALITY_DETAIL_BLOCK'),str(item.get('message') or 'Semantic quality finding.'),Severity.BLOCK,metadata={k:v for k,v in item.items() if k not in {'id','message'}}) for item in semantic_findings)
                    return CommandResult(command,False,ExitCode.BLOCK,'Semantic quality gate blocked review before an approval-ready plan could be created.',data={},findings=findings)
        # A corrected draft always starts a new lifecycle record; persisted row artifact is DRAFT.
        result=self.reviews.start_runtime_draft(source_kind=str(row.get('mode') or 'MANUAL'),source_ref=f'pre-code:{workspace_id}:{stage_id}',artifact=deepcopy(row['artifact']),relative_path=str(self._stage_by_id[stage_id]['relative_path']),content=str(row.get('content') or ''),base_sha=str(row.get('base_sha256') or ZERO_SHA256),actor=actor,actor_role=actor_role,session_principal=session_principal)
        review=(result.data or {}).get('review') if isinstance(result.data,dict) else None
        if isinstance(review,dict):
            row['review_id']=review.get('review_id'); row['status']=str(review.get('status') or 'FINDINGS'); row['findings']=list(review.get('findings') or []); row['validation']=dict(review.get('validation') or {}); row['updated_at']=_now()
            # A failed successor review must not retain an obsolete plan/hash/diff.
            row['plan_id']=None; row['plan_hash']=None; row['diff']=None
            plan=review.get('plan') if isinstance(review.get('plan'),dict) else None
            if plan:
                row['plan_id']=plan.get('plan_id'); row['plan_hash']=plan.get('plan_hash'); row['diff']=plan.get('diff') or plan.get('unified_diff') or plan.get('preview')
            self._write_state(workspace_id,state)
        return result

    def request_approval(self, *, stage_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], reason: str) -> CommandResult:
        command='guided pre-code approval request'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,_=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only current stage can request approval.')
        row=self._stage_state(state,stage_id)
        if stage_id=='architecture' and row.get('mode')=='LOCAL_MODEL' and not self._technology_binding_valid(state,row):
            return self._block(command,'R0304_TECH_APPROVAL_BINDING_BLOCK','El plan Architecture no incluye una elección L/ADR actual y verificable. No reutilices un plan anterior.')
        if row.get('status')!='APPROVAL_REQUIRED' or not row.get('plan_id') or not row.get('plan_hash'):
            return self._block(command,'GSDLC05E_APPROVAL_PLAN_REQUIRED_BLOCK','Current stage must pass validation and produce an immutable plan before approval.')
        result=self.executions.request_apply_approval(plan_id=str(row['plan_id']),plan_hash=str(row['plan_hash']),actor=actor,reason=str(reason or 'Approve governed pre-code artifact apply.'),ttl_minutes=30)
        if result.ok:
            approval=(result.data or {}).get('approval') if isinstance(result.data,dict) else None
            approval_id=str((approval or {}).get('approval_id') or (result.data or {}).get('approval_id') or '')
            if not approval_id:
                # ApprovalApplicationService payloads historically expose the record under approval.
                candidates=[v for v in (result.data or {}).values() if isinstance(v,dict) and str(v.get('approval_id') or '')]
                approval_id=str(candidates[0].get('approval_id')) if candidates else ''
            if not approval_id:return self._block(command,'GSDLC05E_APPROVAL_ID_MISSING_BLOCK','Approval store did not return an approval id.')
            row['approval_id']=approval_id; row['updated_at']=_now(); self._write_state(workspace_id,state)
            data=dict(result.data or {}); data['pre_code']={'stage_id':stage_id,'approval_id':approval_id,'plan_id':row['plan_id'],'plan_hash':row['plan_hash']}
            return CommandResult(command,True,ExitCode.PASS,'Approval request is bound to current immutable plan.',data=data,findings=result.findings)
        return result

    def apply(self, *, stage_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str]) -> CommandResult:
        command='guided pre-code apply'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,_=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only current stage can be applied.')
        row=self._stage_state(state,stage_id)
        if stage_id=='architecture' and row.get('mode')=='LOCAL_MODEL' and not self._technology_binding_valid(state,row):
            return self._block(command,'R0304_TECH_APPLY_BINDING_BLOCK','Architecture/Technology/ADR cambió desde el plan; preparar una revisión sucesora.')
        required=['plan_id','plan_hash','approval_id','review_id']
        if row.get('status')!='APPROVAL_REQUIRED' or any(not row.get(k) for k in required):return self._block(command,'GSDLC05E_APPLY_BINDING_BLOCK','Current stage lacks review/plan/approval binding.')
        result=self.executions.apply(plan_id=str(row['plan_id']),plan_hash=str(row['plan_hash']),approval_id=str(row['approval_id']),actor=actor)
        if result.ok:
            execution=dict((result.data or {}).get('execution') or {}); execution_id=str(execution.get('execution_id') or ((result.data or {}).get('summary') or {}).get('execution_id') or '')
            if not execution_id:return self._block(command,'GSDLC05E_EXECUTION_ID_MISSING_BLOCK','Approved apply returned no execution id.')
            row['execution_id']=execution_id; row['status']='APPLIED'; row['updated_at']=_now(); self._write_state(workspace_id,state)
            data=dict(result.data or {}); data['pre_code']={'stage_id':stage_id,'review_id':row['review_id'],'execution_id':execution_id,'approval_id':row['approval_id']}
            return CommandResult(command,True,ExitCode.PASS,'Approval-bound source apply completed; freeze is the next mandatory action.',data=data,findings=result.findings)
        return result

    def freeze(self, *, stage_id: str, review_id: str, execution_id: str, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        command='guided pre-code freeze'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id); current=self._current_stage(state)
        if current is None or current['stage_id']!=stage_id:return self._block(command,'GSDLC05E_STAGE_SKIP_BLOCK','Only the current mandatory stage can be frozen.')
        row=self._stage_state(state,stage_id)
        if stage_id=='architecture' and row.get('mode')=='LOCAL_MODEL' and not self._technology_binding_valid(state,row):
            return self._block(command,'R0304_TECH_FREEZE_BINDING_BLOCK','No congelar Architecture con decisiones tecnológicas no conciliadas.')
        if row.get('status') != 'APPLIED':
            return self._block(command,'GSDLC05E_APPLY_REQUIRED_BLOCK','Freeze requires the current stage to have an approved applied execution.')
        if str(row.get('review_id') or '')!=str(review_id or '') or str(row.get('execution_id') or '')!=str(execution_id or ''):
            return self._block(command,'GSDLC05E_REVIEW_BINDING_BLOCK','Freeze review id does not match current stage review.')
        result=self.reviews.freeze(review_id=review_id,execution_id=execution_id,actor=actor,actor_role=actor_role,session_principal=session_principal)
        if not result.ok:return result
        review=dict((result.data or {}).get('review') or {})
        if review.get('status')!='FROZEN':return self._block(command,'GSDLC05E_FREEZE_POSTCONDITION_BLOCK','Artifact review did not reach FROZEN.')
        row.update({'status':'FROZEN','execution_id':execution_id,'approval_id':review.get('approval_id'),'approved_sha256':review.get('approved_sha256'),'artifact':review.get('artifact'),'content':None,'updated_at':_now()})
        self._append_trace(workspace_id,{'event':'STAGE_FROZEN','stage_id':stage_id,'order':current['order'],'actor':actor,'actor_role':actor_role,'relative_path':current['relative_path'],'review_id':review_id,'execution_id':execution_id,'approval_id':review.get('approval_id'),'approved_sha256':review.get('approved_sha256'),'at':_now()})
        next_stage=self._current_stage(state)
        if next_stage is None:
            readiness=self._readiness_payload(state,workspace_id,workspace_root)
            state['status']='PRE_CODE_READY' if readiness['status']=='PASS' else 'BLOCKED'
            state['readiness']=readiness
            state['completed_at']=_now() if readiness['status']=='PASS' else None
        else:
            state['status']='IN_PROGRESS'
        state['updated_at']=_now(); self._write_state(workspace_id,state)
        projection=self._projection(state,workspace_id,workspace_root,effective_roles,workspace_scopes)
        return self._pass(command,'GSDLC05E_STAGE_FROZEN_PASS','Stage frozen through approval-bound apply; wizard advanced without skip.',{'pre_code':projection,'review':review})

    def reopen_c01_for_retest(self, *, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str], reason: str) -> CommandResult:
        """Governed runtime-only reset of C-01 for an exact selective retest.

        Preserves managed source bytes and archives the prior runtime state/trace.
        This is intentionally not exposed as a normal-user HTTP route.
        """
        command='guided pre-code reopen C-01 retest'
        context=self._context()
        if isinstance(context,CommandResult): return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        if workspace_id not in set(workspace_scopes):
            return self._block(command,'GSDLC13C01_RETEST_SCOPE_BLOCK','Active workspace scope is required for governed C-01 retest reopen.',metadata={'workspace_id':workspace_id})
        state=self._load_state(workspace_id)
        c01=('product-vision','scope','requirements')
        for stage_id in c01:
            row=self._stage_state(state,stage_id)
            if row.get('status')!='FROZEN':
                return self._block(command,'GSDLC13C01_RETEST_FROZEN_REQUIRED_BLOCK','C-01 retest reopen requires all three prior C-01 stages to be FROZEN.',metadata={'stage_id':stage_id,'status':row.get('status')})
            stage=self._stage_by_id[stage_id]; target=workspace_root/str(stage['relative_path'])
            approved=str(row.get('approved_sha256') or '')
            actual=_sha_bytes(target.read_bytes()) if target.is_file() else ''
            if not _SHA.fullmatch(approved) or actual!=approved:
                return self._block(command,'GSDLC13C01_RETEST_SOURCE_DRIFT_BLOCK','C-01 retest reopen refused because a prior FROZEN source no longer matches its approved bytes.',metadata={'stage_id':stage_id,'approved_sha256':approved or None,'actual_sha256':actual or None})
        current=self._current_stage(state)
        if current is None or current.get('stage_id')!='architecture':
            return self._block(command,'GSDLC13C01_RETEST_BOUNDARY_BLOCK','C-01 retest reopen is allowed only at the post-Requirements boundary before Architecture starts.',metadata={'current_stage_id':current.get('stage_id') if current else None})
        archive_root=self._state_path(workspace_id).parent/'history'
        archive_root.mkdir(parents=True,exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        state_archive=archive_root/f'c01_before_retest_{stamp}_state.json'
        state_archive.write_text(json.dumps(state,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
        trace_path=self._trace_path(workspace_id)
        trace_archive=None
        if trace_path.is_file():
            trace_archive=archive_root/f'c01_before_retest_{stamp}_trace.jsonl'
            trace_archive.write_bytes(trace_path.read_bytes())
        for stage_id in c01:
            prior=deepcopy(self._stage_state(state,stage_id))
            row=self._stage_state(state,stage_id)
            row.clear(); row.update({
                'stage_id':stage_id,'status':'MISSING','mode':None,'content_sha256':None,
                'base_sha256':prior.get('approved_sha256'),'artifact':None,'derivation':None,
                'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,
                'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':_now(),
                'retest_baseline_approved_sha256':prior.get('approved_sha256'),
            })
        state['semantic_model']=None; state['status']='IN_PROGRESS'; state['completed_at']=None; state.pop('readiness',None); state['updated_at']=_now()
        self._write_state(workspace_id,state)
        event={'event':'C01_RETEST_REOPENED','actor':actor,'actor_role':actor_role,'reason':str(reason or 'Selective retest after approved corrective'),'state_archive':str(state_archive.relative_to(self.root)).replace('\\','/'),'trace_archive':str(trace_archive.relative_to(self.root)).replace('\\','/') if trace_archive else None,'project_source_mutations':0,'at':_now()}
        self._append_trace(workspace_id,event)
        return self._pass(command,'GSDLC13C01_RETEST_REOPEN_PASS','C-01 runtime state reopened for an exact selective retest; prior evidence archived and managed project source bytes preserved.',{'workspace_id':workspace_id,'state_archive':event['state_archive'],'trace_archive':event['trace_archive'],'project_source_mutations':0})

    @_serialized_technology_action
    def technology_action(self, *, action: str, actor: str, actor_role: str,
                          session_principal: str, effective_roles: list[str],
                          workspace_scopes: list[str], option_id: str = '',
                          model: str = '', successor: bool = False, content: str = '',
                          artifact_kind: str = 'architecture', expected_sha256: str = '',
                          generation_epoch: str = '') -> CommandResult:
        """One governed UI endpoint for the four explicit R03-04 authoring actions."""
        command = 'guided pre-code technology local authoring'
        context = self._context()
        if isinstance(context, CommandResult): return context
        workspace_id, workspace_root = context
        identity = self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None: return identity
        if workspace_id not in set(workspace_scopes):
            return self._block(command,'R0304_WORKSPACE_SCOPE_DENY','La sesión Owner no tiene alcance al proyecto activo.')
        state = self._load_state(workspace_id)
        current = self._current_stage(state)
        row = self._stage_state(state,'architecture')
        if not current or current['stage_id']!='architecture' or row.get('mode')!='LOCAL_MODEL':
            return self._block(command,'R0304_LOCAL_ARCHITECTURE_REQUIRED','Las opciones requieren Architecture LOCAL_MODEL como etapa actual.')
        if row.get('status') not in ('DRAFT','APPROVAL_REQUIRED') or row.get('approval_id'):
            return self._block(command,'R0304_ARCHITECTURE_LOCKED','Architecture ya tiene approval o fue aplicada; no reescribir decisiones sin sucesor gobernado.')
        if not str(row.get('content') or '').strip() or _sha_text(str(row['content']))!=str(row.get('content_sha256') or ''):
            return self._block(command,'R0304_ARCHITECTURE_CANDIDATE_DRIFT','El Markdown Architecture no coincide con su estado persistido.')
        authoring = dict(state.get('r03_04_authoring') or {})
        tech = dict(authoring.get('technology') or {})
        selected = str(authoring.get('selected_option_id') or '')
        adr = dict(authoring.get('adr') or {})
        initial_arch_sha = row['content_sha256']
        initial_arch_status = row.get('status')
        try:
            frozen = self._r0304_frozen_context(state,workspace_root)
            hashes = {key:_sha_text(value) for key,value in frozen.items()}
            epoch = str((row.get('derivation') or {}).get('generation_epoch') or
                        (row.get('derivation') or {}).get('input_hash') or row['content_sha256'])
            if generation_epoch and generation_epoch != epoch:
                raise ValueError('UX01_B_STALE_EPOCH')
            expected_current = row['content_sha256']
            if action in ('select_option','owner_revise_options') or (action == 'export_handoff' and artifact_kind == 'technology_options'):
                expected_current = tech.get('candidate_sha256')
            elif action == 'owner_revise_adr' or (action == 'export_handoff' and artifact_kind == 'adr'):
                expected_current = adr.get('candidate_sha256')
            if expected_sha256 and expected_sha256 != expected_current:
                raise ValueError('UX01_B_STALE_CANDIDATE')
            if action != 'generate_options' and tech.get('generation_epoch') and tech['generation_epoch'] != epoch:
                raise ValueError('UX01_B_STALE_TECHNOLOGY_EPOCH')
            project_file = workspace_root/'.devpilot/project.yaml'
            if not project_file.is_file() or project_file.is_symlink():
                raise ValueError('R0304_PROJECT_CONTEXT_REQUIRED')
            metadata = parse_project_yaml_metadata(project_file)
            business_need = {'source_id':'.devpilot/project.yaml',
                             'sha256':_sha_bytes(project_file.read_bytes()),
                             'text':str(metadata.get('business_need') or 'UNKNOWN')}
            quality_context = {'frozen':frozen, 'hashes':hashes, 'actor':actor,
                               'business_need':business_need}
            if action in ('select_option', 'generate_adr', 'reconcile',
                          'owner_revise_options', 'owner_revise_adr'):
                _require_current_business_need((tech.get('quality') or {}).get('current', {}), business_need)
                if action in ('reconcile', 'owner_revise_adr'):
                    _require_current_business_need((adr.get('quality') or {}).get('current', {}), business_need)
            if action == 'adr_not_applicable':
                if selected or adr or len(content.strip()) < 35:
                    raise ValueError('UX01_B_ADR_MATERIALITY_REQUIRES_OWNER_RATIONALE')
                authoring['adr_applicability'] = {'status':'NOT_APPLICABLE',
                    'reason':content.strip(),'actor':actor,'at':_now(),
                    'architecture_sha256':row['content_sha256'],'generation_epoch':epoch}
                authoring['status'] = 'ADR_NOT_APPLICABLE'
                state['r03_04_authoring'] = authoring
                row.setdefault('derivation', {})['generation_epoch'] = epoch
                self._write_state(workspace_id,state)
                return self._pass(command,'UX01_B_ADR_NOT_APPLICABLE',
                    'Owner registró ausencia de decisión material; ningún ADR generado.',
                    {'adr_applicability':authoring['adr_applicability'],'source_mutations_performed':False})
            if action == 'export_handoff':
                if artifact_kind == 'architecture':
                    body = str(row['content'])
                    quality = (row.get('derivation') or {}).get('ux01_quality')
                else:
                    target = tech if artifact_kind == 'technology_options' else adr if artifact_kind == 'adr' else None
                    if not target:
                        raise ValueError('UX01_B_HANDOFF_CANDIDATE_MISSING')
                    body = self.technology_authoring.bound_candidate(workspace_id,target)
                    quality = target.get('quality')
                if not quality:
                    raise ValueError('UX01_B_HANDOFF_QUALITY_MISSING')
                if {x['source_id']:x['sha256'] for x in quality['current']['sources']} != hashes:
                    raise ValueError('UX01_B_HANDOFF_SOURCE_DRIFT')
                _require_current_business_need(quality['current'], business_need)
                if quality['current']['generation_epoch'] != epoch:
                    raise ValueError('UX01_B_HANDOFF_EPOCH_DRIFT')
                quality = deepcopy(quality)
                quality['current']['selected_owner_decision'] = {
                    'option_id':selected or 'UNKNOWN',
                    'sha256':authoring.get('selected_technology_sha256') or 'UNKNOWN',
                    'immutable':True}
                packet = export_candidate_handoff(quality,body)
                return self._pass(command,'UX01_B_OFFLINE_HANDOFF_EXPORTED',
                    'Paquete offline; requiere revisión Owner, sin certificación profesional.',
                    {'handoff':packet,'source_mutations_performed':False})
            if action in ('select_option','generate_adr','owner_revise_adr','reconcile'):
                original_arch = (tech.get('input_binding') or {}).get('architecture_sha')
                if original_arch and row['content_sha256'] not in (original_arch,authoring.get('reconciled_architecture_sha256')):
                    raise ValueError('UX01_B_STALE_ARCHITECTURE')
                if (tech.get('quality') or {}).get('current',{}).get('structural_disposition') == 'BLOCK':
                    raise ValueError('UX01_B_TECH_QUALITY_BLOCK')
                if (tech.get('schema_id')!='mp132.r03_04.technology_options.v3'
                        or validate_technology(str(tech.get('content') or ''))):
                    raise ValueError('R0304_TECH_P5_CANDIDATE_REGENERATE_P6')
            if action == 'reconcile':
                if (adr.get('schema_id')!='mp132.r03_04.material_adr.v3'
                        or validate_adr(str(adr.get('content') or ''))):
                    raise ValueError('R0304_ADR_INCOMPLETE_REGENERATE')
            if action == 'generate_options':
                frozen = self._r0304_frozen_context(state,workspace_root)
                project_file=workspace_root/'.devpilot/project.yaml'
                if not project_file.is_file() or project_file.is_symlink():
                    raise ValueError('R0304_PROJECT_CONTEXT_REQUIRED')
                name=str(parse_project_yaml_metadata(project_file).get('project_name') or workspace_id)
                prompt=technology_prompt(name,str(row['content']),frozen, business_need=str(parse_project_yaml_metadata(project_file).get('business_need') or 'UNKNOWN'))
                request = {'upstream_sha':{key:_sha_text(value) for key,value in frozen.items()},
                           'architecture_sha':str(row['content_sha256']),
                           'prompt_sha256':_sha_text(prompt),
                           'context_profile':'r03_04.evidence_selection.v1',
                           'profile_version':'2.3.0', 'generation_epoch':epoch}
                if tech and not successor and (tech.get('input_binding') != request or tech.get('model') != (model or str((row.get('derivation') or {}).get('model') or ''))):
                    raise ValueError('UX01_B_OPTIONS_SUCCESSOR_REQUIRED')
                reply = self.technology_authoring.infer(workspace_id=workspace_id,kind='technology',
                    input_binding=request,prompt=prompt,
                    model=model or str((row.get('derivation') or {}).get('model') or ''),
                    successor=successor,explicit_owner_action=True,quality_context=quality_context)
                if tech.get('candidate_id') != reply.get('candidate_id') or str(tech.get('candidate_sha256') or '') != reply['candidate_sha256']:
                    authoring={'technology':reply,'selected_option_id':None,'adr':None,
                               'reconciled_architecture_sha256':None,'status':'TECH_OPTIONS_DRAFT'}
                else:
                    authoring['technology']=reply
            elif action == 'owner_revise_options':
                self._r0304_frozen_context(state,workspace_root)
                reply=self.technology_authoring.owner_revision(
                    workspace_id=workspace_id,kind='technology',content=content,parent=tech,actor=actor)
                if reply.get('candidate_sha256')!=tech.get('candidate_sha256'):
                    authoring={'technology':reply,'selected_option_id':None,'adr':None,
                               'reconciled_architecture_sha256':None,'status':'TECH_OPTIONS_DRAFT'}
                    self._append_trace(workspace_id,{'event':'R0304_OWNER_TECH_REVISION',
                        'actor':actor,'before_sha256':tech.get('candidate_sha256'),
                        'after_sha256':reply['candidate_sha256'],'at':_now()})
            elif action == 'select_option':
                self.technology_authoring.bound_candidate(workspace_id,tech)
                choices={m.group(1).upper() for m in _OPTION.finditer(str(tech.get('content') or ''))}
                if option_id not in choices:
                    raise ValueError('R0304_UNKNOWN_OPTION_DENY')
                if selected and selected != option_id and not successor:
                    raise ValueError('UX01_B_SELECTION_SUCCESSOR_REQUIRED')
                if selected != option_id:
                    authoring.update({'selected_option_id':option_id,'adr':None,
                                      'reconciled_architecture_sha256':None,'status':'OWNER_OPTION_SELECTED'})
                authoring['selected_technology_sha256']=tech['candidate_sha256']
                authoring['selection_epoch']=epoch
                authoring['selected_by']=actor
                authoring['selection_at']=_now()
            elif action == 'generate_adr':
                technology=self.technology_authoring.bound_candidate(workspace_id,tech)
                if not selected or selected not in {m.group(1).upper() for m in _OPTION.finditer(technology)}:
                    raise ValueError('R0304_OWNER_SELECTION_REQUIRED')
                if authoring.get('selected_technology_sha256') != tech['candidate_sha256'] or authoring.get('selection_epoch') != epoch:
                    raise ValueError('UX01_B_OWNER_SELECTION_STALE')
                inputs={'technology_sha':tech['candidate_sha256'],'selected_option_id':selected,
                        'architecture_sha':row['content_sha256'],'profile_version':'2.3.0',
                        'context_profile':'r03_04.evidence_selection.v1','generation_epoch':epoch,
                        'business_need_sha256':_sha_text(' '.join(business_need['text'].split()))}
                prompt=adr_prompt(str(row['content']),technology,selected)
                inputs['prompt_sha256']=_sha_text(prompt)
                reply=self.technology_authoring.infer(workspace_id=workspace_id,kind='adr',
                    input_binding=inputs,prompt=prompt,
                    model=model or str((row.get('derivation') or {}).get('model') or ''),
                    successor=successor,explicit_owner_action=True,quality_context=quality_context)
                authoring.update({'adr':reply,'reconciled_architecture_sha256':None,
                                  'status':'ADR_DRAFT'})
            elif action == 'owner_revise_adr':
                if not selected:
                    raise ValueError('R0304_OWNER_SELECTION_REQUIRED')
                technology=self.technology_authoring.bound_candidate(workspace_id,tech)
                if selected not in {m.group(1).upper() for m in _OPTION.finditer(technology)}:
                    raise ValueError('R0304_OWNER_SELECTION_DRIFT')
                if not re.search(r'\b'+re.escape(selected)+r'\b',content,re.I):
                    raise ValueError('R0304_OWNER_ADR_SELECTION_MISMATCH')
                reply=self.technology_authoring.owner_revision(
                    workspace_id=workspace_id,kind='adr',content=content,parent=adr,actor=actor)
                if reply.get('candidate_sha256')!=adr.get('candidate_sha256'):
                    authoring.update({'adr':reply,'reconciled_architecture_sha256':None,
                                      'status':'ADR_DRAFT'})
                    self._append_trace(workspace_id,{'event':'R0304_OWNER_ADR_REVISION',
                        'actor':actor,'before_sha256':adr.get('candidate_sha256'),
                        'after_sha256':reply['candidate_sha256'],'at':_now()})
            elif action == 'reconcile':
                technology=self.technology_authoring.bound_candidate(workspace_id,tech)
                decision=self.technology_authoring.bound_candidate(workspace_id,adr)
                if (adr.get('quality') or {}).get('current',{}).get('structural_disposition') == 'BLOCK':
                    raise ValueError('UX01_B_ADR_QUALITY_BLOCK')
                if not selected or selected not in {m.group(1).upper() for m in _OPTION.finditer(technology)}:
                    raise ValueError('R0304_OWNER_SELECTION_REQUIRED')
                if authoring.get('selected_technology_sha256') != tech['candidate_sha256'] or authoring.get('selection_epoch') != epoch:
                    raise ValueError('UX01_B_OWNER_SELECTION_STALE')
                bound = adr.get('input_binding') or {}
                if bound.get('selected_option_id') != selected or bound.get('technology_sha') != tech['candidate_sha256'] or bound.get('generation_epoch') != epoch:
                    raise ValueError('UX01_B_ADR_LINEAGE_DRIFT')
                replacement=compose_architecture(str(row['content']),technology,selected,decision,
                                                  tech['candidate_sha256'],adr['candidate_sha256'])
                if _sha_text(replacement)==str(row['content_sha256']):
                    if self._technology_binding_valid(state,row):
                        return self._pass(command,'R0304_ARCHITECTURE_ALREADY_BOUND_PASS',
                                          'Architecture ya incluye la selección exacta; no se repitió ninguna inferencia.',
                                          {'r03_04_authoring':self._technology_public(state),'source_mutations_performed':False})
                    raise ValueError('R0304_SAME_CONTENT_WITHOUT_BINDING_BLOCK')
                saved=self.save_draft(stage_id='architecture',content=replacement,mode='LOCAL_MODEL',
                    actor=actor,actor_role=actor_role,session_principal=session_principal,
                    effective_roles=effective_roles,workspace_scopes=workspace_scopes)
                if not saved.ok: return saved
                state=self._load_state(workspace_id)
                row=self._stage_state(state,'architecture')
                binding={'generation_epoch':epoch,'technology_candidate_id':tech.get('candidate_id'),
                         'adr_candidate_id':adr.get('candidate_id'),
                         'technology_sha256':tech['candidate_sha256'],'selected_option_id':selected,
                         'adr_sha256':adr['candidate_sha256'],'architecture_sha256':row['content_sha256']}
                row['derivation']=dict(row.get('derivation') or {})
                row['derivation']['technology_selection']=binding
                authoring['reconciled_architecture_sha256']=row['content_sha256']
                authoring['status']='ARCHITECTURE_REVIEW_REQUIRED'
                self._append_trace(workspace_id,{'event':'R0304_OWNER_TECHNOLOGY_SELECTED',
                    'actor':actor,'plan_invalidated':bool((saved.data or {}).get('plan_invalidated')),
                    'binding':binding,'at':_now()})
            else:
                return self._block(command,'R0304_ACTION_UNKNOWN','Operación Technology/ADR no permitida.')
        except (ValueError, OSError, UnicodeError, KeyError, TypeError) as exc:
            return self._block(command,'R0304_LOCAL_AUTHORING_BLOCK',str(exc))
        if action in ('generate_options','generate_adr'):
            try:
                if not project_file.is_file() or project_file.is_symlink():
                    raise ValueError('R0304_PROJECT_CONTEXT_REQUIRED')
                _require_current_business_need({'business_need':business_need}, {
                    'text':str(parse_project_yaml_metadata(project_file).get('business_need') or 'UNKNOWN')})
            except (ValueError, OSError, UnicodeError) as exc:
                return self._block(command,'R0304_LOCAL_AUTHORING_BLOCK',str(exc))
            latest = self._load_state(workspace_id)
            latest_row = self._stage_state(latest,'architecture')
            if (latest_row.get('content_sha256') != initial_arch_sha
                    or latest_row.get('status') != initial_arch_status or latest_row.get('approval_id')):
                return self._block(command,'UX01_B_STATE_CHANGED_DURING_INFERENCE',
                                   'Candidato conservado; Architecture cambió durante la inferencia. Conciliar estado.')
        try:
            if action in ('owner_revise_options','owner_revise_adr'):
                key = 'technology' if action == 'owner_revise_options' else 'adr'
                revised = authoring[key]
                parent = tech if key == 'technology' else adr
                if revised['candidate_sha256'] == parent.get('candidate_sha256'):
                    return self._pass(command,'UX01_B_OWNER_REVISION_UNCHANGED','Contenido idéntico; revisión conservada.',
                        {'r03_04_authoring':self._technology_public(state),'source_mutations_performed':False})
                revised['generation_epoch'] = epoch
                revised['input_binding'] = parent.get('input_binding', {})
                revised['candidate_id'] = revised.get('candidate_id') or revised['candidate_sha256']
                revised['quality'] = candidate_quality(
                    'technology_options' if key == 'technology' else 'adr', revised['content'],
                    frozen=frozen,hashes=hashes,candidate_id=revised['candidate_id'],epoch=epoch,
                    actor=actor,parent_id=parent.get('candidate_id'),
                    before_owner=(parent.get('quality') or {}).get('before_owner'),
                    selected_option_id=selected or None,
                    selected_option_sha256=tech.get('candidate_sha256') if key == 'adr' else None)
            if action in ('owner_revise_options','owner_revise_adr'):
                revised['quality']['current']['business_need'] = business_need
                self.technology_authoring.persist_revision_receipt(workspace_id,revised)
        except (ValueError,OSError,UnicodeError,KeyError,TypeError) as exc:
            return self._block(command,'UX01_B_REVISION_RECEIPT_BLOCK',str(exc))
        row.setdefault('derivation', {})['generation_epoch'] = epoch
        state['r03_04_authoring']=authoring
        state['updated_at']=_now()
        self._write_state(workspace_id,state)
        return self._pass(command,'R0304_LOCAL_AUTHORING_PASS',
            'Modelo local ejecutado o decisión Owner conservada; la publicación requiere approval gobernado.',
            {'r03_04_authoring':self._technology_public(state),'source_mutations_performed':False,
             'network_scope':'loopback' if action in ('generate_options','generate_adr') else 'none'})

    def _r0304_frozen_context(self,state:dict[str,Any],workspace_root:Path)->dict[str,str]:
        frozen={}
        for source_id in ('product-vision','scope','requirements'):
            row=self._stage_state(state,source_id)
            target=workspace_root/str(self._stage_by_id[source_id]['relative_path'])
            approved=str(row.get('approved_sha256') or '')
            if (row.get('status')!='FROZEN' or not _SHA.fullmatch(approved)
                    or not target.is_file() or target.is_symlink()
                    or _sha_bytes(target.read_bytes())!=approved):
                raise ValueError('R0304_UPSTREAM_FROZEN_DRIFT:'+source_id)
            frozen[source_id]=_canonical_text(target.read_text(encoding='utf-8-sig'))
        return frozen

    @staticmethod
    def _technology_binding_valid(state:dict[str,Any],row:dict[str,Any])->bool:
        auth=state.get('r03_04_authoring') or {}
        na = auth.get('adr_applicability') or {}
        if (na.get('status') == 'NOT_APPLICABLE' and na.get('actor') and len(na.get('reason','')) >= 35
                and not auth.get('selected_option_id') and not auth.get('adr')
                and na.get('architecture_sha256') == row.get('content_sha256')
                and na.get('generation_epoch') == (row.get('derivation') or {}).get('generation_epoch')):
            return True
        decision=(row.get('derivation') or {}).get('technology_selection') or {}
        tech=auth.get('technology') or {}; adr=auth.get('adr') or {}
        return (bool(auth.get('reconciled_architecture_sha256'))
            and auth.get('reconciled_architecture_sha256')==row.get('content_sha256')
            and decision.get('architecture_sha256')==row.get('content_sha256')
            and decision.get('technology_sha256')==tech.get('candidate_sha256')
            and decision.get('adr_sha256')==adr.get('candidate_sha256')
            and decision.get('selected_option_id')==auth.get('selected_option_id')
            and tech.get('status')=='COMPLETE' and adr.get('status')=='COMPLETE'
            and (not decision.get('generation_epoch') or (
                decision['generation_epoch']==(row.get('derivation') or {}).get('generation_epoch')
                and decision['generation_epoch']==tech.get('generation_epoch')==adr.get('generation_epoch')
                and decision.get('technology_candidate_id')==tech.get('candidate_id')
                and decision.get('adr_candidate_id')==adr.get('candidate_id'))))

    @staticmethod
    def _technology_public(state:dict[str,Any])->dict[str,Any]:
        auth=state.get('r03_04_authoring') or {}
        tech=auth.get('technology') or {}; adr=auth.get('adr') or {}
        return {'status':auth.get('status') or 'NOT_STARTED','selected_option_id':auth.get('selected_option_id'),
                'architecture_reconciled':bool(auth.get('reconciled_architecture_sha256')),
                'selected_technology_sha256':auth.get('selected_technology_sha256'),
                'generation_epoch':auth.get('selection_epoch'),
                'adr_applicability':auth.get('adr_applicability'),
                'technology':{key:tech.get(key) for key in ('status','candidate_file','candidate_sha256','content','model','tokens_estimated','quality_certified','human_review_required','origin','revision_of_sha256','created_by','candidate_id','generation_epoch','quality','elapsed_ms','format_findings')},
                'adr':{key:adr.get(key) for key in ('status','candidate_file','candidate_sha256','content','model','tokens_estimated','quality_certified','human_review_required','origin','revision_of_sha256','created_by','candidate_id','generation_epoch','quality','elapsed_ms','format_findings')},
                'model_execution_used':bool(tech.get('model_execution_used')),
                'project_source_mutations':0,'technology_path':'docs/02_architecture/technology_options.md',
                'adr_path':'docs/02_architecture/adrs/ADR-001-*.md'}

    def architecture_adrs_prepare(self, *, actor: str, actor_role: str, session_principal: str, effective_roles: list[str]) -> CommandResult:
        command='guided pre-code architecture ADRs prepare'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id)
        result=self.adr_bundle.prepare(workspace_root=workspace_root,workspace_id=workspace_id,state=state,actor=actor,actor_role=actor_role)
        if result.ok:self._write_state(workspace_id,state)
        return result

    def architecture_adrs_request_approval(self, *, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], reason: str) -> CommandResult:
        command='guided pre-code architecture ADRs approval request'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id)
        result=self.adr_bundle.request_approval(workspace_root=workspace_root,workspace_id=workspace_id,state=state,actor=actor,actor_role=actor_role,reason=reason)
        if result.ok:self._write_state(workspace_id,state)
        return result

    def architecture_adrs_apply(self, *, actor: str, actor_role: str, session_principal: str, effective_roles: list[str]) -> CommandResult:
        command='guided pre-code architecture ADRs apply'
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        identity=self._identity(actor,actor_role,session_principal,effective_roles)
        if identity is not None:return identity
        state=self._load_state(workspace_id)
        result=self.adr_bundle.apply(workspace_root=workspace_root,workspace_id=workspace_id,state=state,actor=actor,actor_role=actor_role)
        if result.ok:self._write_state(workspace_id,state)
        return result

    def decide_miasi_applicability(self, *, actor: str, actor_role: str, session_principal: str, effective_roles: list[str], workspace_scopes: list[str], declared_ai_usage: bool, capabilities: list[str], risk_level: str, evidence_refs: list[str] | None = None) -> CommandResult:
        command = 'guided pre-code MIASI applicability decision'
        context = self._context()
        if isinstance(context, CommandResult):
            return context
        workspace_id, workspace_root = context
        identity = self._identity(actor, actor_role, session_principal, effective_roles)
        if identity is not None:
            return identity
        if 'owner' not in set(effective_roles):
            return self._block(command, 'GSDLC13C03_MIASI_OWNER_BLOCK', 'Owner role is required to classify project MIASI applicability.')
        if workspace_id not in set(workspace_scopes):
            return self._block(command, 'GSDLC13C03_MIASI_SCOPE_BLOCK', 'Active workspace scope is required for the MIASI applicability decision.')
        state = self._load_state(workspace_id)
        if self._current_stage(state) is not None:
            return self._block(command, 'GSDLC13C03_PRE_CODE_NOT_COMPLETE_BLOCK', 'MIASI applicability for strict pre-code readiness can be finalized only after all seven pre-code stages are FROZEN.')
        payload = {
            'schema_id': 'SCHEMA-DEVPL-MIASI-APPLICABILITY-CONTEXT-V1',
            'schema_version': '1.0',
            'project': {
                'declared_ai_usage': bool(declared_ai_usage),
                'capabilities': [str(x).strip() for x in capabilities if str(x).strip()],
                'risk_level': str(risk_level or 'low').strip().lower(),
                'evidence_refs': [str(x) for x in (evidence_refs or []) if str(x)],
            },
            'features': [],
            'risk_review_status': 'NOT_REQUIRED',
            'evidence_refs': [f'owner-decision:{workspace_id}:13-C-03'],
            'decision_actor': actor,
        }
        try:
            result = self.miasi.evaluate(payload, state_payload={'artifacts': []}, context_source='owner-session/runtime-preview')
        except Exception as exc:
            return self._block(command, 'GSDLC13C03_MIASI_INPUT_BLOCK', f'MIASI applicability input is invalid: {exc}')
        target = self.miasi.context_path(workspace_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix('.tmp')
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        os.replace(tmp, target)
        evaluated = self.miasi.evaluate_workspace(workspace_id, {'artifacts': []}).to_payload()
        evaluated.update({'pre_code_authoritative': True, 'blocking_scope': 'pre-code-readiness'})
        readiness = self._readiness_payload(state, workspace_id, workspace_root, miasi=evaluated)
        if readiness.get('status') == 'PASS' and readiness.get('pre_code_ready') is True:
            state['status'] = 'PRE_CODE_READY'
            state['completed_at'] = state.get('completed_at') or _now()
            state['updated_at'] = _now()
            self._write_state(workspace_id, state)
            self._append_trace(workspace_id, {'event': 'MIASI_APPLICABILITY_CONFIRMED', 'actor': actor, 'status': evaluated.get('status'), 'gate_status': evaluated.get('gate_status'), 'pre_code_ready': True, 'at': _now()})
        else:
            state['status'] = 'BLOCKED'
            state['updated_at'] = _now()
            self._write_state(workspace_id, state)
            self._append_trace(workspace_id, {'event': 'MIASI_APPLICABILITY_CONFIRMED', 'actor': actor, 'status': evaluated.get('status'), 'gate_status': evaluated.get('gate_status'), 'pre_code_ready': False, 'at': _now()})
        projection = self._projection(state, workspace_id, workspace_root, effective_roles, workspace_scopes)
        return self._pass(command, 'GSDLC13C03_MIASI_DECISION_PASS', 'MIASI applicability was evaluated from an explicit Owner decision and strict pre-code readiness was recomputed.', {'pre_code': projection, 'miasi_decision': {'runtime_only': True, 'context_source': evaluated.get('context_source'), 'workspace_source_writes': 0, 'network_used': False, 'external_api_used': False}})

    def readiness(self, *, effective_roles: list[str], workspace_scopes: list[str]) -> CommandResult:
        context=self._context()
        if isinstance(context,CommandResult):return context
        workspace_id,workspace_root=context
        state=self._load_state(workspace_id); payload=self._readiness_payload(state,workspace_id,workspace_root)
        ok=payload['status']=='PASS'
        return CommandResult('guided pre-code readiness',ok,ExitCode.PASS if ok else ExitCode.BLOCK,'Guided pre-code vertical-slice strict readiness passed.' if ok else 'Guided pre-code vertical-slice strict readiness is blocked.',data={'readiness':payload},findings=[] if ok else [Finding('GSDLC05E_READINESS_STRICT_BLOCK','One or more mandatory wizard stages are not frozen/source-valid.',Severity.BLOCK,metadata={'blockers':payload['blockers']})])

    def _projection(self,state:dict[str,Any],workspace_id:str,workspace_root:Path,effective_roles:list[str],workspace_scopes:list[str])->dict[str,Any]:
        current=self._current_stage(state)
        advisor_payload=None
        miasi=self._miasi_payload(workspace_id)
        if current is not None:
            artifact_status=str(self._stage_state(state,current['stage_id']).get('status') or 'MISSING')
            ctx=AdvisorContext(workspace_id=workspace_id,current_step=str(current['advisor_step']),effective_roles=tuple(effective_roles),workspace_scopes=tuple(workspace_scopes),artifact_readiness='READY' if artifact_status in {'DRAFT','APPROVAL_REQUIRED','FROZEN'} else 'UNKNOWN',miasi_gate_status=str(miasi.get('gate_status') or 'BLOCK'),provider_status='NOT_AVAILABLE',budget_status='NOT_APPLICABLE',active_project_context=True)
            advisor_payload=self.advisor.advise(ctx).to_payload()
        readiness=self._readiness_payload(state,workspace_id,workspace_root,miasi=miasi)
        current_row=self._stage_state(state,current['stage_id']) if current else {}
        current_derivation=current_row.get('derivation') if isinstance(current_row.get('derivation'),dict) else {}
        technology_decision=None
        architecture_row=self._stage_state(state,'architecture')
        if str(architecture_row.get('content') or '').strip():
            architecture_derivation=architecture_row.get('derivation') if isinstance(architecture_row.get('derivation'),dict) else {}
            frozen_sha=str(architecture_row.get('approved_sha256') or '')
            frozen_proven=False
            if architecture_row.get('status')=='FROZEN' and frozen_sha:
                target=workspace_root/str(self._stage_by_id['architecture']['relative_path'])
                frozen_proven=target.is_file() and not target.is_symlink() and _sha_bytes(target.read_bytes())==frozen_sha
            technology_decision=inspect_technology_decisions(
                str(architecture_row.get('content') or ''),
                source_refs=architecture_derivation.get('upstream_refs') or architecture_derivation.get('source_refs') or [],
                lifecycle=str(architecture_row.get('status') or 'DRAFT'),
                architecture_approval_id=str(architecture_row.get('approval_id') or ''),
                frozen_sha256=frozen_sha,source_sha256_verified=frozen_proven)
        adr_bundle=self.adr_bundle.projection(workspace_root=workspace_root,workspace_id=workspace_id,state=state)
        from .r02_07_segmented import progress as requirements_progress
        from .r03_03_segments import progress as architecture_progress
        segmented_status=(requirements_progress(self.root,workspace_id) if current and current['stage_id']=='requirements'
                          else architecture_progress(self.root,workspace_id) if current and current['stage_id']=='architecture'
                          else None)
        return {'product_definition_coverage':(self._product_definition_coverage(state,workspace_root) if workspace_id in set(workspace_scopes) else None), 'segmented_progress':segmented_status, 'technology_decision':technology_decision, 'schema_id':'devpilot.gsdlc05e.pre_code_projection.v1','profile_id':self.catalog['profile_id'],'readiness_semantics':self.catalog.get('readiness_semantics'),'workspace_id':workspace_id,'status':state.get('status','NOT_STARTED'),'current_stage_id':current['stage_id'] if current else None,'current_stage_order':current['order'] if current else None,'stages':[self._public_stage(self._stage_state(state,x['stage_id']),x) for x in self._stages],'semantic_model':deepcopy(state.get('semantic_model')) if isinstance(state.get('semantic_model'),dict) else None,'advisor':advisor_payload,'miasi':miasi,'readiness':readiness,'architecture_adr_bundle':adr_bundle,'transition_trace_ref':f'outputs/pre_code_wizard/gsdlc_05_e/{workspace_id}/transition_trace.jsonl','server_authoritative':True,'normal_user_powershell_required':0,'external_operator_project_writes':0,'network_used':False,'external_api_used':False,'model_execution_used':bool(current_derivation.get('model_execution_used',False)),'agent_execution_used':bool(current_derivation.get('agent_execution_used',False)),'rag_execution_used':bool(current_derivation.get('rag_execution_used',False)),'deterministic_local_derivation_available':bool(current and 'DEVPL_MOCK' in current.get('allowed_modes',[]))}

    def _product_definition_coverage(self, state:dict[str,Any], workspace_root:Path)->dict[str,Any]|None:
        """A188 read-only post-FROZEN audit; never changes readiness or lifecycle.

        This projection reads server-authoritative stage receipts and compares
        their exact approved bytes before handing evidence to the canonical
        ArtifactProfileRegistry. Its REVIEW is not a new freeze requirement.
        """
        from devpilot_core.validation.product_definition_coverage import FrozenProof, ProductDefinitionInput
        stages=(('product-vision','product-vision'),('scope','mvp-scope'),('requirements','requirements-specification'))
        if any(str(self._stage_state(state,k).get('status') or '')!='FROZEN' for k,_ in stages):
            return None
        proofs={}; accepts={}
        for stage_id,typ in stages:
            row=self._stage_state(state,stage_id)
            path=(workspace_root/str(self._stage_by_id[stage_id]['relative_path'])).resolve()
            if not path.is_relative_to(workspace_root.resolve()) or not path.is_file():
                continue
            bytes_now=path.read_bytes()
            expected=str(row.get('approved_sha256') or '')
            digest=_sha_bytes(bytes_now)
            if expected and digest==expected:
                proofs[typ]=FrozenProof(_sha_text(bytes_now.decode('utf-8-sig')),
                    'pre-code-runtime:'+str(row.get('approval_id') or '')+':'+str(row.get('execution_id') or ''))
                if row.get('approval_id') and row.get('review_id'):
                    accepts[typ]=(str(row['approval_id']),str(row['review_id']))
            else:
                # Do not construct a trusted proof for an invalid state.
                proofs[typ]=FrozenProof('0'*64,'pre-code-runtime:HASH_DRIFT')
        return self.profiles.evaluate_product_definition(workspace_root,ProductDefinitionInput(
            frozen=proofs,semantic_acceptance=accepts))

    def _readiness_payload(self,state:dict[str,Any],workspace_id:str,workspace_root:Path,*,miasi:dict[str,Any]|None=None)->dict[str,Any]:
        blockers=[]; artifacts=[]
        miasi=miasi or self._miasi_payload(workspace_id)
        miasi_gate=str(miasi.get('gate_status') or 'BLOCK').upper()
        miasi_required_now=self._current_stage(state) is None
        if miasi_gate!='PASS' and (miasi_gate!='DEFERRED' or miasi_required_now):
            blockers.append({'stage_id':'miasi-applicability','status':str(miasi.get('status') or 'REVIEW_REQUIRED'),'reason':'MIASI gate must PASS at strict pre-code readiness; before that checkpoint missing context is DEFERRED','reason_codes':list(miasi.get('reason_codes') or [])})
        for stage in self._stages:
            row=self._stage_state(state,stage['stage_id']); target=(workspace_root/stage['relative_path']).resolve(); status=str(row.get('status') or 'MISSING'); actual_sha=_sha_bytes(target.read_bytes()) if target.is_file() else None
            expected=str(row.get('approved_sha256') or '') or None
            profile_ok=False; profile_findings=[]
            if target.is_file():
                try:
                    content=target.read_text(encoding='utf-8'); doc=parse_frontmatter_text(content,path=Path(stage['relative_path'])); fm=validate_frontmatter_document(doc,root=None,strict=True); headings=extract_headings(doc.body); profile=self.profiles.select(Path(stage['relative_path'])); missing=[h for h in profile.required_headings if not any(normalize_heading(h) in x.normalized for x in headings)]; profile_ok=fm.ok and not missing; profile_findings=missing
                except Exception as exc: profile_findings=[str(exc)]
            ok=status=='FROZEN' and bool(expected) and actual_sha==expected and profile_ok
            if not ok:blockers.append({'stage_id':stage['stage_id'],'status':status,'source_exists':target.is_file(),'expected_sha256':expected,'actual_sha256':actual_sha,'profile_ok':profile_ok,'profile_findings':profile_findings})
            artifacts.append({'stage_id':stage['stage_id'],'relative_path':stage['relative_path'],'lifecycle_state':status,'approved_sha256':expected,'actual_sha256':actual_sha,'profile_id':stage['profile_id'],'profile_valid':profile_ok})
        adr_projection=self.adr_bundle.projection(workspace_root=workspace_root,workspace_id=workspace_id,state=state)
        if bool(adr_projection.get('required')) and not bool(adr_projection.get('ready')):
            blockers.append({'stage_id':'architecture-adrs','status':str(adr_projection.get('status') or 'REQUIRED'),'reason':'Standalone Architecture ADR companion artifacts must be approval-bound and materialized before downstream C-02 stages/readiness.'})
        return {'schema_id':'devpilot.gsdlc05e.pre_code_readiness.v1','profile_id':self.catalog['profile_id'],'strict':True,'scope':'guided-pre-code-manual-v1/vertical-slice','status':'PASS' if not blockers else 'BLOCK','pre_code_ready':not blockers,'mandatory_stages_total':len(self._stages),'mandatory_stages_frozen':sum(1 for x in artifacts if x['lifecycle_state']=='FROZEN'),'artifacts':artifacts,'miasi':miasi,'blockers':blockers,'historical_global_readiness_replaced':False,'network_used':False,'external_api_used':False}

    def _adr_companion_gate(self, *, state: dict[str,Any], workspace_root: Path, requested_stage_id: str) -> CommandResult | None:
        stage=self._stage_by_id.get(str(requested_stage_id))
        if stage is None or int(stage.get('order') or 0)<=4:return None
        projection=self.adr_bundle.projection(workspace_root=workspace_root,workspace_id=str(state.get('workspace_id') or ''),state=state)
        if bool(projection.get('required')) and not bool(projection.get('ready')):
            return self._block('guided pre-code downstream stage','GSDLC13C02_ADR_COMPANION_REQUIRED_BLOCK','Architecture is FROZEN, but its standalone ADR companion gate is not complete. Materialize the approved ADR bundle before starting Security or later C-02 stages.',metadata={'requested_stage_id':requested_stage_id,'architecture_adr_bundle':projection})
        return None

    def _miasi_payload(self,workspace_id:str)->dict[str,Any]:
        context_path=self.miasi.context_path(workspace_id)
        if not context_path.is_file():
            try: context_source=context_path.relative_to(self.root).as_posix()
            except ValueError: context_source=str(context_path)
            return {
                'status':'NOT_EVALUATED','gate_status':'DEFERRED',
                'reason_codes':['MIASI_APPLICABILITY_DEFERRED_UNTIL_PRE_CODE'],
                'risk_level':'unknown','project_decision':{},'feature_decisions':[],
                'required_controls':[],'missing_controls':[],'policy_binding':{},'blockers':[],
                'evidence_refs':[],'context_source':context_source,'reevaluation_required':True,
                'agent_execution_allowed':False,'rag_execution_allowed':False,
                'execution_reason_code':'MIASI_EVALUATION_DEFERRED',
                'network_used':False,'external_api_used':False,'model_execution_used':False,
                'agents_executed':False,'rag_executed':False,'source_mutations_performed':False,
                'pre_code_authoritative':False,'blocking_scope':'pre-code-readiness',
            }
        try:
            payload=self.miasi.evaluate_workspace(workspace_id, {'artifacts': []}).to_payload()
            payload.update({'pre_code_authoritative':True,'blocking_scope':'pre-code-readiness'})
            return payload
        except Exception:
            # Once context exists MIASI is authoritative and evaluator failures remain fail-closed.
            return {
                'status':'REVIEW_REQUIRED','gate_status':'BLOCK',
                'reason_codes':['MIASI_APPLICABILITY_EVALUATION_ERROR'],
                'risk_level':'unknown','project_decision':{},'feature_decisions':[],
                'required_controls':[],'missing_controls':[],'policy_binding':{},
                'blockers':[{'code':'MIASI_APPLICABILITY_EVALUATION_ERROR','message':'MIASI applicability could not be evaluated deterministically.'}],
                'evidence_refs':[],'context_source':'unavailable','reevaluation_required':True,
                'agent_execution_allowed':False,'rag_execution_allowed':False,
                'network_used':False,'external_api_used':False,'model_execution_used':False,
                'agents_executed':False,'rag_executed':False,'source_mutations_performed':False,
                'pre_code_authoritative':True,'blocking_scope':'pre-code-readiness',
            }

    def _load_catalog(self)->dict[str,Any]:
        payload=json.loads((self.root/CATALOG).read_text(encoding='utf-8'))
        stages=payload.get('stages')
        if payload.get('schema_id')!='devpilot.gsdlc05e.pre_code_wizard_catalog.v1' or not isinstance(stages,list) or len(stages)!=7:raise ValueError('invalid GSDLC-05-E wizard catalog')
        ids=[x.get('stage_id') for x in stages]; orders=[x.get('order') for x in stages]
        if len(set(ids))!=7 or sorted(orders)!=list(range(1,8)):raise ValueError('wizard catalog stage id/order drift')
        return payload

    def _context(self):
        context=self.documents.context_resolver.resolve()
        if not context.configured or not context.valid or not context.active_workspace_id or context.active_workspace_root is None:
            return self._block('guided pre-code','GSDLC05E_PROJECT_CONTEXT_REQUIRED_BLOCK','An active server-valid project context is required.')
        return str(context.active_workspace_id),context.active_workspace_root.resolve()

    def _initial_state(self,workspace_id:str)->dict[str,Any]:
        return {'schema_id':'devpilot.gsdlc05e.pre_code_state.v1','workspace_id':workspace_id,'profile_id':self.catalog['profile_id'],'status':'NOT_STARTED','semantic_model':None,'stages':{x['stage_id']:{'stage_id':x['stage_id'],'status':'MISSING','mode':None,'content_sha256':None,'base_sha256':None,'artifact':None,'derivation':None,'review_id':None,'plan_id':None,'plan_hash':None,'diff':None,'execution_id':None,'approval_id':None,'approved_sha256':None,'findings':[],'validation':{},'updated_at':None} for x in self._stages},'created_at':_now(),'updated_at':_now(),'completed_at':None}

    def _state_path(self,workspace_id:str)->Path:
        safe=re.sub(r'[^A-Za-z0-9_.-]','_',workspace_id); return self.root/STORE_ROOT/safe/'state.json'
    def _trace_path(self,workspace_id:str)->Path:
        return self._state_path(workspace_id).with_name('transition_trace.jsonl')
    def _load_state(self,workspace_id:str)->dict[str,Any]:
        p=self._state_path(workspace_id)
        if not p.is_file():return self._initial_state(workspace_id)
        try: data=json.loads(p.read_text(encoding='utf-8'))
        except Exception:return self._initial_state(workspace_id)
        return data if data.get('schema_id')=='devpilot.gsdlc05e.pre_code_state.v1' and data.get('workspace_id')==workspace_id else self._initial_state(workspace_id)
    def _write_state(self,workspace_id:str,state:dict[str,Any])->None:
        p=self._state_path(workspace_id); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix('.tmp')
        with self._lock:
            tmp.write_text(json.dumps(state,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(tmp,p)
    def _append_trace(self,workspace_id:str,event:dict[str,Any])->None:
        p=self._trace_path(workspace_id); p.parent.mkdir(parents=True,exist_ok=True)
        with self._lock:
            with p.open('a',encoding='utf-8',newline='\n') as f: f.write(json.dumps(event,sort_keys=True,ensure_ascii=False)+'\n')
    def _current_stage(self,state:dict[str,Any])->dict[str,Any]|None:
        for stage in self._stages:
            if str(self._stage_state(state,stage['stage_id']).get('status') or 'MISSING')!='FROZEN':return stage
        return None
    @staticmethod
    def _stage_state(state:dict[str,Any],stage_id:str)->dict[str,Any]: return state['stages'][stage_id]
    @staticmethod
    def _candidate_content_binding(row:dict[str,Any])->dict[str,Any]:
        """Server-side correlation of visible DRAFT to immutable candidate provenance.

        The original model Markdown remains immutable. Owner revisions have a
        separate expected digest. This is not a semantic quality PASS.
        """
        if row.get('mode') != 'LOCAL_MODEL' or row.get('status') not in {'DRAFT','FINDINGS','APPROVAL_REQUIRED'}:
            return {'status':'NOT_APPLICABLE'}
        derived=row.get('derivation') if isinstance(row.get('derivation'),dict) else {}
        content=row.get('content')
        if not isinstance(content,str) or not content:
            return {'status':'BLOCK','reason':'MISSING_DRAFT_TEXT'}
        actual=_sha_text(content)  # Git-style logical Markdown hash (LF)
        physical_sha=_sha_bytes(content.encode('utf-8'))  # persisted runtime receipt uses exact bytes
        original=str(derived.get('candidate_sha256') or '')
        path=str(derived.get('candidate_path') or '')
        if not re.fullmatch(r'[0-9a-f]{64}',original) or not re.fullmatch(r'cand-[0-9a-f]{64}\.md',path):
            return {'status':'BLOCK','reason':'CANDIDATE_PROVENANCE_MISSING'}
        edited=bool(derived.get('owner_edited'))
        expected=str(derived.get('owner_edited_content_sha256') or '') if edited else original
        recorded=str(row.get('content_sha256') or '')
        consistent=(actual==expected and physical_sha==recorded)
        return {'status':'PASS' if consistent else 'BLOCK',
                'reason':'MATCH' if consistent else 'CONTENT_PROVENANCE_DRIFT',
                'visible_sha256':actual,'candidate_sha256':original,'candidate_path':path,
                'owner_edited':edited,'expected_sha256':expected,
                'model':str(derived.get('model') or '')}

    @staticmethod
    def _public_stage(row:dict[str,Any],stage:dict[str,Any])->dict[str,Any]:
        return {'candidate_content_binding':PreCodeWizardApplicationService._candidate_content_binding(row),
                'stage_id':stage['stage_id'],'order':stage['order'],'label':stage['label'],'relative_path':stage['relative_path'],'profile_id':stage['profile_id'],'advisor_step':stage['advisor_step'],'allowed_modes':list(stage['allowed_modes']),'status':row.get('status'),'mode':row.get('mode'),'content_sha256':row.get('content_sha256'),'base_sha256':row.get('base_sha256'),'draft_content':row.get('content') if row.get('status') in {'DRAFT','FINDINGS','APPROVAL_REQUIRED'} else None,'derivation':dict(row.get('derivation') or {}) if isinstance(row.get('derivation'),dict) else None,'review_id':row.get('review_id'),'plan_id':row.get('plan_id'),'plan_hash':row.get('plan_hash'),'diff':row.get('diff'),'execution_id':row.get('execution_id'),'approval_id':row.get('approval_id'),'approved_sha256':row.get('approved_sha256'),'findings':list(row.get('findings') or []),'validation':dict(row.get('validation') or {})}
    def _ensure_semantic_model(self, *, stage_id: str, workspace_id: str, workspace_root: Path, state: dict[str, Any], submitted: dict[str, Any] | None) -> dict[str, Any] | CommandResult:
        command='guided pre-code semantic model'
        existing=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
        if stage_id!='product-vision':
            if not existing:
                return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_REQUIRED_BLOCK','A PreCode Semantic Model from Product Vision is required before deterministic downstream generation.')
            if submitted is None:
                return existing
            try:
                updated=normalize_owner_model(existing,submitted)
            except ValueError as exc:
                return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_INPUT_BLOCK',str(exc))
            state['semantic_model']=updated; state['updated_at']=_now(); self._write_state(workspace_id,state)
            self._append_trace(workspace_id,{'event':'SEMANTIC_DECISIONS_UPDATED','stage_id':stage_id,'semantic_model_sha256':updated['semantic_model_sha256'],'actor':'owner','at':_now()})
            return updated
        project_file=workspace_root/'.devpilot/project.yaml'
        if not project_file.is_file():
            return self._block(command,'GSDLC13C01_PROJECT_CONTEXT_BLOCK','Project context is missing; Semantic Model cannot be grounded.')
        metadata=parse_project_yaml_metadata(project_file)
        need=str(metadata.get('business_need') or '').strip()
        constraints=dict(metadata.get('project_constraints') or {}) if isinstance(metadata.get('project_constraints'),dict) else {}
        model_policy=dict(metadata.get('model_policy') or {}) if isinstance(metadata.get('model_policy'),dict) else {}
        project_text=_canonical_text(project_file.read_text(encoding='utf-8'))
        if existing is None:
            candidate=build_candidate_model(workspace_id=workspace_id,business_need=need,source_ref='.devpilot/project.yaml',source_sha256=_sha_text(project_text),constraints=constraints,model_policy=model_policy)
            existing=prepare_draft_first_model(candidate)
            state['semantic_model']=existing; state['status']='IN_PROGRESS'; state['updated_at']=_now(); self._write_state(workspace_id,state)
            self._append_trace(workspace_id,{'event':'SEMANTIC_MODEL_PREPARED_DRAFT_FIRST','semantic_model_sha256':existing['semantic_model_sha256'],'at':_now()})
        if submitted is None:
            return existing
        try:
            updated=normalize_owner_model(existing,submitted)
        except ValueError as exc:
            return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_INPUT_BLOCK',str(exc))
        state['semantic_model']=updated; state['updated_at']=_now(); self._write_state(workspace_id,state)
        self._append_trace(workspace_id,{'event':'SEMANTIC_DECISIONS_UPDATED','stage_id':stage_id,'semantic_model_sha256':updated['semantic_model_sha256'],'actor':'owner','at':_now()})
        return updated

    def _derive_local_proposal(self, *, stage_id: str, workspace_id: str, workspace_root: Path, state: dict[str, Any]) -> tuple[str, dict[str, Any]] | CommandResult:
        command='guided pre-code deterministic local proposal'
        if stage_id not in {'product-vision','scope','requirements',*C02_STAGES}:
            return self._block(command,'GSDLC13C_DERIVATION_SCOPE_BLOCK','DEVPL_MOCK derivation is not implemented for this pre-code stage.')
        project_file=workspace_root/'.devpilot/project.yaml'
        if not project_file.is_file():
            return self._block(command,'GSDLC13C01_PROJECT_CONTEXT_BLOCK','Project context is missing; deterministic proposal cannot be grounded.')
        project_text=_canonical_text(project_file.read_text(encoding='utf-8'))
        metadata=parse_project_yaml_metadata(project_file)
        need=str(metadata.get('business_need') or '').strip()
        name=str(metadata.get('project_name') or metadata.get('project_id') or workspace_id).strip()
        project_id=str(metadata.get('project_id') or workspace_id).strip()
        constraints=dict(metadata.get('project_constraints') or {}) if isinstance(metadata.get('project_constraints'),dict) else {}
        model_policy=dict(metadata.get('model_policy') or {}) if isinstance(metadata.get('model_policy'),dict) else {}
        if len(need)<20:
            return self._block(command,'GSDLC13C01_BUSINESS_NEED_BLOCK','Persisted business need is missing or too short for governed derivation.')
        document_date=self._project_document_date(workspace_root)
        refs=[{'path':'.devpilot/project.yaml','sha256':_sha_text(project_text),'kind':'project-context'}]
        upstream:dict[str,str]={}
        verified_technical_sources: list[TechnicalSource] = []
        required_upstream={
            'product-vision':(),
            'scope':('product-vision',),
            'requirements':('product-vision','scope'),
            'architecture':('product-vision','scope','requirements'),
            'security':('requirements','architecture'),
            'test-strategy':('requirements','architecture','security'),
            'traceability':('product-vision','scope','requirements','architecture','security','test-strategy'),
        }[stage_id]
        for source_id in required_upstream:
            source_stage=self._stage_by_id[source_id]
            source_row=self._stage_state(state,source_id)
            if source_row.get('status')!='FROZEN':
                return self._block(command,'GSDLC13C01_PREVIOUS_STAGE_REQUIRED_BLOCK','Required governed upstream stage must be FROZEN before derivation.',metadata={'required_stage':source_id})
            source_path=workspace_root/str(source_stage['relative_path'])
            if not source_path.is_file():
                return self._block(command,'GSDLC13C01_PREVIOUS_SOURCE_MISSING_BLOCK','Frozen upstream source is missing.',metadata={'required_stage':source_id})
            source_bytes=source_path.read_bytes()
            approved_sha=str(source_row.get('approved_sha256') or '')
            actual_sha=_sha_bytes(source_bytes)
            if not _SHA.fullmatch(approved_sha) or actual_sha!=approved_sha:
                return self._block(command,'GSDLC13C01_PREVIOUS_SOURCE_DRIFT_BLOCK','Frozen upstream source no longer matches its approved content hash.',metadata={'required_stage':source_id,'expected_sha256':approved_sha or None,'actual_sha256':actual_sha})
            text=_canonical_text(source_bytes.decode('utf-8'))
            upstream[source_id]=text
            refs.append({'path':str(source_stage['relative_path']),'sha256':_sha_text(text),'approved_sha256':approved_sha,'kind':'frozen-input'})
            if stage_id == 'architecture':
                verified_technical_sources.append(TechnicalSource(stage=source_id,path=str(source_stage['relative_path']).replace('\\','/'),raw_bytes=source_bytes,expected_sha256=approved_sha,lifecycle='FROZEN'))
        semantic_model=state.get('semantic_model') if isinstance(state.get('semantic_model'),dict) else None
        if stage_id in C02_STAGES:
            try:
                content,technical=derive_technical_stage(
                    root=self.root,stage_id=stage_id,workspace_id=workspace_id,project_name=name,document_date=document_date,
                    project_metadata=metadata,upstream=upstream,semantic_model=semantic_model,
                )
            except ValueError as exc:
                return self._block(command,'GSDLC13C02_DERIVATION_INPUT_BLOCK',str(exc),metadata={'stage_id':stage_id})
            derivation=dict(technical)
            if stage_id == 'architecture':
                try:
                    technical_context=resolve_technical_context(self.root,sources=tuple(verified_technical_sources),facts=ProjectFacts(project_id=project_id,revision=1,product_has_ai=None))
                except ValueError as exc:
                    return self._block(command,'MP132_R03_02_CONTEXT_BLOCK',str(exc),metadata={'stage_id':stage_id})
                # Store only a provenance receipt; do not persist project source text.
                derivation['technical_context_profile']={
                    'profile_id':technical_context['profile_id'],
                    'profile_version':technical_context['profile_version'],
                    'status':technical_context['status'],
                    'context_sha256':technical_context['context_sha256'],
                    'project_context_sha256':technical_context['project_context_sha256'],
                    'source_refs':technical_context['source_refs'],
                    'pesp':technical_context['pesp'],
                    'truncated_stages':technical_context['truncated_stages'],
                    'safety':technical_context['safety'],
                }
            derivation['source_refs']=refs + list(technical.get('rag_source_refs') or [])
            derivation['owner_review_required']=True; derivation['approval_required_before_source_write']=True
            return content,derivation
        if not semantic_model or semantic_model.get('schema_id')!='devpilot.gsdlc13c01.pre_code_semantic_model.v1':
            return self._block(command,'GSDLC13C01_SEMANTIC_MODEL_REQUIRED_BLOCK','A valid PreCode Semantic Model is required for deterministic generation.')
        canonical_input={
            'generator_version':DERIVATION_MODEL,
            'stage_id':stage_id,
            'workspace_id':workspace_id,
            'project':{
                'project_id':project_id,'project_name':name,'business_need':' '.join(need.split()),
                'document_date':document_date,'project_constraints':constraints,'model_policy':model_policy,
            },
            'semantic_model':semantic_model,
            'upstream':upstream,
        }
        canonical_json=json.dumps(canonical_input,sort_keys=True,separators=(',',':'),ensure_ascii=False)
        artifact_type=artifact_type_for_stage(stage_id)
        profile=self.profiles.select(self.root/str(self._stage_by_id[stage_id]['relative_path']))
        dependency_profile=select_product_definition_dependency_profile(self.root,artifact_type)
        upstream_hashes={str(row['path']):str(row['sha256']) for row in refs}
        request=GenerationRequest(
            request_id=f"c01-{workspace_id}-{stage_id}-{_sha_bytes(canonical_json.encode('utf-8'))[:16]}",
            artifact_type=artifact_type,
            profile_version=profile.profile_version,
            dependency_profile_version=dependency_profile.profile_version,
            upstream_hashes=upstream_hashes,
            owner_inputs={'semantic_model_sha256':semantic_hash(semantic_model),'owner_semantic_reviewed':bool(semantic_model.get('owner_semantic_reviewed'))},
            preferred_route='deterministic',allowed_routes=('deterministic',),
            policy_snapshot={'network':'deny','external_api':False,'source_write':False,'apply_authority':False},
            budget_snapshot={'max_cost_usd':0.0},context_reference=f"pre-code:{workspace_id}:{stage_id}",
        )
        render_input={
            'stage_id':stage_id,'workspace_id':workspace_id,'project_name':name,'business_need':need,
            'document_date':document_date,'constraints':constraints,'model_policy':model_policy,'upstream':upstream,'semantic_model':semantic_model,
        }
        provider=DeterministicProductDefinitionProvider(lambda value:self._proposal_markdown(**dict(value)))
        candidate=provider.generate(request,render_input)
        content=str(candidate.payload['content'])
        candidate_meta=candidate.to_dict(); candidate_meta.pop('payload',None)
        derivation={
            'schema_id':DERIVATION_SCHEMA,
            'mode':'DEVPL_MOCK','provider':provider.provider_id,'model':provider.model_id,
            'network_used':False,'external_api_used':False,'cost_usd':0.0,
            'source_refs':refs,'canonical_input_sha256':_sha_bytes(canonical_json.encode('utf-8')),
            'generated_content_sha256':_sha_text(content),
            'semantic_model_sha256':semantic_hash(semantic_model),'semantic_model_schema_id':semantic_model.get('schema_id'),'owner_semantic_reviewed':bool(semantic_model.get('owner_semantic_reviewed')),
            'owner_review_required':True,'approval_required_before_source_write':True,
            'generation_request':request.to_dict(),'candidate_envelope':candidate_meta,'provider_contract':'GenerationProvider',
        }
        return content,derivation

    @staticmethod
    def _business_clauses(text: str) -> list[str]:
        normalized=' '.join(str(text or '').split())
        parts=[x.strip(' .') for x in re.split(r'[;.]|,\s+(?=(?:y\s+)?[A-Za-zÁÉÍÓÚáéíóúÑñ])', normalized) if x.strip(' .')]
        return parts[:10] or [normalized]

    @staticmethod
    def _markdown_section(text: str, heading: str) -> str:
        target=normalize_heading(heading)
        lines=_canonical_text(text).split('\n')
        captured:list[str]=[]; active=False
        for line in lines:
            if line.startswith('## '):
                current=normalize_heading(line[3:].strip())
                if active: break
                active=current==target
                continue
            if active: captured.append(line)
        return '\n'.join(captured).strip()

    @classmethod
    def _semantic_items(cls, text: str, heading: str) -> list[str]:
        section=cls._markdown_section(text,heading)
        if not section:return []
        bullets=[]
        for raw in section.splitlines():
            line=raw.strip()
            if not line:continue
            line=re.sub(r'^(?:[-*+]\s+|\d+[.)]\s+)', '', line).strip()
            line=re.sub(r'^\*\*(?:RF-\d+|RNF-\d+)[^*]*\*\*\s*[—:-]*\s*','',line).strip()
            if line:bullets.append(line.rstrip('.'))
        if bullets:return bullets[:12]
        return cls._business_clauses(section)[:12]

    @staticmethod
    def _clean_scope_capability(value: str) -> str:
        text=' '.join(str(value or '').split()).strip(' .')
        for prefix in ('Incluir la capacidad necesaria para:', 'Incluir la capacidad para:', 'Incluir:'):
            if text.lower().startswith(prefix.lower()):
                text=text[len(prefix):].strip(' .')
                break
        return text

    @staticmethod
    def _constraint_lines(constraints: dict[str,Any], model_policy: dict[str,Any]) -> list[str]:
        local_first=bool(constraints.get('local_first',True))
        cloud_required=bool(constraints.get('cloud_required',False))
        operator_writes=bool(constraints.get('operator_project_writes_allowed',False))
        baseline=str(model_policy.get('baseline') or 'mock-no-api')
        local_model=str(model_policy.get('local_model') or 'optional-opt-in')
        external_api=str(model_policy.get('external_api') or 'approval-provenance-only')
        return [
            f'- Local-first: {"sí" if local_first else "no"}.',
            f'- Cloud obligatorio: {"sí" if cloud_required else "no"}.',
            f'- Escrituras de proyecto por operador externo: {"permitidas" if operator_writes else "no permitidas"}.',
            f'- Baseline de modelos: {baseline}.',
            f'- Modelo local: {local_model}.',
            f'- API externa: {external_api}.',
        ]

    def _proposal_markdown(self, *, stage_id: str, workspace_id: str, project_name: str, business_need: str, document_date: str, constraints: dict[str,Any], model_policy: dict[str,Any], upstream: dict[str,str], semantic_model: dict[str,Any]) -> str:
        doc_id=f"{workspace_id.upper().replace('-', '_')}_{stage_id.upper().replace('-', '_')}"
        title={'product-vision':'Product Vision','scope':'MVP Scope','requirements':'Requirements Specification'}[stage_id]
        front=[
            '---',f'doc_id: "{doc_id}"',f'title: "{title} — {project_name}"','status: "draft"','version: "0.2.0"',
            'owner: "Owner / DevPilot"',f'updated: "{document_date}"','lifecycle_authority: "DevPilot runtime state"','---','',f'# {title}',''
        ]
        active=lambda key:[x for x in semantic_model.get(key) or [] if x.get('status')!='REJECTED']
        actors=active('actors'); outcomes=active('outcomes'); capabilities=active('capabilities')
        open_questions=[x for x in semantic_model.get('open_questions') or [] if x.get('status')!='REJECTED']
        constraint_lines=self._constraint_lines(constraints,model_policy)
        if stage_id=='product-vision':
            actor_text='; '.join(str(x.get('statement') or '') for x in actors)
            outcome_text='; '.join(str(x.get('statement') or '') for x in outcomes)
            body=[
                '## Resumen ejecutivo','',f'**{project_name}** es un producto orientado a {actor_text or 'un actor pendiente de precisión'}. DevPilot deriva este DRAFT desde un Semantic Model interno y gobernado; no fija todavía arquitectura ni stack.','',
                '## Problema','',business_need,'',
                '## Usuario/actor','',*sum(([f'- **{x["id"]}** — {x["statement"]}.',''] for x in actors),[]),
                '## Visión','',f'Permitir que {actor_text or 'el actor principal'} alcance el resultado de negocio identificado: {outcome_text or 'resultado pendiente de precisión'}.','',
                '## Propuesta de valor','',*sum(([f'- **{x["id"]}** — {x["statement"]}.',''] for x in outcomes),[]),
                '## MVP','',*sum(([f'- **{x["id"]}** — {x["statement"]}.',''] for x in capabilities),[]),
                '## Indicadores','',
                '- Las capacidades MVP representadas en este DRAFT pueden revisarse de extremo a extremo por el Owner.','',
                '- Las métricas cuantitativas no se inventan: cualquier umbral no presente en la fuente permanece como decisión gobernada.','',
                '## Local-first','',*constraint_lines,'',
                '## Preguntas abiertas','',
                *([f'- {q["id"]}: {q["statement"]} — decisión: {q.get("decision") or "pendiente no crítica"}.' for q in open_questions] or ['- No quedan preguntas críticas abiertas para este DRAFT.']),'',
                '## Post-MVP','',
                'No se incorporan automáticamente capacidades Post-MVP. Cualquier ampliación requiere una decisión gobernada posterior.','',
            ]
        elif stage_id=='scope':
            body=[
                '## MVP','',*sum(([f'- **{x["id"]}** — In scope: {x["statement"]}.',''] for x in capabilities),[]),
                '## MVP+','',
                '- No se materializan ítems MVP+ por defecto; cualquier ampliación requiere decisión explícita del Owner.','',
                '## Out of scope','',
                '- Capacidades no trazadas a Product Vision FROZEN o al Semantic Model confirmado.','',
                '- Selección de frontend, backend, base de datos o framework antes de Architecture.','',
                '- Cloud obligatorio o API externa obligatoria cuando Project Context no lo autoriza.','',
                '## Criterios','',
                '- Cada ítem In Scope conserva un ID estable y traza a una capability gobernada.','',
                '- El alcance no agrega capacidades no aprobadas y mantiene tecnología diferida hasta Architecture.','',
                '## Restricciones','',*constraint_lines,'',
                '## Dependencies','',
                '- Product Vision debe permanecer FROZEN y con hash aprobado coincidente.','',
                '## Upstream trace','',
                f'- Product Vision FROZEN content SHA-256: {_sha_text(upstream.get("product-vision", ""))}.','',
                '## Open decisions','',
                *([f'- {q["id"]}: {q["statement"]} — decisión: {q.get("decision") or "pendiente"}.' for q in open_questions if q.get('critical')] or ['- No quedan decisiones críticas abiertas para delimitar el MVP.']),'',
                '## Exit criteria','',
                '- Todas las capabilities MVP gobernadas están representadas exactamente una vez y no existe scope drift.','',
            ]
        else:
            records=requirement_records(semantic_model)
            rf=[]
            for rec in records:
                lines=[f'### {rec["id"]}','',f'- **Tipo:** {rec["type"]}.',f'- **Statement:** {rec["statement"]}',f'- **Fuente:** {", ".join(rec["source_capability_ids"])}.']
                if rec.get('owner_decision_context'):
                    lines.append(f'- **Decisión Owner vinculada:** {rec["owner_decision_context"]}')
                lines.extend([f'- **Prioridad:** {rec["priority"]}.',f'- **Criterio de aceptación:** {rec["acceptance_criteria"][0]}',f'- **Método de verificación:** {rec["verification_method"]}.',''])
                rf.extend(lines)
            body=[
                '## Propósito','',f'Definir requisitos verificables del MVP de {project_name}, derivados del Semantic Model gobernado, Scope FROZEN y Product Vision FROZEN.','',
                '## Alcance','',*[f'- {x["id"]}: {x["statement"]}.' for x in capabilities],'',
                '## Requerimientos funcionales del MVP','',*rf,
                '## Requerimientos no funcionales','',
                '- No se fabrican NFR cuantitativos. Los atributos de calidad que requieran métricas se decidirán de forma gobernada antes de convertirse en NFR verificables.','',
                '## Decisiones pendientes','',
                *([f'- {q["id"]}: {q["statement"]} — pendiente antes de approval.' for q in unresolved_decisions_for_stage(semantic_model,'requirements')] or ['- No quedan decisiones críticas pendientes para Requirements.']),'',
                '## Restricciones heredadas','',*constraint_lines,'',
                '## Trazabilidad','',*[f'- {rec["id"]} ← {", ".join(rec["source_capability_ids"])}.' for rec in records],'',
                '## Upstream trace','',
                f'- Product Vision FROZEN content SHA-256: {_sha_text(upstream.get("product-vision", ""))}.',
                f'- MVP Scope FROZEN content SHA-256: {_sha_text(upstream.get("scope", ""))}.','',
                '## Criterios de bloqueo','',
                '- BLOCK si un RF no describe comportamiento observable.','',
                '- BLOCK si falta fuente, prioridad, criterio de aceptación o método de verificación.','',
                '- BLOCK si una decisión crítica permanece abierta o si se introduce arquitectura antes de C-02.','',
            ]
        return '\n'.join(front+body).rstrip()+'\n'

    @staticmethod
    def _project_document_date(workspace_root: Path) -> str:
        manifest=workspace_root/'.devpilot/bootstrap-execution.json'
        if manifest.is_file():
            try:
                payload=json.loads(manifest.read_text(encoding='utf-8'))
                value=str(payload.get('completed_at') or '').strip()
                if re.fullmatch(r'\d{4}-\d{2}-\d{2}.*',value):return value[:10]
            except Exception:
                pass
        try:
            cp=subprocess.run(['git','-C',str(workspace_root),'log','--reverse','-1','--format=%cs'],capture_output=True,text=True,timeout=5,check=False)
            value=cp.stdout.strip()
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):return value
        except Exception:
            pass
        return '1970-01-01'

    def _reconcile_governed_parents(self, *, workspace_id: str, workspace_root: Path) -> CommandResult:
        command='guided pre-code reconcile structure'
        root=workspace_root.resolve()
        guard=PathGuard(root)
        planned:list[tuple[Path,Path]]=[]
        for rel in REQUIRED_DOCUMENT_PARENTS:
            candidate=root/rel
            decision=guard.evaluate(rel,action='create')
            if not decision.ok:
                return self._block(command,'GSDLC13C01_STRUCTURE_PATH_BLOCK','PathGuard rejected a governed document namespace.',metadata={'relative_path':rel.as_posix(),'policy':decision.to_dict()})
            cursor=root
            for part in rel.parts:
                cursor=cursor/part
                if cursor.exists() and cursor.is_symlink():
                    return self._block(command,'GSDLC13C01_STRUCTURE_SYMLINK_BLOCK','Governed document namespace contains a symlink boundary.',metadata={'relative_path':rel.as_posix(),'symlink':str(cursor)})
            if candidate.exists() and not candidate.is_dir():
                return self._block(command,'GSDLC13C01_STRUCTURE_COLLISION_BLOCK','Governed document namespace collides with a non-directory path.',metadata={'relative_path':rel.as_posix()})
            planned.append((rel,candidate))
        before=self._git_status(root)
        if before is None:
            return self._block(command,'GSDLC13C01_STRUCTURE_GIT_STATUS_BLOCK','Git status could not be verified before structural reconciliation.')
        created:list[Path]=[]
        try:
            for rel,candidate in planned:
                if not candidate.exists():
                    candidate.mkdir(parents=True,exist_ok=False)
                    created.append(candidate)
            after=self._git_status(root)
            if after is None or after!=before:
                for candidate in reversed(created):
                    try:candidate.rmdir()
                    except OSError:pass
                return self._block(command,'GSDLC13C01_STRUCTURE_GIT_DRIFT_BLOCK','Structural reconciliation changed Git-observable project content and was rolled back.',metadata={'git_before_clean':before==b'','git_after_clean':after==b'' if after is not None else None})
        except Exception as exc:
            for candidate in reversed(created):
                try:candidate.rmdir()
                except OSError:pass
            return self._block(command,'GSDLC13C01_STRUCTURE_RECONCILIATION_BLOCK','Governed document namespace reconciliation failed closed.',metadata={'error':str(exc)})
        receipt={
            'schema_id':'devpilot.gsdlc13c01.structure_reconciliation.v1','workspace_id':workspace_id,
            'required_directories':[x.as_posix() for x in REQUIRED_DOCUMENT_PARENTS],
            'directories_created':[x.relative_to(root).as_posix() for x in created],
            'operator_project_writes':0,'project_content_files_written':0,
            'git_before_clean':before==b'','git_after_clean':after==b'','git_status_unchanged':True,
            'network_used':False,'external_api_used':False,'status':'PASS','completed_at':_now(),
        }
        receipt_path=self.root/STRUCTURE_RECEIPT_ROOT/re.sub(r'[^A-Za-z0-9_.-]','_',workspace_id)/'structure_reconciliation.json'
        receipt_path.parent.mkdir(parents=True,exist_ok=True)
        tmp=receipt_path.with_suffix('.tmp'); tmp.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(tmp,receipt_path)
        receipt['receipt_path']=str(receipt_path.relative_to(self.root)).replace('\\','/')
        return self._pass(command,'GSDLC13C01_STRUCTURE_RECONCILIATION_PASS','Governed document namespaces are available; no project content file or Git-visible mutation was introduced.',{'structure_reconciliation':receipt})

    @staticmethod
    def _git_status(workspace_root: Path) -> bytes | None:
        try:
            cp=subprocess.run(['git','-C',str(workspace_root),'status','--porcelain=v1','-z'],capture_output=True,timeout=5,check=False)
            return cp.stdout if cp.returncode==0 else None
        except Exception:
            return None

    @staticmethod
    def _identity(actor:str,actor_role:str,principal:str,effective_roles:list[str])->CommandResult|None:
        if not actor.strip() or actor.strip()!=principal.strip():return PreCodeWizardApplicationService._block('guided pre-code','GSDLC05E_SESSION_ACTOR_BINDING_BLOCK','Authenticated actor/session binding is required.')
        if actor_role not in effective_roles:return PreCodeWizardApplicationService._block('guided pre-code','GSDLC05E_ROLE_BINDING_BLOCK','Actor role must come from authenticated canonical roles.')
        if actor_role != 'owner':return PreCodeWizardApplicationService._block('guided pre-code','GSDLC05E_AUTHOR_ROLE_BLOCK','Current role cannot author/approve this pre-code stage.',metadata={'role':actor_role})
        return None
    @staticmethod
    def _base_commit(workspace_root:Path)->str:
        import subprocess
        try:
            cp=subprocess.run(['git','-C',str(workspace_root),'rev-parse','HEAD'],capture_output=True,text=True,timeout=5,check=False); v=cp.stdout.strip(); return v if re.fullmatch(r'[0-9a-f]{40}',v) else '0'*40
        except Exception:return '0'*40
    @staticmethod
    def _pass(command:str,fid:str,message:str,data:dict[str,Any])->CommandResult:return CommandResult(command,True,ExitCode.PASS,message,data=data,findings=[Finding(fid,message,Severity.INFO)])
    @staticmethod
    def _block(command:str,fid:str,message:str,metadata:dict[str,Any]|None=None)->CommandResult:return CommandResult(command,False,ExitCode.BLOCK,message,data={},findings=[Finding(fid,message,Severity.BLOCK,metadata=metadata or {})])
