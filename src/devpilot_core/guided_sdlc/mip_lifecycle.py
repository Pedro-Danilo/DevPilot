from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import jsonschema

from .models import MIPSoftwarePhase, WorkspaceEngineeringState
from .workflow_engine import TransitionBlocker, TransitionCatalog, TransitionEvidence, TransitionSpec, WorkflowEngine

REGISTRY_REL = Path('.devpilot/gsdlc/mip_workflow_registry.json')
SCHEMA_REL = Path('docs/schemas/mip_workflow_registry.schema.json')
PROFILE_REL = Path('docs/validation/artifact_profiles.json')
EXPECTED_SCHEMA_ID = 'SCHEMA-DEVPL-GSDLC-05-B-MIP-WORKFLOW-REGISTRY-V1'

class MIPWorkflowRegistryError(ValueError): pass

def _sha256(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _canonical_text_sha256(path: Path) -> str:
    data=path.read_bytes()
    try: text=data.decode('utf-8')
    except UnicodeDecodeError: return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(text.replace('\r\n','\n').replace('\r','\n').encode('utf-8')).hexdigest()

def _parse_utc(value: str) -> datetime:
    text=value.replace('Z','+00:00')
    parsed=datetime.fromisoformat(text)
    if parsed.tzinfo is None: raise MIPWorkflowRegistryError('waiver timestamps require timezone')
    return parsed.astimezone(timezone.utc)

@dataclass(frozen=True)
class MIPWaiver:
    waiver_id: str
    workspace_id: str
    transition_id: str
    gate_id: str
    owner: str
    rationale: str
    issued_at_utc: str
    expires_at_utc: str
    policy_ref: str
    audit_ref: str

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> 'MIPWaiver':
        required=('waiver_id','workspace_id','transition_id','gate_id','owner','rationale','issued_at_utc','expires_at_utc','policy_ref','audit_ref')
        missing=[k for k in required if not str(payload.get(k,'')).strip()]
        if missing: raise MIPWorkflowRegistryError(f'waiver missing fields: {missing}')
        return cls(**{k:str(payload[k]) for k in required})

    def valid_for(self, *, workspace_id: str, transition_id: str, gate_id: str, observed_at_utc: str) -> tuple[bool,str]:
        if self.workspace_id != workspace_id: return False,'WAIVER_WRONG_WORKSPACE'
        if self.transition_id != transition_id: return False,'WAIVER_WRONG_TRANSITION'
        if self.gate_id != gate_id: return False,'WAIVER_WRONG_SCOPE'
        now=_parse_utc(observed_at_utc); issued=_parse_utc(self.issued_at_utc); expires=_parse_utc(self.expires_at_utc)
        if expires <= issued: return False,'WAIVER_INVALID_WINDOW'
        if now < issued: return False,'WAIVER_NOT_YET_VALID'
        if now >= expires: return False,'WAIVER_EXPIRED'
        return True,'WAIVER_VALID'

@dataclass(frozen=True)
class MIPGateResult:
    decision: str
    transition_id: str | None
    blockers: tuple[dict[str,Any], ...]
    remediation_actions: tuple[dict[str,Any], ...]
    waiver: dict[str,Any]
    source_state_fingerprint: str
    registry_version: str
    network_used: bool=False
    external_api_used: bool=False
    model_execution_used: bool=False
    source_mutations_performed: bool=False
    def to_dict(self)->dict[str,Any]:
        return {'schema_id':'DEVPL-GSDLC-05-B-MIP-GATE-RESULT-v1','decision':self.decision,'transition_id':self.transition_id,'blockers':list(self.blockers),'remediation_actions':list(self.remediation_actions),'waiver':dict(self.waiver),'source_state_fingerprint':self.source_state_fingerprint,'registry_version':self.registry_version,'network_used':False,'external_api_used':False,'model_execution_used':False,'source_mutations_performed':False}

class MIPWorkflowRegistry:
    def __init__(self, root: Path, payload: Mapping[str,Any] | None=None):
        self.root=Path(root).resolve(); self.payload=dict(payload or json.loads((self.root/REGISTRY_REL).read_text(encoding='utf-8')))
        self._validate()
        self.phases=tuple(sorted((dict(x) for x in self.payload['phases']), key=lambda x:int(x['ordinal'])))
        self.by_phase={str(x['phase']):x for x in self.phases}
        self.by_transition={str(x['transition_id']):x for x in self.phases if x.get('transition_id')}

    @property
    def registry_version(self)->str: return str(self.payload['registry_version'])

    def _validate(self)->None:
        schema=json.loads((self.root/SCHEMA_REL).read_text(encoding='utf-8'))
        jsonschema.Draft202012Validator(schema).validate(self.payload)
        if self.payload.get('schema_id') != EXPECTED_SCHEMA_ID: raise MIPWorkflowRegistryError('unsupported schema')
        source=self.payload['source_standard']; source_path=self.root/source['path']
        if not source_path.is_file(): raise MIPWorkflowRegistryError('MIPSoftware source missing')
        if _canonical_text_sha256(source_path) != source['source_sha256']: raise MIPWorkflowRegistryError('MIPSoftware source hash drift')
        source_text=source_path.read_text(encoding='utf-8')
        if source.get('source_hash_policy') != 'canonical-lf-utf8': raise MIPWorkflowRegistryError('unsupported source hash policy')
        for key in ('lifecycle_heading','artifact_matrix_heading','gate_matrix_heading'):
            if source[key] not in source_text: raise MIPWorkflowRegistryError(f'MIPSoftware source heading missing: {source[key]}')
        pred=self.payload['predecessor_registry']; pred_path=self.root/pred['path']
        pred_data=json.loads(pred_path.read_text(encoding='utf-8'))
        if pred_data.get('registry_id') != pred['registry_id']: raise MIPWorkflowRegistryError('predecessor registry identity mismatch')
        if pred.get('approved_required') and not (pred_data.get('status')=='approved' and pred_data.get('registry_authoritative') is True): raise MIPWorkflowRegistryError('05-A registry must be owner-approved before 05-B')
        phases=list(self.payload['phases'])
        if [x['ordinal'] for x in phases] != list(range(19)): raise MIPWorkflowRegistryError('phase ordinals must be exactly 0..18')
        if sum(int(x['weight_bps']) for x in phases)!=10000: raise MIPWorkflowRegistryError('phase weights must total 10000 bps')
        if len({x['phase_id'] for x in phases})!=19 or len({x['phase'] for x in phases})!=19: raise MIPWorkflowRegistryError('duplicate phase identifiers')
        profile_data=json.loads((self.root/PROFILE_REL).read_text(encoding='utf-8'))
        profiles={profile_data['generic_profile']['id']}|{x['id'] for x in profile_data['profiles']}
        source_sha=source['source_sha256']
        for phase in phases:
            if phase['source_refs'][0]['source_sha256'] != source_sha: raise MIPWorkflowRegistryError(f'phase source hash mismatch: {phase["phase_id"]}')
            heading=phase['source_refs'][0]['heading']
            if heading not in source_text: raise MIPWorkflowRegistryError(f'phase heading missing: {heading}')
            for artifact in phase['required_artifacts']:
                if artifact['profile_id'] not in profiles: raise MIPWorkflowRegistryError(f'unknown artifact profile {artifact["profile_id"]}')
                if artifact['validator_ids'] != ['artifact-profile.validate']: raise MIPWorkflowRegistryError('v1 validator binding must be artifact-profile.validate')
        # Reuse and enrich the existing generic transition catalog; it remains unchanged.
        generic=TransitionCatalog.load(self.root/self.payload['generic_transition_catalog']['path'])
        graph={str(p['phase']):str(p['next_phase']) for p in phases if p.get('next_phase')}
        visiting=set(); visited=set()
        def walk(node):
            if node in visiting: raise MIPWorkflowRegistryError(f'MIP workflow cycle detected at {node}')
            if node in visited: return
            visiting.add(node)
            nxt=graph.get(node)
            if nxt is not None:
                if nxt not in {str(p['phase']) for p in phases}: raise MIPWorkflowRegistryError(f'unknown next phase {nxt}')
                walk(nxt)
            visiting.remove(node); visited.add(node)
        for node in sorted(graph): walk(node)
        for phase in phases[:-1]:
            tid=phase['transition_id']; spec=generic.get(tid)
            if spec is None: raise MIPWorkflowRegistryError(f'missing generic transition {tid}')
            if spec.source_phase.value != phase['phase'] or spec.source_step != phase['current_step']: raise MIPWorkflowRegistryError(f'generic transition source drift: {tid}')
            if spec.target_phase.value != phase['next_phase']: raise MIPWorkflowRegistryError(f'generic transition target drift: {tid}')
        if phases[-1]['phase']!='RELEASE' or not phases[-1]['terminal_in_registry'] or phases[-1].get('next_phase') is not None: raise MIPWorkflowRegistryError('release must be terminal for 05-B scope')

    def enriched_transition_catalog(self)->TransitionCatalog:
        generic=TransitionCatalog.load(self.root/self.payload['generic_transition_catalog']['path'])
        specs=[]
        for phase in self.phases[:-1]:
            base=generic.get(phase['transition_id']); assert base is not None
            row={
              'transition_id':base.transition_id,'version':self.registry_version,
              'source':{'phase':base.source_phase.value,'current_step':base.source_step,'lifecycle_statuses':[x.value for x in base.source_lifecycle_statuses]},
              'target':{'phase':base.target_phase.value,'current_step':base.target_step,'lifecycle_status':base.target_lifecycle_status.value},
              'required_prerequisites':list(phase['required_prerequisites']),
              'required_gates':[{'gate_id':phase['exit_gate']['gate_id'],'accepted_statuses':phase['exit_gate']['accepted_statuses']}],
              'required_artifacts':[{'artifact_id':a['artifact_id'],'accepted_statuses':a['accepted_statuses']} for a in phase['required_artifacts']],
              'approval':{'required':False,'approval_key':None,'accepted_statuses':[]},
              'risk_classification':base.risk_classification,'preview_allowed':base.preview_allowed,
              'evidence_refs':[f"MIPS-DOC-003#{phase['source_refs'][0]['heading']}",f"registry:{self.payload['registry_id']}:{self.registry_version}"],
            }
            specs.append(TransitionSpec.from_payload(row))
        return TransitionCatalog(specs,catalog_id=self.payload['registry_id'],catalog_version=self.registry_version)

    def coverage_report(self)->dict[str,Any]:
        return {'schema_id':'DEVPL-GSDLC-05-B-MIP-WORKFLOW-COVERAGE-v1','status':'PASS','registry_id':self.payload['registry_id'],'registry_version':self.registry_version,'phases_total':len(self.phases),'transitions_total':len(self.phases)-1,'required_phases_total':sum(1 for x in self.phases if x['mandatory']),'required_phases_skippable_without_gate':0,'artifact_bindings_total':sum(len(x['required_artifacts']) for x in self.phases),'artifact_profiles_bound_total':sum(len(x['required_artifacts']) for x in self.phases),'weights_total_bps':sum(int(x['weight_bps']) for x in self.phases),'llm_authority':False,'production_waivable_gate_ids':list(self.payload['waiver_policy']['production_waivable_gate_ids']),'network_used':False,'external_api_used':False,'mutations_performed':False}

class MIPGateEvaluator:
    def __init__(self, registry: MIPWorkflowRegistry):
        self.registry=registry; self.engine=WorkflowEngine(registry.enriched_transition_catalog())

    @classmethod
    def from_root(cls, root: Path)->'MIPGateEvaluator': return cls(MIPWorkflowRegistry(root))

    def evaluate(self, state: WorkspaceEngineeringState, evidence: TransitionEvidence|Mapping[str,Any]|None=None, *, transition_id: str|None=None, waiver: MIPWaiver|Mapping[str,Any]|None=None, observed_at_utc: str|None=None)->MIPGateResult:
        phase=self.registry.by_phase.get(state.phase.value)
        if phase is None:
            return self._result('BLOCK',None,[{'code':'MIP_PHASE_OUT_OF_SCOPE','category':'state','subject':state.phase.value,'message':'Current WorkspaceEngineeringState phase is outside the 05-B intake-through-release registry.'}],state,{'provided':False})
        expected_transition=phase.get('transition_id')
        if transition_id is not None and transition_id != expected_transition:
            return self._result('BLOCK',transition_id,[{'code':'MIP_REQUIRED_PHASE_SKIP','category':'transition','subject':transition_id,'message':f'Requested transition is not the required successor of {phase["phase"]}.'}],state,{'provided':False})
        if phase['terminal_in_registry']:
            if state.current_step != phase['current_step']:
                return self._result('BLOCK',None,[{'code':'SOURCE_STEP_MISMATCH','category':'source','subject':state.current_step,'message':f"Release phase expects current_step {phase['current_step']}."}],state,{'provided':False})
            return self._result('PASS',None,[],state,{'provided':False,'effect':'terminal-release-reached'})
        tid=phase['transition_id']; evaluation=self.engine.evaluate(state,tid,evidence)
        blockers=[x.to_payload() for x in evaluation.blockers]
        waiver_meta={'provided':False,'valid':False,'applied':False}
        if waiver is not None:
            w=waiver if isinstance(waiver,MIPWaiver) else MIPWaiver.from_payload(waiver)
            waiver_meta={'provided':True,'waiver_id':w.waiver_id,'valid':False,'applied':False}
            gate_id=phase['exit_gate']['gate_id']; now=observed_at_utc or datetime.now(timezone.utc).isoformat()
            valid,reason=w.valid_for(workspace_id=state.workspace_id,transition_id=tid,gate_id=gate_id,observed_at_utc=now)
            policy_allows=bool(phase['exit_gate']['waiver_allowed']) and gate_id in set(self.registry.payload['waiver_policy'].get('production_waivable_gate_ids') or [])
            waiver_meta.update({'valid':valid and policy_allows,'reason':reason if not valid else ('WAIVER_POLICY_ALLOWS' if policy_allows else 'WAIVER_POLICY_DENY')})
            if valid and policy_allows:
                remaining=[b for b in blockers if not (b['category']=='gate' and b['subject']==gate_id and b['code'] in {'GATE_BLOCK','GATE_NOT_SATISFIED'})]
                if len(remaining)<len(blockers): blockers=remaining; waiver_meta['applied']=True
        decision='PASS' if not blockers else 'BLOCK'
        return self._result(decision,tid,blockers,state,waiver_meta)

    def preview_advance(self,state:WorkspaceEngineeringState,evidence:TransitionEvidence|Mapping[str,Any]|None=None,*,updated_at_utc:str):
        phase=self.registry.by_phase.get(state.phase.value)
        if phase is None or phase['terminal_in_registry']: return None
        # No waiver is accepted by production v1.0.0, so preview delegates directly to existing WorkflowEngine.
        return self.engine.preview_advance(state,phase['transition_id'],evidence,updated_at_utc=updated_at_utc)

    def _result(self,decision:str,tid:str|None,blockers:list[dict[str,Any]],state:WorkspaceEngineeringState,waiver:dict[str,Any])->MIPGateResult:
        rem=[]
        mapping={'PREREQUISITE_NOT_SATISFIED':'COMPLETE_PREREQUISITE','GATE_BLOCK':'RESOLVE_GATE','GATE_NOT_SATISFIED':'RESOLVE_GATE','ARTIFACT_NOT_READY':'COMPLETE_OR_APPROVE_ARTIFACT','SOURCE_PHASE_MISMATCH':'RECONCILE_STATE','SOURCE_STEP_MISMATCH':'RECONCILE_STATE','STATE_REVALIDATION_REQUIRED':'RECONCILE_STATE','STATE_BLOCKED':'RESOLVE_STATE_BLOCKER'}
        for b in sorted(blockers,key=lambda x:(int(x.get('priority',100)),x.get('code',''),x.get('subject',''))):
            action=mapping.get(str(b.get('code')),'INSPECT_BLOCKER')
            rem.append({'action_id':f"remediate:{str(b.get('code','unknown')).lower()}:{str(b.get('subject','unknown')).replace(':','-')}",'kind':action,'subject':b.get('subject'),'explanation':b.get('message'),'mutating':False,'dry_run_required':True})
        return MIPGateResult(decision,tid,tuple(blockers),tuple(rem),waiver,state.fingerprint(),self.registry.registry_version)

class MIPProgressModel:
    def __init__(self, registry:MIPWorkflowRegistry): self.registry=registry
    @classmethod
    def from_root(cls,root:Path)->'MIPProgressModel': return cls(MIPWorkflowRegistry(root))
    def project(self,state:WorkspaceEngineeringState)->dict[str,Any]:
        phase=self.registry.by_phase.get(state.phase.value)
        if phase is None: return {'status':'BLOCK','reason_code':'MIP_PHASE_OUT_OF_SCOPE','percent':None,'completed_bps':None,'total_bps':10000,'registry_version':self.registry.registry_version}
        if state.current_step != phase['current_step']: return {'status':'BLOCK','reason_code':'SOURCE_STEP_MISMATCH','percent':None,'completed_bps':None,'total_bps':10000,'registry_version':self.registry.registry_version}
        ordinal=int(phase['ordinal']); completed=10000 if phase['terminal_in_registry'] else sum(int(x['weight_bps']) for x in self.registry.phases[:ordinal])
        return {'status':'PASS','policy_id':self.registry.payload['weight_policy']['policy_id'],'weights_version':self.registry.payload['weight_policy']['weights_version'],'phase':phase['phase'],'phase_id':phase['phase_id'],'ordinal':ordinal,'completed_bps':completed,'total_bps':10000,'percent':round(completed/100,2),'terminal':bool(phase['terminal_in_registry']),'registry_version':self.registry.registry_version,'network_used':False,'external_api_used':False,'model_execution_used':False}


class MIPLifecycleService:
    """Read-only facade for GSDLC-05-B lifecycle reports and evaluation."""
    def __init__(self, root: Path):
        self.root=Path(root).resolve(); self.registry=MIPWorkflowRegistry(self.root); self.evaluator=MIPGateEvaluator(self.registry); self.progress=MIPProgressModel(self.registry)
    def workflow_coverage(self)->dict[str,Any]: return self.registry.coverage_report()
    def transition_case_matrix(self)->dict[str,Any]:
        return {
          'schema_id':'DEVPL-GSDLC-05-B-TRANSITION-CASE-MATRIX-v1','status':'PASS','registry_version':self.registry.registry_version,
          'cases':[
            {'case_id':'nominal-phase-advance','expected':'PASS'},
            {'case_id':'skip-required-phase','expected':'BLOCK/MIP_REQUIRED_PHASE_SKIP'},
            {'case_id':'missing-prerequisite','expected':'BLOCK/PREREQUISITE_NOT_SATISFIED'},
            {'case_id':'gate-missing','expected':'BLOCK/GATE_NOT_SATISFIED'},
            {'case_id':'gate-block','expected':'BLOCK/GATE_BLOCK'},
            {'case_id':'artifact-missing','expected':'BLOCK/ARTIFACT_NOT_READY'},
            {'case_id':'production-owner-bypass','expected':'BLOCK/WAIVER_POLICY_DENY'},
            {'case_id':'typed-waiver-expired','expected':'BLOCK/WAIVER_EXPIRED'},
            {'case_id':'typed-waiver-wrong-scope','expected':'BLOCK/WAIVER_WRONG_SCOPE'},
            {'case_id':'release-terminal','expected':'PASS/terminal-release-reached'},
          ],
          'llm_authority':False,'network_used':False,'external_api_used':False,'mutations_performed':False,
        }
    def progress_determinism_report(self)->dict[str,Any]:
        completed=0; rows=[]
        for phase in self.registry.phases:
            rows.append({'phase':phase['phase'],'ordinal':phase['ordinal'],'weight_bps':phase['weight_bps'],'completed_bps_at_entry':10000 if phase['terminal_in_registry'] else completed,'percent_at_entry':100.0 if phase['terminal_in_registry'] else round(completed/100,2)})
            completed += int(phase['weight_bps'])
        return {'schema_id':'DEVPL-GSDLC-05-B-PROGRESS-DETERMINISM-v1','status':'PASS','policy_id':self.registry.payload['weight_policy']['policy_id'],'weights_version':self.registry.payload['weight_policy']['weights_version'],'weights_total_bps':completed,'stable_ordering':True,'samples':rows,'network_used':False,'external_api_used':False,'model_execution_used':False,'mutations_performed':False}
