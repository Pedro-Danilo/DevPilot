"""R03-04 read-only Technology/ADR companion projection for Architecture.

Architecture's existing review/approval is the sole decision authority.  This
module neither invokes a model nor installs a stack, writes project source,
creates an approval, or guesses that a proposed ADR was accepted by its author.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

PROFILE_VERSION = 'mp132.r03_04.tech_decision.v1'
_HEADER = re.compile(r'^##\s+(.+?)\s*$', re.M)
_ADR = re.compile(r'^###\s+(ADR-[A-Z0-9-]{3,24})\s*[—–:-]\s*(.+?)\s*$', re.I | re.M)
_FIELD = re.compile(r'^\s*(?:[-*]\s*)?\*\*(Contexto|Decisi[oó]n|Alternativas|Consecuencias|Justificaci[oó]n|Costo|Soporte|Seguridad):?\*\*\s*:?\s*(.+)$', re.I | re.M)
_SHA = re.compile(r'^[0-9a-f]{64}$')
_UNAUTHORIZED_INSTALL = re.compile(
    r'(?i)\b(?:instalaremos|instalar[aá]|instala(?:r)?|provisionaremos|provisionar[aá])\b'
    r'[^.\n]{0,90}\b(?:autom[aá]ticamente|sin aprobaci[oó]n|sin autorizaci[oó]n)\b'
)
_FALSE_TECH_APPROVAL = re.compile(
    r'(?i)\b(?:stack|perfil tecnol[oó]gico|framework|motor de base de datos)\b'
    r'[^.\n]{0,90}\b(?:ya aprobado|aprobado por el owner|aprobada por el owner)\b'
)


def _affirmative_action(pattern: re.Pattern[str], value: str) -> bool:
    """Do not misread an explicit prohibition as a proposed sensitive action."""
    for match in pattern.finditer(value):
        prior = value[max(0, match.start() - 40):match.start()]
        if re.search(r'(?i)(?:\bno\b|\bnunca\b|\bevitar\b|\bprohibid[oa]\b|\bse proh[ií]be)\s*$', prior):
            continue
        return True
    return False


def _logical(value: str) -> str:
    return str(value or '').replace('\r\n', '\n').replace('\r', '\n')


def _sha(value: str) -> str:
    return hashlib.sha256(_logical(value).encode('utf-8')).hexdigest()


def _section(text: str, aliases: set[str]) -> str:
    markers = list(_HEADER.finditer(text))
    for i, match in enumerate(markers):
        if match.group(1).strip().casefold() in aliases:
            return text[match.end():markers[i+1].start() if i+1 < len(markers) else len(text)].strip()
    return ''


def _slug(value: str) -> str:
    plain = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+', '-', plain).strip('-')[:48] or 'decision'


def inspect_technology_decisions(content: str, *, source_refs: list[dict[str, Any]] | None = None,
                                 lifecycle: str = 'DRAFT', architecture_approval_id: str = '',
                                 frozen_sha256: str = '', source_sha256_verified: bool = False) -> dict[str, Any]:
    """Project-neutral, bounded observations; not a self-certifying quality gate.

    A material, demonstrable violation is BLOCK; absent professional evidence is
    REVIEW_REQUIRED.  A real approval is derived only from FROZEN runtime/source.
    """
    text = _logical(content)
    checks: list[dict[str, str]] = []

    def issue(rule: str, severity: str, reason: str) -> None:
        checks.append({'rule_id': rule, 'severity': severity, 'message': reason})

    technology = _section(text, {'tecnología y alternativas', 'tecnologia y alternativas', 'tecnología', 'tecnologia'})
    adr_text = _section(text, {'adrs materiales', 'adrs'})
    if not technology:
        issue('TECH_CONTEXT_MISSING', 'REVIEW_REQUIRED', 'No consta una sección Technology con drivers, alternativas y consecuencias.')
    if technology and not re.search(r'(?i)alternativ|opci[oó]n|comparaci[oó]n|trade.?off', technology):
        issue('TECH_ALTERNATIVES_UNEXPLAINED', 'REVIEW_REQUIRED', 'La selección tecnológica carece de comparación o alternativa identificable.')
    if technology and not re.search(r'(?i)costo|licencia|soporte|seguridad|riesgo|operaci[oó]n|mantenibilidad', technology):
        issue('TECH_DRIVERS_UNEXPLAINED', 'REVIEW_REQUIRED', 'Revisar coste, soporte, seguridad y operaciones antes de decidir.')
    if _affirmative_action(_UNAUTHORIZED_INSTALL, technology + '\n' + adr_text):
        issue('TECH_AUTOINSTALL_DENY', 'BLOCK', 'La propuesta ordena instalar/provisionar automáticamente sin autorización material.')
    if lifecycle in {'MISSING', 'DRAFT', 'FINDINGS', 'APPROVAL_REQUIRED'} and _FALSE_TECH_APPROVAL.search(technology + '\n' + adr_text):
        issue('TECH_UNGROUNDED_APPROVAL', 'BLOCK', 'Una selección tecnológica propuesta se presenta como ya aprobada sin recibo de Architecture FROZEN.')

    adr_matches = list(_ADR.finditer(adr_text))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, match in enumerate(adr_matches):
        adr_id = match.group(1).upper()
        title = match.group(2).strip()
        block = adr_text[match.end():adr_matches[i+1].start() if i+1 < len(adr_matches) else len(adr_text)].strip()
        fields = {unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii').lower(): value.strip()
                  for name, value in _FIELD.findall(block)}
        if adr_id in seen:
            issue('TECH_ADR_DUPLICATE', 'BLOCK', 'Identificador ADR duplicado dentro de Architecture: '+adr_id)
            continue
        seen.add(adr_id)
        required = ('contexto', 'decision', 'alternativas', 'consecuencias')
        missing = [key for key in required if not fields.get(key)]
        if missing:
            issue('TECH_ADR_INCOMPLETE', 'BLOCK', adr_id+': faltan campos materiales '+', '.join(missing))
        standalone_path = f'docs/02_architecture/adrs/{adr_id}-{_slug(title)}.md'
        records.append({'adr_id': adr_id, 'title': title,
                        'proposal': fields.get('decision', ''),
                        'rationale': fields.get('justificacion', ''),
                        'alternatives': fields.get('alternativas', ''),
                        'consequences': fields.get('consecuencias', ''),
                        'cost': fields.get('costo', 'NOT_AVAILABLE'),
                        'support': fields.get('soporte', 'NOT_AVAILABLE'),
                        'security': fields.get('seguridad', 'NOT_AVAILABLE'),
                        'relative_path': standalone_path,
                        'source_section_sha256': _sha(match.group(0)+'\n'+block),
                        'disposition': 'INCLUDED_IN_ARCHITECTURE_DRAFT'})

    na_claim = bool(re.search(r'(?i)(?:no (?:hay|existen|aplican) decisiones (?:materiales|adr)|adrs?\s*[:=]\s*(?:n/?a|not_applicable))', adr_text))
    if not records and not na_claim:
        issue('TECH_ADR_MATERIALITY_UNRESOLVED', 'REVIEW_REQUIRED',
              'No hay ADR estructurada ni motivo explícito de NOT_APPLICABLE; el Owner debe valorar materialidad.')
    if na_claim and not records and len(adr_text) < 35:
        issue('TECH_ADR_NA_RATIONALE', 'REVIEW_REQUIRED', 'Justificar por qué no hay decisiones tecnológicas materiales.')

    # Source refs are provenance, not a source of approval.  Never confuse a
    # well-formed 64-character hash with a verified FROZEN approval receipt.
    refs = source_refs if isinstance(source_refs, list) else []
    valid_refs = [dict(r) for r in refs if isinstance(r, dict) and
                  r.get('stage') in ('product-vision','scope','requirements') and
                  _SHA.fullmatch(str(r.get('sha256') or ''))]
    if {r['stage'] for r in valid_refs} != {'product-vision','scope','requirements'}:
        issue('TECH_UPSTREAM_PROVENANCE', 'REVIEW_REQUIRED', 'Falta trazabilidad SHA a Vision/Scope/Requirements FROZEN.')
    approval_confirmed = (lifecycle == 'FROZEN' and bool(architecture_approval_id)
                          and source_sha256_verified and bool(frozen_sha256)
                          and _SHA.fullmatch(frozen_sha256) is not None)
    if approval_confirmed:
        for record in records:
            record['disposition'] = 'APPROVED_WITH_ARCHITECTURE'
    else:
        issue('TECH_OWNER_DECISION_PENDING', 'REVIEW_REQUIRED',
              'Tecnología y ADRs permanecen propuestas; su decisión se incluye en el approval normal de Architecture.')
    severity = 'BLOCK' if any(c['severity'] == 'BLOCK' for c in checks) else 'REVIEW_REQUIRED'
    return {'schema_id': PROFILE_VERSION, 'status': severity,
            'semantic_quality_certified': False, 'read_only': True,
            'source_mutations_performed': False, 'dependency_installation_performed': False,
            'separate_technology_approval_required': False,
            'candidate_content_sha256': _sha(text),
            'upstream_refs': valid_refs,
            'technology_excerpt': technology[:2200],
            'material_adr_count': len(records), 'material_adr_applicability':
            ('MATERIAL' if records else 'NOT_APPLICABLE_REPORTED' if na_claim else 'REVIEW_REQUIRED'),
            'adrs': records, 'findings': checks,
            'approval_lineage': {'state': 'APPROVED_WITH_ARCHITECTURE' if approval_confirmed else 'NOT_APPROVED',
                                 'architecture_approval_id': architecture_approval_id if approval_confirmed else None,
                                 'architecture_sha256': frozen_sha256 if approval_confirmed else None}}
