"""Deterministic, provenance-preserving evidence selection for local authoring.

Source documents are never rewritten or silently treated as fully read by the
LLM.  This *prompt-only* projection reports exactly what was omitted, binds
every source to its full SHA, and retains business/technical decision signals.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any


PROFILE = 'r03_04.evidence_selection.v1'
# Ollama's P6 adapter permits bounded num_predict <= 768; it cannot
# request a larger num_ctx through this contract. Keep prompts compact enough
# for the usual local context window and expose omissions instead of hiding
# them behind an arbitrarily larger context request.
TECH_PROMPT_LIMIT = 13000
ADR_PROMPT_LIMIT = 12500

_CRITICAL = re.compile(
    r'(?i)(?:\bRF[-_ ]?\d+\b|\bRNF[-_ ]?\d+\b|\bADR[-_ ]?\d+\b|'
    r'aprobaci[oó]n|autorizaci[oó]n|sin\s+(?:permiso|aprobar)|humano|owner|'
    r'inventario|stock|ventas|transacci[oó]n|consisten|seguridad|privacidad|'
    r'exclu(?:siones|ido)|fuera de alcance|obligatori[oa]|restricci[oó]n|'
    r'disponibilidad|continuidad|respaldo|sincronizaci[oó]n|agentes?|'
    r'interfaz|m[oó]vil|offline|local.first|datos?|almacenamiento|persistencia)',
)
_TECHNICAL = re.compile(
    r'(?i)(?:arquitectura|componente|integraci[oó]n|API|interfaz|costo|licencia|'
    r'soporte|operaci[oó]n|despliegue|riesgo|mitigaci[oó]n|tecnolog[ií]a|'
    r'alternativa|opci[oó]n\s+T[1-3]|decisi[oó]n|objetivo|MVP|\bNFR\b|'
    r'stack|servidor|servicio|base de datos|PostgreSQL|SQLite|Python|licencias?)',
)
_HEAD = re.compile(r'^\s*#{1,5}\s+(.+?)\s*$')
_BREAK = re.compile(r'(?<=[.;!?])\s+|\s+\|\s+')


def _text(text: str) -> str:
    return str(text or '').replace('\r\n', '\n').replace('\r', '\n')


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _score(value: str, heading: str, selected_option: str) -> int:
    score = 0
    if _CRITICAL.search(value): score += 6
    if _TECHNICAL.search(value): score += 3
    if _CRITICAL.search(heading): score += 2
    if _TECHNICAL.search(heading): score += 1
    if re.search(r'(?i)\b(?:no|nunca|solo|debe|prohibid[oa])\b', value): score += 2
    if selected_option and re.search(r'(?i)\bOpci[oó]n\s+'+re.escape(selected_option)+r'\b', heading):
        score += 15
    return score


def _source_units(body: str, selected_option: str) -> list[tuple[int, int, str, str]]:
    units=[]
    section='Resumen inicial'
    fenced=False
    for line in body.splitlines():
        stripped=line.strip()
        if stripped.startswith('```'):
            fenced=not fenced
            continue
        if fenced or not stripped: continue
        heading=_HEAD.match(stripped)
        if heading:
            section=heading.group(1).strip()[:140]
            continue
        # Evidence excerpts are complete clauses, never raw character slices.
        # Oversized indivisible lines are omitted and counted, not truncated.
        pieces=[stripped] if len(stripped)<=650 else _BREAK.split(stripped)
        for piece in pieces:
            piece=piece.strip(' \t|')
            if not 5 <= len(piece) <= 650:continue
            units.append((_score(piece,section,selected_option),len(units),section,piece))
    return units


def excerpt(kind: str, content: str, *, budget: int, selected_option: str = '') -> tuple[str, dict[str, Any]]:
    """Return bounded source evidence and an honest, reproducible coverage receipt."""
    full=_text(content)
    body=full.strip()
    if not body:
        raise ValueError('R0304_EMPTY_GROUNDED_SOURCE:'+kind)
    # Bind the exact complete logical text, including its outer whitespace.
    # This matches the service's canonical line-ending-only SHA policy.
    digest=_digest(full)
    prefix=f'<SOURCE kind="{kind}" full_sha256="{digest}" profile="{PROFILE}">\n'
    suffix='\n</SOURCE>'
    allowance=budget-len(prefix)-len(suffix)-350
    if allowance < 350:
        raise ValueError('R0304_CONTEXT_BUDGET_INVALID')
    if len(body)<=allowance:
        return prefix+body+suffix,{'source':kind,'full_sha256':digest,'full_chars':len(full),
                                    'selected_chars':len(body),'omitted_units':0,'excerpted':False}
    units=_source_units(body,selected_option)
    if not units:
        raise ValueError('R0304_CONTEXT_UNEXTRACTABLE:'+kind)
    chosen: dict[int, tuple[str,str]]={}
    per_section=defaultdict(int)
    used=0
    # First pass selects high-signal clauses across distinct sections.
    candidates=sorted(units,key=lambda item:(-item[0],item[1]))
    for diversity_round in (True,False):
        for priority,index,heading,line in candidates:
            if index in chosen or (diversity_round and per_section[heading]>=5):continue
            rendered=f'- [{heading}] {line}'
            if used+len(rendered)+1>allowance:continue
            chosen[index]=(heading,line)
            per_section[heading]+=1
            used+=len(rendered)+1
    if not chosen or not any(_CRITICAL.search(line) or _TECHNICAL.search(line) for _,line in chosen.values()):
        raise ValueError('R0304_CONTEXT_NO_MATERIAL_EVIDENCE:'+kind)
    ordered=[f'- [{chosen[index][0]}] {chosen[index][1]}' for index in sorted(chosen)]
    omitted=len(units)-len(chosen)
    notice=(f'EXTRACTO EXPLÍCITO: fuente íntegra {len(full)} caracteres y SHA indicado; '
            f'{len(chosen)} de {len(units)} cláusulas elegibles, {omitted} no incluidas. '
            'No concluir que algo no existe porque no aparezca en el extracto; '
            'incertidumbres y contradicciones deben quedar para revisión Owner.\n')
    selection='\n'.join(ordered)
    result=prefix+notice+selection+suffix
    if len(result)>budget:
        raise ValueError('R0304_CONTEXT_EXCERPT_OVER_BUDGET:'+kind)
    return result,{'source':kind,'full_sha256':digest,'full_chars':len(full),
                   'selected_chars':len(selection),'selected_units':len(chosen),
                   'eligible_units':len(units),'omitted_units':omitted,'excerpted':True}


def technology_context(architecture: str, frozen: dict[str,str]) -> tuple[str, dict[str, Any]]:
    required={'product-vision','scope','requirements'}
    if set(frozen)!=required:
        raise ValueError('R0304_REQUIRED_FROZEN_CONTEXT_MISSING')
    budgets={'architecture':3300,'product-vision':1350,'scope':1550,'requirements':3350}
    sources=[]; receipts=[]
    for kind,body in [('architecture',architecture),*( (k,frozen[k]) for k in ('product-vision','scope','requirements'))]:
        segment,receipt=excerpt(kind,body,budget=budgets[kind])
        sources.append(segment);receipts.append(receipt)
    body='\n'.join(sources)
    if len(body)>TECH_PROMPT_LIMIT-3000:
        raise ValueError('R0304_TECH_CONTEXT_INTERNAL_LIMIT')
    return body,{'profile':PROFILE,'sources':receipts,'context_sha256':_digest(body),
                 'excerpted_source_count':sum(1 for x in receipts if x['excerpted'])}


def adr_context(architecture: str, technology: str, selected: str) -> tuple[str,dict[str,Any]]:
    if not re.fullmatch(r'T[1-3]',selected):
        raise ValueError('R0304_ADR_SELECTION_INVALID')
    parts=[];receipts=[]
    for kind,content,limit in [('architecture',architecture,4600),('technology',technology,4800)]:
        piece,receipt=excerpt(kind,content,budget=limit,selected_option=selected)
        parts.append(piece);receipts.append(receipt)
    text='\n'.join(parts)
    if len(text)>ADR_PROMPT_LIMIT-2500:
        raise ValueError('R0304_ADR_CONTEXT_INTERNAL_LIMIT')
    return text,{'profile':PROFILE,'sources':receipts,'context_sha256':_digest(text)}
