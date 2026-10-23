"""R03-02: evidence-bound, read-only technical context over verified FROZEN inputs.

This resolver does not publish documents, choose a stack, call an LLM, or access
network resources. Existing PreCode lifecycle and PESP remain authorities.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

from devpilot_core.policy import redact_string
from devpilot_core.validation.artifact_profile_registry import ArtifactProfileRegistry
from devpilot_core.validation.project_profile import ProjectFacts


PROFILE_PATH = Path('.devpilot/rag/technical_source_profile.json')
_SHA = re.compile(r'^[a-f0-9]{64}$')
_INJECTION = re.compile(r'(?i)(ignore (all )?(previous|prior) instructions|\[/?system\]|<\|im_start\|>|developer message:|reveal (your|the) system prompt)')
_REQUIRED = ('product-vision', 'scope', 'requirements')


@dataclass(frozen=True)
class TechnicalSource:
    stage: str
    path: str
    raw_bytes: bytes
    expected_sha256: str
    lifecycle: str
    registered_active: bool = True


def _safe_path(path: str) -> bool:
    p = PurePosixPath(path)
    return bool(path) and not p.is_absolute() and '\\' not in path and '..' not in p.parts and p.suffix.lower() in {'.md', '.txt'} and path.startswith('docs/')


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_technical_context(
    root: Path, *, sources: tuple[TechnicalSource, ...], facts: ProjectFacts,
    optional_sources: tuple[TechnicalSource, ...] = (),
) -> dict[str, Any]:
    """Fail closed on required authority; exclude untrusted optional sources.

    `raw_bytes` and approved SHA come from the already-authoritative runtime
    document lifecycle. The source's raw SHA is intentionally verified; LF/CRLF
    differences in unrelated Git working-tree files are never compared here.
    """
    root = Path(root)
    policy = json.loads((root / PROFILE_PATH).read_text(encoding='utf-8'))
    if policy.get('profile_id') != 'TECHNICAL_RAG_SOURCE_PROFILE' or policy.get('profile_version') != '1.0.0':
        raise ValueError('TECH_CONTEXT_PROFILE_UNRECOGNIZED')
    if tuple(policy.get('required_stages', [])) != _REQUIRED:
        raise ValueError('TECH_CONTEXT_REQUIRED_STAGES_DRIFT')
    if len(sources) != len(_REQUIRED) or {s.stage for s in sources} != set(_REQUIRED):
        raise ValueError('TECH_CONTEXT_FROZEN_INPUTS_REQUIRED')
    if facts.state not in {'DRAFT', 'FROZEN'}:
        raise ValueError('TECH_CONTEXT_PROJECT_FACTS_INVALID')

    rejected: list[dict[str, str]] = []
    entries: list[dict[str, Any]] = []
    for item in (*sources, *optional_sources):
        required = item.stage in _REQUIRED and item in sources
        reason = ''
        if item in optional_sources and item.stage in _REQUIRED:
            reason = 'OPTIONAL_STAGE_SPOOF'
        elif item.stage not in {*_REQUIRED, 'adr', 'security-risk'}:
            reason = 'SOURCE_STAGE_UNKNOWN'
        elif not _safe_path(item.path):
            reason = 'UNSAFE_SOURCE_PATH'
        elif not item.registered_active:
            reason = 'SOURCE_NOT_IN_ACTIVE_AUTHORITY'
        elif required and item.lifecycle != 'FROZEN':
            reason = 'REQUIRED_NOT_FROZEN'
        elif not required and item.lifecycle not in {'FROZEN', 'CURRENT'}:
            reason = 'HISTORICAL_OR_SUPERSEDED'
        elif not _SHA.fullmatch(item.expected_sha256) or _hash(item.raw_bytes) != item.expected_sha256:
            reason = 'SOURCE_HASH_DRIFT'
        elif len(item.raw_bytes) > int(policy['limits']['max_source_bytes']):
            reason = 'SOURCE_TOO_LARGE'
        else:
            try:
                decoded = item.raw_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                reason = 'SOURCE_NOT_UTF8'
            else:
                if _INJECTION.search(decoded):
                    reason = 'POISONED_SOURCE'
        if reason:
            if required:
                raise ValueError(f'TECH_CONTEXT_{reason}:{item.stage}')
            rejected.append({'stage': item.stage, 'path': item.path, 'reason': reason})
            continue
        text = decoded.replace('\r\n', '\n').replace('\r', '\n')
        entries.append({'stage': item.stage, 'path': item.path, 'sha256': item.expected_sha256,
                        'lifecycle': item.lifecycle, 'text': str(redact_string(text)),
                        'required': required})

    order = {name: i for i, name in enumerate(_REQUIRED)}
    optional_order = {'adr': 3, 'security-risk': 4}
    entries.sort(key=lambda x: (order.get(x['stage'], optional_order.get(x['stage'], 5)), x['path']))
    cap = int(policy['limits']['max_context_chars'])
    per_source = int(policy['limits']['max_source_chars'])
    max_sources = int(policy['limits']['max_sources'])
    used = 0
    selected = []
    truncated = []
    for entry in entries:
        if len(selected) >= max_sources or used >= cap:
            truncated.append(entry['stage'])
            continue
        take = min(len(entry['text']), per_source, cap-used)
        if take < len(entry['text']):
            truncated.append(entry['stage'])
        selected.append({**entry, 'text': entry['text'][:take], 'selected_chars': take,
                         'text_truncated': take < len(entry['text'])})
        used += take

    pesp = ArtifactProfileRegistry(root).evaluate_project_applicability(facts)
    miasi = next(x for x in pesp['standards'] if x['id'] == 'MIASI')
    coverage = {
        'architecture': {'applicability': 'REQUIRED', 'rationale': 'Architecture design follows confirmed Product Definition.'},
        'adr': {'applicability': 'CONDITIONAL', 'rationale': 'Material technology/security decisions are assessed during Architecture; no ADR invented.'},
        'security-risk': {'applicability': 'CONDITIONAL', 'rationale': 'Risk inputs depend on actual architecture and product threat scope.'},
        'miasi': {'applicability': miasi['applicability'], 'rationale': miasi['rationale'], 'evidence_refs': miasi.get('evidence_refs', [])},
    }
    manifest = [{k: row[k] for k in ('stage', 'path', 'sha256', 'lifecycle', 'text_truncated')} for row in selected]
    compact = {'profile_version': policy['profile_version'], 'project_hash': pesp['fingerprint'],
               'sources': manifest, 'excluded': rejected, 'truncated': truncated}
    context_sha256 = _hash(json.dumps(compact, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    status = 'PASS' if not truncated and miasi['applicability'] != 'REVIEW_REQUIRED' else 'REVIEW_REQUIRED'
    return {'profile_id': policy['profile_id'], 'profile_version': policy['profile_version'],
            'project_context_sha256': pesp['fingerprint'], 'context_sha256': context_sha256,
            'status': status, 'sources': selected, 'source_refs': manifest, 'excluded': rejected,
            'truncated_stages': sorted(set(truncated)), 'pesp': coverage,
            'limitations': ['Local read-only deterministic selection, not professional semantic quality certification.',
                            'Unconfirmed product AI scope requires review, not fabricated NOT_APPLICABLE.'],
            'safety': {'network_used': False, 'external_api_used': False, 'llm_used': False,
                       'source_mutations': False, 'max_context_chars': cap, 'selected_chars': used}}
