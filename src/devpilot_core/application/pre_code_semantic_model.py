from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

SCHEMA_ID = "devpilot.gsdlc13c01.pre_code_semantic_model.v1"
GENERATOR_ID = "deterministic-semantic-model-template-v3"
_ALLOWED_KINDS = {"ACTOR", "OUTCOME", "CAPABILITY", "CONSTRAINT", "CONTEXT", "OPEN_QUESTION"}
_ALLOWED_CONFIDENCE = {"EXPLICIT", "DERIVED_SAFE", "AMBIGUOUS"}
_ALLOWED_STATUS = {"CANDIDATE", "CONFIRMED", "REJECTED", "OPEN"}
_STAGE_ORDER = {"product-vision": 1, "scope": 2, "requirements": 3}
_VAGUE_VERBS = {"administrar", "gestionar", "controlar", "manejar"}
_ACTION_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:ar|er|ir)\b", re.IGNORECASE)
_ENGLISH_ACTION_RE = re.compile(
    r"^(?:create|read|update|delete|manage|register|record|consult|query|identify|track|calculate|show|list|notify|export|import|approve|reject)\b",
    re.IGNORECASE,
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def semantic_hash(model: dict[str, Any]) -> str:
    governed = {
        "schema_id": model.get("schema_id"),
        "workspace_id": model.get("workspace_id"),
        "source_refs": model.get("source_refs") or [],
        "business_context": model.get("business_context") or "",
        "actors": model.get("actors") or [],
        "outcomes": model.get("outcomes") or [],
        "capabilities": model.get("capabilities") or [],
        "constraints": model.get("constraints") or [],
        "open_questions": model.get("open_questions") or [],
        "decisions": model.get("decisions") or {},
        "owner_semantic_reviewed": bool(model.get("owner_semantic_reviewed")),
    }
    return hashlib.sha256(canonical_json(governed).encode("utf-8")).hexdigest()


def _compact(text: str) -> str:
    return " ".join(str(text or "").split()).strip(" .")


def _item(
    *,
    item_id: str,
    kind: str,
    statement: str,
    source_excerpt: str,
    source_ref: str,
    confidence: str,
    status: str = "CANDIDATE",
    related_item_ids: list[str] | None = None,
    critical: bool = False,
    decision: str = "",
    required_stage: str | None = None,
) -> dict[str, Any]:
    row = {
        "id": item_id,
        "kind": kind,
        "statement": _compact(statement),
        "source_excerpt": _compact(source_excerpt),
        "source_ref": source_ref,
        "confidence_class": confidence,
        "owner_confirmed": status == "CONFIRMED",
        "status": status,
        "related_item_ids": list(related_item_ids or []),
        "critical": bool(critical),
        "decision": _compact(decision),
    }
    if required_stage:
        row["required_stage"] = required_stage
    return row


def _split_actions(text: str) -> list[str]:
    value = _compact(text)
    value = re.sub(r"\b(?:así\s+como|además\s+de)\b", ",", value, flags=re.IGNORECASE)
    raw_parts = [p.strip(" ,.;") for p in value.split(",") if p.strip(" ,.;")]
    parts: list[str] = []
    for raw in raw_parts:
        pieces = re.split(r"\s+(?:y|e)\s+(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:ar|er|ir)\b)", raw, flags=re.IGNORECASE)
        parts.extend(_compact(p) for p in pieces if _compact(p))
    return parts


def _capability_question(statement: str, cap_id: str, question_id: str) -> dict[str, Any] | None:
    low = statement.lower()
    if re.match(r"^(administrar|gestionar|controlar|manejar)\b", low):
        return _item(
            item_id=question_id,
            kind="OPEN_QUESTION",
            statement=f"¿Qué operaciones observables incluye «{statement}»?",
            source_excerpt=statement,
            source_ref="derived-semantic-question",
            confidence="AMBIGUOUS",
            status="OPEN",
            related_item_ids=[cap_id],
            critical=True,
            required_stage="requirements",
        )
    if "información básica" in low or "informacion basica" in low:
        return _item(
            item_id=question_id,
            kind="OPEN_QUESTION",
            statement="¿Qué información de ventas debe estar disponible en la consulta del MVP?",
            source_excerpt=statement,
            source_ref="derived-semantic-question",
            confidence="AMBIGUOUS",
            status="OPEN",
            related_item_ids=[cap_id],
            critical=True,
            required_stage="requirements",
        )
    if "bajo nivel de stock" in low or "stock bajo" in low or "bajo stock" in low:
        return _item(
            item_id=question_id,
            kind="OPEN_QUESTION",
            statement="¿Cuál es el criterio gobernado para determinar que un producto tiene stock bajo?",
            source_excerpt=statement,
            source_ref="derived-semantic-question",
            confidence="AMBIGUOUS",
            status="OPEN",
            related_item_ids=[cap_id],
            critical=True,
            required_stage="requirements",
        )
    return None


def build_candidate_model(
    *,
    workspace_id: str,
    business_need: str,
    source_ref: str,
    source_sha256: str,
    constraints: dict[str, Any],
    model_policy: dict[str, Any],
) -> dict[str, Any]:
    need = _compact(business_need)
    actors: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    capabilities: list[dict[str, Any]] = []
    open_questions: list[dict[str, Any]] = []

    if re.search(r"empresa\s+unipersonal", need, flags=re.IGNORECASE):
        actors.append(
            _item(
                item_id="ACT-001",
                kind="ACTOR",
                statement="Persona propietaria y operadora de la empresa unipersonal",
                source_excerpt="empresa unipersonal",
                source_ref=source_ref,
                confidence="DERIVED_SAFE",
            )
        )
    else:
        open_questions.append(
            _item(
                item_id="Q-001",
                kind="OPEN_QUESTION",
                statement="¿Quién es el actor o usuario principal del producto?",
                source_excerpt=need,
                source_ref=source_ref,
                confidence="AMBIGUOUS",
                status="OPEN",
                critical=True,
                required_stage="product-vision",
            )
        )

    outcome_match = re.search(
        r"\bpara\s+((?:facilitar|mantener|mejorar|reducir|aumentar|garantizar|asegurar)\b.+)$",
        need,
        flags=re.IGNORECASE,
    )
    capability_source = need
    if outcome_match:
        outcome_text = _compact(outcome_match.group(1))
        if outcome_text:
            outcomes.append(
                _item(
                    item_id="OUT-001",
                    kind="OUTCOME",
                    statement=outcome_text[0].upper() + outcome_text[1:],
                    source_excerpt=outcome_match.group(0),
                    source_ref=source_ref,
                    confidence="EXPLICIT",
                )
            )
            capability_source = need[: outcome_match.start()].rstrip(" ,.;")
    else:
        open_questions.append(
            _item(
                item_id=f"Q-{len(open_questions)+1:03d}",
                kind="OPEN_QUESTION",
                statement="¿Qué resultado de negocio observable espera obtener el Owner con el MVP?",
                source_excerpt=need,
                source_ref=source_ref,
                confidence="AMBIGUOUS",
                status="OPEN",
                critical=True,
                required_stage="product-vision",
            )
        )

    start = re.search(r"\b(?:que\s+le\s+permita|que\s+permita|permita|para\s+poder)\s+(.+)$", capability_source, flags=re.IGNORECASE)
    action_text = start.group(1) if start else ""
    actions = _split_actions(action_text) if action_text else []
    if not actions:
        for sentence in re.split(r"[.;]", capability_source):
            sentence = _compact(sentence)
            if _ACTION_RE.match(sentence) or _ENGLISH_ACTION_RE.match(sentence):
                actions.extend(_split_actions(sentence))

    for index, action in enumerate(actions[:16], start=1):
        if len(action) < 8:
            continue
        cap_id = f"CAP-{index:03d}"
        probe = _capability_question(action, cap_id, "Q-000")
        confidence = "AMBIGUOUS" if probe else "EXPLICIT"
        capabilities.append(
            _item(
                item_id=cap_id,
                kind="CAPABILITY",
                statement=action,
                source_excerpt=action,
                source_ref=source_ref,
                confidence=confidence,
            )
        )
        question = _capability_question(action, cap_id, f"Q-{len(open_questions)+1:03d}")
        if question:
            capabilities[-1]["related_item_ids"].append(question["id"])
            open_questions.append(question)

    if not capabilities:
        open_questions.append(
            _item(
                item_id=f"Q-{len(open_questions)+1:03d}",
                kind="OPEN_QUESTION",
                statement="¿Qué capacidades concretas debe ofrecer el MVP?",
                source_excerpt=need,
                source_ref=source_ref,
                confidence="AMBIGUOUS",
                status="OPEN",
                critical=True,
                required_stage="product-vision",
            )
        )

    constraints_rows = [
        _item(
            item_id="CON-001",
            kind="CONSTRAINT",
            statement=f"Local-first: {'sí' if bool(constraints.get('local_first', True)) else 'no'}",
            source_excerpt="project_constraints.local_first",
            source_ref=source_ref,
            confidence="EXPLICIT",
            status="CONFIRMED",
        ),
        _item(
            item_id="CON-002",
            kind="CONSTRAINT",
            statement=f"Cloud obligatorio: {'sí' if bool(constraints.get('cloud_required', False)) else 'no'}",
            source_excerpt="project_constraints.cloud_required",
            source_ref=source_ref,
            confidence="EXPLICIT",
            status="CONFIRMED",
        ),
        _item(
            item_id="CON-003",
            kind="CONSTRAINT",
            statement=f"Baseline de modelos: {str(model_policy.get('baseline') or 'mock-no-api')}",
            source_excerpt="model_policy.baseline",
            source_ref=source_ref,
            confidence="EXPLICIT",
            status="CONFIRMED",
        ),
    ]

    model = {
        "schema_id": SCHEMA_ID,
        "generator": GENERATOR_ID,
        "workspace_id": workspace_id,
        "source_refs": [{"path": source_ref, "sha256": source_sha256, "kind": "project-context"}],
        "business_context": need,
        "actors": actors,
        "outcomes": outcomes,
        "capabilities": capabilities,
        "constraints": constraints_rows,
        "open_questions": open_questions,
        "decisions": {},
        "owner_semantic_reviewed": False,
        "quality_state": "REVIEW_REQUIRED",
    }
    model["semantic_model_sha256"] = semantic_hash(model)
    return model


def prepare_draft_first_model(candidate: dict[str, Any]) -> dict[str, Any]:
    """Prepare a conservative internal model without forcing micro-confirmation.

    Candidate semantic items remain distinguishable from explicit Owner decisions,
    while the model becomes usable for draft rendering. Open questions keep their
    required_stage and are surfaced only when that stage actually needs them.
    """
    model = deepcopy(candidate)
    model["quality_state"] = "DRAFT_READY"
    model["owner_semantic_reviewed"] = bool(model.get("owner_semantic_reviewed"))
    model["semantic_model_sha256"] = semantic_hash(model)
    return model


def _all_items(model: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("actors", "outcomes", "capabilities", "constraints", "open_questions"):
        for item in model.get(key) or []:
            if isinstance(item, dict):
                rows.append(item)
    return rows


def _active(model: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [x for x in model.get(key) or [] if isinstance(x, dict) and str(x.get("status") or "") != "REJECTED"]


def _question_required_by_stage(question: dict[str, Any], stage_id: str) -> bool:
    required = str(question.get("required_stage") or "requirements")
    return _STAGE_ORDER.get(required, 3) <= _STAGE_ORDER.get(stage_id, 3)


def unresolved_decisions_for_stage(model: dict[str, Any], stage_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for question in _active(model, "open_questions"):
        if not bool(question.get("critical")) or not _question_required_by_stage(question, stage_id):
            continue
        if str(question.get("status") or "") == "CONFIRMED" and _compact(question.get("decision") or ""):
            continue
        rows.append(question)
    return rows


def normalize_owner_model(candidate: dict[str, Any], submitted: dict[str, Any]) -> dict[str, Any]:
    base = deepcopy(candidate)
    original_by_id = {str(x.get("id")): x for x in _all_items(candidate)}
    normalized: dict[str, list[dict[str, Any]]] = {k: [] for k in ("actors", "outcomes", "capabilities", "constraints", "open_questions")}
    next_numbers = {"ACTOR": 1, "OUTCOME": 1, "CAPABILITY": 1, "CONSTRAINT": 1, "OPEN_QUESTION": 1}
    prefixes = {"ACTOR": "ACT", "OUTCOME": "OUT", "CAPABILITY": "CAP", "CONSTRAINT": "CON", "OPEN_QUESTION": "Q"}
    for existing in original_by_id.values():
        kind = str(existing.get("kind") or "")
        m = re.search(r"(\d+)$", str(existing.get("id") or ""))
        if kind in next_numbers and m:
            next_numbers[kind] = max(next_numbers[kind], int(m.group(1)) + 1)

    incoming: list[dict[str, Any]] = []
    for key in normalized:
        for item in submitted.get(key) or []:
            if isinstance(item, dict):
                incoming.append(item)
    if not incoming:
        raise ValueError("semantic model submission contains no items")

    for raw in incoming:
        kind = str(raw.get("kind") or "").upper()
        if kind not in _ALLOWED_KINDS:
            raise ValueError(f"invalid semantic kind: {kind}")
        raw_id = str(raw.get("id") or "").strip()
        statement = _compact(raw.get("statement") or "")
        decision = _compact(raw.get("decision") or "")
        # UX hardening: an optional, newly-added but untouched row is not part of
        # the governed submission. Existing items may never be erased silently.
        if not raw_id and not statement and not decision:
            continue
        original = original_by_id.get(raw_id)
        item_id = raw_id
        if not original:
            item_id = f"{prefixes[kind]}-{next_numbers[kind]:03d}"
            next_numbers[kind] += 1
        if not statement:
            raise ValueError(f"empty semantic statement: {item_id}")
        status = str(raw.get("status") or (original or {}).get("status") or "CANDIDATE").upper()
        if decision and kind == "OPEN_QUESTION":
            status = "CONFIRMED"
        if status not in _ALLOWED_STATUS:
            raise ValueError(f"invalid semantic status: {status}")
        confidence = str((original or raw).get("confidence_class") or "AMBIGUOUS").upper()
        if confidence not in _ALLOWED_CONFIDENCE:
            confidence = "AMBIGUOUS"
        row = _item(
            item_id=item_id,
            kind=kind,
            statement=statement,
            source_excerpt=str((original or raw).get("source_excerpt") or "Owner semantic review"),
            source_ref=str((original or raw).get("source_ref") or "owner-semantic-review"),
            confidence=confidence,
            status=status,
            related_item_ids=list(raw.get("related_item_ids") or (original or {}).get("related_item_ids") or []),
            critical=bool(raw.get("critical", (original or {}).get("critical", False))),
            decision=decision,
            required_stage=str(raw.get("required_stage") or (original or {}).get("required_stage") or "") or None,
        )
        row["owner_confirmed"] = status == "CONFIRMED"
        normalized[{"ACTOR": "actors", "OUTCOME": "outcomes", "CAPABILITY": "capabilities", "CONSTRAINT": "constraints", "OPEN_QUESTION": "open_questions"}[kind]].append(row)

    base.update(normalized)
    base["decisions"] = {str(q["id"]): q.get("decision", "") for q in normalized["open_questions"] if q.get("decision")}
    base["owner_semantic_reviewed"] = True
    base["quality_state"] = "CONFIRMED" if not unresolved_decisions_for_stage(base, "requirements") else "DRAFT_READY"
    base["semantic_model_sha256"] = semantic_hash(base)
    return base


def capability_actionable(statement: str, *, allow_vague: bool = False) -> bool:
    text = _compact(statement)
    if len(text) < 12:
        return False
    low = text.lower()
    first = low.split()[0] if low.split() else ""
    if first in _VAGUE_VERBS and not allow_vague and not re.search(
        r"[,;]|\b(?:crear|consultar|actualizar|registrar|identificar|listar|calcular|mostrar|notificar|exportar|importar)\b",
        low,
    ):
        return False
    return bool(_ACTION_RE.match(text) or _ENGLISH_ACTION_RE.match(text))


def _resolved_related_decisions(model: dict[str, Any], capability: dict[str, Any]) -> list[str]:
    question_by_id = {str(x.get("id")): x for x in _active(model, "open_questions")}
    decisions: list[str] = []
    for qid in capability.get("related_item_ids") or []:
        question = question_by_id.get(str(qid))
        if not question:
            continue
        decision = _compact(question.get("decision") or "")
        if str(question.get("status") or "") == "CONFIRMED" and decision:
            decisions.append(decision)
    return decisions


def validate_model_for_stage(model: dict[str, Any], stage_id: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if model.get("schema_id") != SCHEMA_ID:
        findings.append({"id": "SEMANTIC_MODEL_SCHEMA_BLOCK", "message": "Semantic Model schema_id is not supported."})
    actors = _active(model, "actors")
    outcomes = _active(model, "outcomes")
    caps = _active(model, "capabilities")
    if not actors:
        findings.append({"id": "SEMANTIC_MODEL_ACTOR_REQUIRED_BLOCK", "message": "At least one actor is required before this artifact can be approval-ready."})
    if not outcomes:
        findings.append({"id": "SEMANTIC_MODEL_OUTCOME_REQUIRED_BLOCK", "message": "At least one business outcome is required before this artifact can be approval-ready."})
    if not caps:
        findings.append({"id": "SEMANTIC_MODEL_CAPABILITY_REQUIRED_BLOCK", "message": "At least one product capability is required before this artifact can be approval-ready."})
    for cap in caps:
        if not capability_actionable(str(cap.get("statement") or ""), allow_vague=stage_id in {"product-vision", "scope"}):
            decisions = _resolved_related_decisions(model, cap)
            if not (stage_id == "requirements" and decisions and any(capability_actionable(x, allow_vague=False) for x in decisions)):
                findings.append({"id": "SEMANTIC_MODEL_CAPABILITY_ACTION_BLOCK", "message": f"Capability {cap.get('id')} still needs an observable definition for {stage_id}.", "item_id": cap.get("id")})
        if not str(cap.get("source_ref") or "").strip():
            findings.append({"id": "SEMANTIC_MODEL_SOURCE_EVIDENCE_BLOCK", "message": f"Capability {cap.get('id')} lacks source evidence.", "item_id": cap.get("id")})
    for question in unresolved_decisions_for_stage(model, stage_id):
        findings.append(
            {
                "id": "SEMANTIC_MODEL_CRITICAL_QUESTION_BLOCK",
                "message": f"Decision {question.get('id')} is required before {stage_id} can be approval-ready: {question.get('statement')}",
                "item_id": question.get("id"),
                "required_stage": question.get("required_stage"),
            }
        )
    return findings


def validate_confirmed_model(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Backward-compatible strict validation used by older callers/tests.

    The strict form corresponds to Requirements readiness, where all critical
    semantic decisions must be resolved.
    """
    return validate_model_for_stage(model, "requirements")


def requirement_records(model: dict[str, Any]) -> list[dict[str, Any]]:
    caps = _active(model, "capabilities")
    questions = {str(x.get("id")): x for x in _active(model, "open_questions")}
    records = []
    for index, cap in enumerate(caps, 1):
        statement = _compact(cap.get("statement") or "")
        related = [questions.get(str(qid)) for qid in cap.get("related_item_ids") or [] if questions.get(str(qid))]
        resolved = [q for q in related if q and str(q.get("status") or "") == "CONFIRMED" and _compact(q.get("decision") or "")]
        unresolved = [str(q.get("id")) for q in related if q and q not in resolved and bool(q.get("critical"))]
        low = statement.lower()
        effective_action = statement
        if low.split() and low.split()[0] in _VAGUE_VERBS:
            action_decision = next((_compact(q.get("decision") or "") for q in resolved if capability_actionable(_compact(q.get("decision") or ""), allow_vague=False)), "")
            if action_decision:
                effective_action = action_decision
        fr_statement = f"El sistema debe permitir al actor autorizado {effective_action[0].lower()+effective_action[1:] if effective_action else effective_action}."
        if low.startswith(("consultar ", "listar ", "mostrar ")):
            decision = "; ".join(_compact(q.get("decision") or "") for q in resolved)
            criterion = f"Dada información existente y accesible, al ejecutar «{statement}», el sistema devuelve la información solicitada{': '+decision if decision else ''} sin modificarla."
            method = "TEST"
        elif low.startswith(("registrar ", "crear ", "importar ")):
            criterion = f"Dados datos válidos, al ejecutar «{statement}», el resultado queda registrado y puede verificarse posteriormente."
            method = "TEST"
        elif low.startswith(("actualizar ", "modificar ")):
            criterion = f"Dado un estado inicial conocido, al ejecutar «{statement}», el estado resultante refleja la actualización solicitada."
            method = "TEST"
        elif low.startswith(("identificar ", "detectar ")):
            decision = "; ".join(_compact(q.get("decision") or "") for q in resolved)
            criterion = f"Dados datos que cumplen el criterio confirmado{': '+decision if decision else ' [PENDIENTE: resolver decisión asociada]'}, el sistema identifica los elementos correspondientes y no marca los que no lo cumplen."
            method = "TEST"
        elif unresolved:
            criterion = f"[PENDIENTE: resolver {', '.join(unresolved)} antes de approval]"
            method = "DEMONSTRATION"
        else:
            criterion = f"Mediante demostración controlada, un actor autorizado puede completar «{effective_action}» y observar el resultado definido por el alcance aprobado."
            method = "DEMONSTRATION"
        records.append(
            {
                "id": f"RF-{index:03d}",
                "type": "FR",
                "statement": fr_statement,
                "source_capability_ids": [cap.get("id")],
                "priority": "MUST",
                "acceptance_criteria": [criterion],
                "verification_method": method,
                "open_decisions": unresolved,
            }
        )
    return records


def validate_rendered_artifact(stage_id: str, content: str, model: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if stage_id in {"product-vision", "scope"}:
        for cap in _active(model, "capabilities"):
            if str(cap.get("statement") or "") not in content:
                findings.append({"id": "SEMANTIC_RENDER_CAPABILITY_TRACE_BLOCK", "message": f"Rendered {stage_id} omitted governed capability {cap.get('id')}."})
    if stage_id == "requirements":
        records = requirement_records(model)
        for rec in records:
            if rec["id"] not in content or rec["statement"] not in content or rec["verification_method"] not in content:
                findings.append({"id": "SEMANTIC_REQUIREMENT_RENDER_BLOCK", "message": f"Rendered requirements omitted governed fields for {rec['id']}."})
            if rec.get("open_decisions"):
                findings.append({"id": "SEMANTIC_REQUIREMENT_OPEN_DECISION_BLOCK", "message": f"{rec['id']} still depends on {', '.join(rec['open_decisions'])}."})
        if re.search(r"El sistema debe soportar(?: de forma verificable)?:", content, flags=re.IGNORECASE):
            findings.append({"id": "SEMANTIC_REQUIREMENT_PLACEHOLDER_BLOCK", "message": "Generic legacy requirement placeholder is forbidden."})
    return findings
