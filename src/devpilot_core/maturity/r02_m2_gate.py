"""MP132 R02-10 M2: read-only, conservative Pilot B Product Definition acceptance.

Not a publisher, model evaluator, or replacement for lifecycle authority.
Unknown proof is PARTIAL, not PASS; material drift is BLOCK. No network/writes.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

STAGES = {
    'product-vision': 'docs/00_product/product_vision.md',
    'scope': 'docs/00_product/mvp_scope.md',
    'requirements': 'docs/01_requirements/requirements_specification.md',
}
HEX = re.compile(r'^[a-f0-9]{64}$')


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob.replace(b'\r\n', b'\n').replace(b'\r', b'\n')).hexdigest()


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('M2_JSON_NOT_OBJECT')
    return data


def _finding(items: list, code: str, status: str, explanation: str):
    items.append({'rule_id': code, 'status': status, 'explanation': explanation})


def assess_pilot_b(*, workspace: Path, platform: Path, project_id: str,
                   closure: Mapping[str, Any], model_evidence: Mapping[str, Any] | None,
                   ui_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate live workspace and immutable historical receipts without modifying them.

    model_evidence is an *independent* receipt, not a self-asserted string entered
    by a user. The model's competence is not asserted merely by an Ollama call.
    UI snapshots/Owner review are outside this function and must be provided as
    separately captured evidence before M2 can move beyond PARTIAL.
    """
    workspace, platform = Path(workspace), Path(platform)
    findings: list[dict] = []
    checks: dict[str, Any] = {}
    # Neither the physical Markdown frontmatter status nor a candidate receipt
    # is allowed to replace server-authoritative lifecycle status.
    state_path = platform / 'outputs/pre_code_wizard/gsdlc_05_e' / project_id / 'state.json'
    try:
        state = _read_json(state_path)
    except (OSError, ValueError, TypeError) as exc:
        state = {}
        _finding(findings, 'M2_LIFECYCLE_UNAVAILABLE', 'BLOCK', type(exc).__name__)
    if state and state.get('workspace_id') != project_id:
        _finding(findings, 'M2_WORKSPACE_AUTHORITY_DRIFT', 'BLOCK', 'Identificador runtime diferente')
    project_file = workspace / '.devpilot/project.yaml'
    try:
        from devpilot_core.workspace.manager import parse_project_yaml_metadata
        metadata = parse_project_yaml_metadata(project_file)
        need = str(metadata.get('business_need') or '').strip()
        bound_id = str(metadata.get('project_id') or '')
    except (OSError, ValueError, TypeError):
        need, bound_id = '', ''
    checks['b0'] = {'project_id_consistent': bound_id == project_id,
                    'need_present': bool(need), 'source': '.devpilot/project.yaml'}
    if not need or bound_id != project_id:
        _finding(findings, 'M2_B0_MISSING_OR_UNBOUND', 'BLOCK', 'Necesidad Owner / project_id inválidos')
    observed: dict[str, dict[str, Any]] = {}
    stages = state.get('stages') if isinstance(state.get('stages'), dict) else {}
    for stage, relative in STAGES.items():
        row = stages.get(stage) if isinstance(stages.get(stage), dict) else {}
        path = workspace / relative
        # Only fixed trusted relative paths are read; no path selected from model data.
        try:
            if path.is_symlink(): raise ValueError('SYMLINK_NOT_ALLOWED')
            raw = path.read_bytes()
            sha = digest(raw)
        except (OSError, ValueError):
            sha = ''
        approved = str(row.get('approved_sha256') or '').lower()
        recorded = str(row.get('content_sha256') or '').lower()
        ids = {k: str(row.get(k) or '') for k in ('approval_id','execution_id')}
        valid = bool(sha and row.get('status') == 'FROZEN' and all(ids.values())
                     and (approved == sha or approved == hashlib.sha256(raw).hexdigest()))
        observed[stage] = {'source': relative, 'sha256_lf': sha, 'status': row.get('status'),
                           'receipt_ids_present': all(ids.values()), 'frozen_verified': valid,
                           'draft_content_hash_matches': (not recorded or recorded == sha),
                           'authoring_mode': str(row.get('mode') or 'NOT_AVAILABLE'),
                           'owner_edited': bool((row.get('derivation') or {}).get('owner_edited')) if isinstance(row.get('derivation'), dict) else False}
        if not valid:
            _finding(findings, 'M2_FROZEN_DRIFT_'+stage.upper().replace('-', '_'), 'BLOCK',
                     'Falta FROZEN / aprobación / apply o hash publicado diferente')
        if str(row.get('mode') or '') != 'LOCAL_MODEL':
            _finding(findings, 'M2_LOCAL_AUTHORING_NOT_PROVEN_'+stage.upper().replace('-', '_'), 'PARTIAL',
                     'El modo local no queda acreditado por el estado runtime')
    checks['documents'] = observed
    if closure.get('result') != 'PASS' or closure.get('project_id') != project_id or closure.get('requirements_state') != 'FROZEN':
        _finding(findings, 'M2_PREDECESSOR_CLOSURE_NOT_PROVEN', 'PARTIAL', 'Recibo R02-07 incompleto o no vinculado')
    if observed.get('requirements', {}).get('sha256_lf') != closure.get('source_content_sha256_lf'):
        _finding(findings, 'M2_REQUIREMENTS_CLOSURE_DRIFT', 'BLOCK', 'Hash del cierre R02-07 diferente al source actual')
    # Scope cross-reference does not by itself prove substantive equivalence.
    scope_doc = workspace / STAGES['scope']
    req_doc = workspace / STAGES['requirements']
    try:
        from devpilot_core.validation.product_definition_coverage import _rf_origins
        scope = scope_doc.read_text(encoding='utf-8-sig')
        req = req_doc.read_text(encoding='utf-8-sig')
        scoped = sorted(set(re.findall(r'\bSC-IN-\d{2,3}\b', scope, flags=re.I)))
        origins = _rf_origins(req)
        misses = [x for x in scoped if x.upper() not in origins]
        checks['scope_to_requirements'] = {'scope_ids': scoped, 'missing_rf_origins': misses,
                                            'presence_only_not_semantic_equivalence': True}
        if misses:
            _finding(findings, 'M2_SCOPE_RF_COVERAGE_MISSING', 'BLOCK', 'Capacidades sin RF de origen: '+','.join(misses))
        if not scoped:
            _finding(findings, 'M2_SCOPE_IDS_NOT_OBSERVABLE', 'PARTIAL', 'No existen SC-IN verificables')
    except (OSError, ValueError):
        _finding(findings, 'M2_SCOPE_RF_UNAVAILABLE', 'BLOCK', 'No es posible leer Scope/Requirements')
    model = model_evidence or {}
    # An actual COR221 call record proves at least a real local-model response,
    # but not high first-draft quality or all three stage authoring histories.
    recorded_calls = ((model.get('cor221_operation') or {}).get('model_calls_started')
                      if isinstance(model, Mapping) else None)
    entries = (model.get('cor221_operation') or {}).get('per_target') if isinstance(model, Mapping) else None
    model_proven = bool(isinstance(recorded_calls, int) and recorded_calls > 0 and isinstance(entries, list)
                        and len(entries) == recorded_calls and all(e.get('status') == 'PASS' for e in entries))
    checks['local_model'] = {'requirements_focal_real_call_receipt': model_proven,
                             'call_count_recorded': recorded_calls if model_proven else None,
                             'all_stages_real_competence_independently_proven': False,
                             'quality_owner_supervised': True}
    if not model_proven:
        _finding(findings, 'M2_LOCAL_MODEL_REAL_RECEIPT_UNPROVEN', 'PARTIAL', 'No se validó el recibo de inferencia local real')
    # Pilot B received material Owner rewrites, so competence cannot be
    # certified solely from presence of candidates or lexical gates.
    _finding(findings, 'M2_LOCAL_FIRST_DRAFT_QUALITY_LIMITED', 'REVIEW_REQUIRED',
             'La revisión Owner fue sustantiva; el rendimiento profesional autónomo sigue sin acreditarse')
    ui = ui_evidence or {}
    checks['browser'] = {'owner_journey_observed': ui.get('owner_journey_observed') is True,
                         'restart_observed': ui.get('restart_observed') is True,
                         'owner_notes_present': ui.get('owner_notes_present') is True}
    if not all(checks['browser'].values()):
        _finding(findings, 'M2_BROWSER_ACCEPTANCE_INCOMPLETE', 'PARTIAL',
                 'Falta observación Owner de UI normal/reinicio o sus notas')
    _finding(findings, 'M2_SEMANTIC_EQUIVALENCE_UNPROVEN', 'REVIEW_REQUIRED',
             'La cobertura literal no acredita equivalencia ni ausencia de decisiones inventadas')
    decision = ('BLOCK' if any(f['status'] == 'BLOCK' for f in findings) else
                'PARTIAL' if any(f['status'] == 'PARTIAL' for f in findings) else
                'PASS_WITH_FINDINGS' if findings else 'PASS')
    return {'schema':'MP132.R02.M2.acceptance.v1', 'milestone':'M2_PRODUCT_DEFINITION_LOCAL_REAL',
            'decision':decision, 'project_id':project_id, 'checks':checks, 'findings':findings,
            'limitations':['Evidencia modelo local no garantiza calidad autónoma',
                           'No se afirma equivalencia semántica basada en IDs',
                           'Sin llamadas al modelo, red o writes de proyecto en esta evaluación'],
            'operator_project_writes':0, 'model_calls':0, 'external_api_calls':0,
            'next_sprint_authorized':False, 'mp_1b_authorized':False}
