"""UX01-A: read-only quality and handoff contract for Architecture/Options/ADR.

This is a *projection* over already-owned C02 candidate/lifecycle services,
not a new generator, writer, source registry, or approval authority. UX01-B
may call it from the existing authoring boundary; UX01-C may render its DTO.
It deliberately does not certify professional semantics from keyword matches.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from .r03_03_architecture import HEADINGS as ARCHITECTURE_HEADINGS

CONTRACT = "mp132.r03_04.ux01_artifact_quality.v1"
KINDS = ("architecture", "technology_options", "adr")
SOURCE_IDS = ("product-vision", "scope", "requirements")
TECH_CRITERIA = (
    "scope_and_requirements", "team_capacity", "domain_complexity",
    "users_and_data_volume", "concurrency", "os_and_hardware",
    "offline_and_deployment", "integration_constraints", "cost_and_licences",
    "maintainability_and_support", "transactions_and_recovery",
    "backup_restore", "security_and_privacy", "observability",
    "reversibility_and_evolution", "deferred_capabilities",
)
COMPARISON_AXES = (
    ("requirements_fit", r"(?i)\b(?:RF-\d+|RNF-\d+|requisit|alcance|funcionalidad)"),
    ("accidental_complexity", r"(?i)\b(?:complejid|proceso|dependenc|infra|servicio|capa)"),
    ("maintainability", r"(?i)\b(?:mantenim|soporte|comunidad|operaci[oó]n)"),
    ("transactions_recovery", r"(?i)\b(?:transacci[oó]n|consisten|backup|copia|restaur|idempoten)"),
    ("security_privacy", r"(?i)\b(?:seguridad|privacidad|permiso|autorizaci[oó]n)"),
    ("cost_deployment", r"(?i)\b(?:costo|coste|licencia|despliegue|local)"),
    ("reversibility_triggers", r"(?i)\b(?:migraci[oó]n|reversib|crecimiento|evoluci[oó]n|disparador)"),
)
REQUIRED_SECTIONS = {
    "architecture": tuple(ARCHITECTURE_HEADINGS),
    "technology_options": ("Drivers y restricciones", "Recomendación razonada"),
    "adr": ("Contexto", "Decisión", "Alternativas", "Consecuencias",
            "Riesgos y mitigaciones", "Reversibilidad"),
}
_SECTIONS = re.compile(r"(?m)^##[ \t]+([^\n]+)[ \t]*$")
_OPTIONS = re.compile(r"(?m)^##[ \t]+Opci[oó]n[ \t]+(T[1-3])\s*[—–:-]\s*(.*)$", re.I)
_REQUIREMENT_ID = re.compile(r"(?i)\b(?:RF|RNF)-\d+\b")
_UNSAFE = re.compile(
    r"(?i)(?:\b(?:instalar|publicar|comprar|aprobar)\b.{0,60}"
    r"\b(?:autom[aá]ticamente|sin autorizaci[oó]n|sin aprobaci[oó]n)\b)"
)
_UNAPPROVED = re.compile(
    r"(?i)\b(?:publicar|comprar|cambiar precios|autorizar pagos)\b.{0,55}"
    r"\b(?:autom[aá]ticamente|sin aprobaci[oó]n|sin autorizaci[oó]n)\b"
)
_OVERBUILT = re.compile(r"(?i)\b(?:kubernetes|microservicios|serverless|"
                        r"AWS Lambda|API Gateway|cloud|nube)\b")
_PLACEHOLDER = re.compile(r"(?i)\b(?:TODO|TBD|FIXME|lorem ipsum)\b")


def _asserts_unauthorized_action(text: str, pattern: re.Pattern[str]) -> bool:
    """Only a positive unsafe instruction blocks; a prohibition is not unsafe."""
    for line in re.split(r"[\n.;]", text):
        match = pattern.search(line)
        if match and not re.search(
            r"(?i)\b(?:no|nunca|prohibid[oa]|evitar)\b.{0,35}$",
            line[:match.start()],
        ):
            return True
    return False


def logical_text(value: str) -> str:
    """Only physical newlines are normalized; never erase semantic spacing."""
    if not isinstance(value, str):
        raise ValueError("UX01_A_TEXT_REQUIRED")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def logical_sha256(value: str) -> str:
    return hashlib.sha256(logical_text(value).encode("utf-8")).hexdigest()


def _slug(title: str) -> str:
    lowered = unicodedata.normalize("NFKD", title).casefold()
    ascii_only = "".join(c for c in lowered if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")[:72] or "section"


def markdown_sections(markdown: str) -> list[dict[str, Any]]:
    """Return exact, stable H2 boundaries for a later scoped model refinement."""
    text = logical_text(markdown)
    matches = list(_SECTIONS.finditer(text))
    seen: dict[str, int] = {}
    result: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        key = _slug(heading)
        seen[key] = seen.get(key, 0) + 1
        identifier = key if seen[key] == 1 else f"{key}-{seen[key]}"
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        result.append({
            "section_id": identifier, "heading": heading,
            "start": match.start(), "body_start": match.end(), "end": end,
            "body_sha256": logical_sha256(body),
            "requirement_ids": sorted(set(x.upper() for x in _REQUIREMENT_ID.findall(body))),
            "characters": len(body.strip()),
        })
    return result


def technology_context_requirements(context: Mapping[str, Any]) -> dict[str, Any]:
    """Expose missing context explicitly; do not invent team size or data loads."""
    if not isinstance(context, Mapping):
        raise ValueError("UX01_A_CONTEXT_MAPPING_REQUIRED")
    factors: dict[str, dict[str, str]] = {}
    for key in TECH_CRITERIA:
        raw = context.get(key)
        if raw is None or not str(raw).strip():
            factors[key] = {"status": "UNKNOWN", "value": "UNKNOWN"}
        else:
            factors[key] = {"status": "GROUNDED", "value": str(raw).strip()[:500]}
    return {
        "schema_id": CONTRACT + ".technology_factors",
        "factors": factors,
        "unknown_factors": [k for k, v in factors.items() if v["status"] == "UNKNOWN"],
        "policy": {
            "default_ecosystem": "Python",
            "non_python_requires_comparative_advantage": True,
            "simplest_sufficient_solution": True,
            "no_unjustified_distributed_or_cloud_stack": True,
            "choice_made_by_owner_only": True,
        },
    }


def assess_artifact(
    kind: str,
    markdown: str,
    *,
    frozen_sources: Mapping[str, str],
    verified_source_hashes: Mapping[str, str],
    candidate_id: str,
    runtime_status: str,
    document_id: str = "UNKNOWN",
    revision_id: str = "UNKNOWN",
    author_actor: str = "UNKNOWN",
    model_id: str = "UNKNOWN",
    owner_phase: str = "before_owner",
    project_context: Mapping[str, Any] | None = None,
    selected_option_id: str | None = None,
    selected_option_sha256: str | None = None,
) -> dict[str, Any]:
    """Project existing validators into a stable, cautious multi-provider DTO.

    Verified hashes must come from the authenticated pre-code lifecycle, not
    from untrusted Markdown or local-model declarations. This function never
    mutates project state, calls a provider or marks an artifact as approved.
    """
    if kind not in KINDS or not candidate_id.strip():
        raise ValueError("UX01_A_KIND_OR_CANDIDATE_INVALID")
    if owner_phase not in ("before_owner", "after_owner"):
        raise ValueError("UX01_A_INVALID_OWNER_PHASE")
    body = logical_text(markdown)
    sections = markdown_sections(body)
    source_refs: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []

    def issue(code: str, severity: str, section: str, reason: str,
              repair: str, source: str = "") -> None:
        findings.append({
            "id": code, "severity": severity, "section_id": section,
            "source_ref": source, "why": reason, "suggested_fix": repair,
            "resolution": "OPEN", "provenance": CONTRACT,
            "evidence": "REQUIRES_SOURCE_VERIFICATION" if source else "DETERMINISTIC_TEXT_CHECK",
        })

    for source_id in SOURCE_IDS:
        original = frozen_sources.get(source_id)
        expected = verified_source_hashes.get(source_id)
        if not isinstance(original, str) or not isinstance(expected, str) or not expected:
            issue("UX01_A_FROZEN_SOURCE_ABSENT", "BLOCK", "GLOBAL",
                  f"Fuente FROZEN no verificada: {source_id}.",
                  "Revalidar los tres upstream desde runtime, con SHA vigente.", source_id)
            continue
        actual = logical_sha256(original)
        source_refs.append({"source_id": source_id, "sha256": actual,
                            "verified": "true" if expected == actual else "false"})
        if expected != actual:
            issue("UX01_A_FROZEN_SOURCE_DRIFT", "BLOCK", "GLOBAL",
                  f"SHA lógico no coincide con autoridad FROZEN: {source_id}.",
                  "Detener generación y renovar referencia desde lifecycle.", source_id)
    if not body.strip():
        issue("UX01_A_EMPTY_ARTIFACT", "REVIEW_REQUIRED", "GLOBAL",
              "El candidato está vacío.", "Generar contenido material.")
    if str(runtime_status).upper() not in ("APPROVED", "FROZEN") and re.search(
        r"(?im)^\s*(?:status|estado)\s*:\s*(?:approved|aprobado|frozen|congelado)\s*$",
        body,
    ):
        issue("UX01_A_FICTITIOUS_APPROVAL", "BLOCK", "GLOBAL",
              "El documento se declara aprobado pero el runtime no lo confirma.",
              "Conservar el estado real del lifecycle y solicitar approval formal.")
    heading_names = {s["heading"].casefold(): s for s in sections}
    for required in REQUIRED_SECTIONS[kind]:
        found = heading_names.get(required.casefold())
        if found is None:
            issue("UX01_A_MATERIAL_SECTION_MISSING", "REVIEW_REQUIRED",
                  _slug(required), f"Sección necesaria ausente: {required}.",
                  f"Completar únicamente la sección {required} con contexto trazable.")
        elif found["characters"] < 35:
            issue("UX01_A_SECTION_NOT_SUBSTANTIVE", "REVIEW_REQUIRED",
                  found["section_id"], f"Sin desarrollo material: {required}.",
                  "Explicar decisiones, ejemplos, límites y tradeoffs concretos.")
    if _PLACEHOLDER.search(body):
        issue("UX01_A_PLACEHOLDER", "REVIEW_REQUIRED", "GLOBAL",
              "Queda un marcador sin resolver.", "Precisar la brecha o declararla UNKNOWN.")
    if _asserts_unauthorized_action(body, _UNSAFE):
        issue("UX01_A_UNAUTHORIZED_MUTATION", "BLOCK", "GLOBAL",
              "El texto indica instalación/publicación/compra/aprobación no autorizada.",
              "Retirar automatización y someter la decisión al Owner.")
    if _asserts_unauthorized_action(body, _UNAPPROVED) and any(
        re.search(r"(?i)aprobaci[oó]n humana|autorizaci[oó]n (?:del )?owner",
                  str(value)) for value in frozen_sources.values()
    ):
        issue("UX01_A_HUMAN_AUTHORITY_CONFLICT", "BLOCK", "GLOBAL",
              "Contradicción explícita con acciones sensibles gobernadas.",
              "Conservar la obligación de autorización humana.", "requirements")

    if kind == "technology_options":
        option_matches = list(_OPTIONS.finditer(body))
        ids = [row.group(1).upper() for row in option_matches]
        comparison_rows: list[dict[str, Any]] = []
        if not 2 <= len(ids) <= 3 or len(ids) != len(set(ids)):
            issue("UX01_A_OPTIONS_NOT_COMPARABLE", "REVIEW_REQUIRED", "GLOBAL",
                  "Se necesitan 2–3 alternativas con IDs distintos.",
                  "Describir al menos dos soluciones verdaderamente diferentes.")
        stack_signatures: set[str] = set()
        for index, row in enumerate(option_matches):
            section = next(
                (s["section_id"] for s in sections if s["heading"].casefold().startswith(
                    f"opción {row.group(1)}".casefold())),
                _slug(f"Opción {row.group(1)}"),
            )
            chunk = body[row.end():option_matches[index+1].start()
                         if index+1 < len(option_matches) else len(body)]
            match = re.search(r"(?im)^\s*[-*]\s*\*\*Stack:\*\*\s*(.+)$", chunk)
            signature = re.sub(r"\s+", " ", match.group(1).strip().casefold()) if match else ""
            if not signature:
                issue("UX01_A_TECH_STACK_UNSPECIFIED", "REVIEW_REQUIRED", section,
                      "No se identifica stack concreto.",
                      "Identificar backend, almacenamiento y UI/operación.")
            elif signature in stack_signatures:
                issue("UX01_A_TECH_DUPLICATE_STACK", "REVIEW_REQUIRED", section,
                      "Otra alternativa repite el mismo stack sin diferencia comprobable.",
                      "Contrastar una opción materialmente diferente.")
            stack_signatures.add(signature)
            axes = {}
            for axis, pattern in COMPARISON_AXES:
                evidence = re.search(pattern, chunk)
                axes[axis] = {
                    "status": "TEXT_PRESENT_UNVERIFIED" if evidence else "UNKNOWN",
                    "evidence_excerpt": (chunk[max(0, evidence.start()-40):evidence.end()+70].strip()[:140]
                                         if evidence else "UNKNOWN"),
                }
            comparison_rows.append({"option_id": row.group(1).upper(),
                                    "section_id": section, "stack": signature or "UNKNOWN",
                                    "axes": axes})
            if re.search(r"(?i)\b(?:java|node(?:\.js)?|typescript|golang|go\s+lang|c#|dotnet)\b",
                         signature) and not re.search(
                r"(?i)python.{0,140}(?:ventaja|beneficio|superior|compar)|"
                r"(?:ventaja|beneficio|superior|compar).{0,140}python", chunk
            ):
                issue("UX01_A_NONPYTHON_ADVANTAGE_UNVERIFIED", "REVIEW_REQUIRED", section,
                      "Stack no-Python sin comparación favorable sustentada frente a Python.",
                      "Explicar ventaja neta y costo de adopción con restricciones del proyecto.")
            if _OVERBUILT.search(signature) and not re.search(
                r"(?i)requisito material|necesidad comprobada|RF-\d+|RNF-\d+", chunk
            ):
                issue("UX01_A_OVERENGINEERING_RISK", "REVIEW_REQUIRED", section,
                      "Stack distribuido/cloud sin necesidad rastreable en la opción.",
                      "Vincular a fuente o reemplazar por una alternativa más simple.")
        if "python" not in body.casefold():
            issue("UX01_A_PYTHON_COMPARISON_MISSING", "REVIEW_REQUIRED", "GLOBAL",
                  "No consta alternativa Python ni justificación comparativa.",
                  "Evaluar Python viable o documentar una ventaja verificable no-Python.")
        if not re.search(r"(?i)complejidad|mantenimiento|operaci[oó]n", body):
            issue("UX01_A_PROPORTIONALITY_MISSING", "REVIEW_REQUIRED", "GLOBAL",
                  "No se explicita costo de complejidad y operación.",
                  "Comparar trabajo de mantenimiento para el equipo real.")
        for row in comparison_rows:
            if sum(v["status"] == "UNKNOWN" for v in row["axes"].values()) >= 4:
                issue("UX01_A_TECH_MATRIX_GAPS", "REVIEW_REQUIRED", row["section_id"],
                      "Faltan dimensiones materiales para comparar esta opción.",
                      "Añadir restricciones, costos y criterios compartidos con trazabilidad.")
    else:
        comparison_rows = []
    if kind == "adr" and selected_option_id:
        if not re.fullmatch(r"T[1-3]", selected_option_id):
            raise ValueError("UX01_A_SELECTED_OPTION_INVALID")
        decision = next((s for s in sections if s["heading"].casefold() == "decisión"), None)
        decision_body = (body[decision["body_start"]:decision["end"]]
                         if decision else "")
        stated = set(x.upper() for x in re.findall(r"\bT[1-3]\b", decision_body, re.I))
        if stated and selected_option_id not in stated:
            issue("UX01_A_SELECTED_OPTION_CONFLICT", "BLOCK", "decision",
                  "ADR contradice la opción elegida por Owner.",
                  "Conciliar el ID elegido exacto antes de approval.")
        elif selected_option_id not in stated:
            issue("UX01_A_ADR_SELECTION_UNTRACED", "REVIEW_REQUIRED", "decision",
                  "Decisión no identifica la opción elegida.",
                  "Vincular explícitamente el ID/hash Owner.")
    if kind == "adr" and not re.search(
        r"(?i)desventaja|consecuencia negativa|limitaci[oó]n|trade.off|costo de", body
    ):
        issue("UX01_A_ADR_NEGATIVE_TRADEOFF_MISSING", "REVIEW_REQUIRED",
              "consecuencias", "No se exponen costos/consecuencias adversas.",
              "Describir efectos negativos y mitigaciones de la decisión.")

    blocked = any(x["severity"] == "BLOCK" for x in findings)
    review = any(x["severity"] == "REVIEW_REQUIRED" for x in findings)
    structural = "BLOCK" if blocked else ("REVIEW_REQUIRED" if review else "STRUCTURALLY_VALID")
    return {
        "schema_id": CONTRACT, "profile_id": kind, "candidate_id": candidate_id,
        "document_id": document_id, "revision_id": revision_id,
        "provenance": {"author_actor": author_actor, "model_id": model_id,
                       "validation_engine": CONTRACT},
        "owner_phase": owner_phase, "candidate_sha256": logical_sha256(body),
        "runtime_status": str(runtime_status),
        "sources": source_refs, "sections": sections, "findings": findings,
        "requirement_trace": {s["section_id"]: s["requirement_ids"] for s in sections},
        "assumptions_and_unknowns": [
            {"section_id": s["section_id"], "marker": m.group(0).upper(),
             "verification": "OPEN"}
            for s in sections for m in re.finditer(r"(?i)\b(?:UNKNOWN|ASSUMPTION|VERIFY)\b",
                                                  body[s["body_start"]:s["end"]])
        ],
        "selected_owner_decision": {"option_id": selected_option_id or "UNKNOWN",
                                    "sha256": selected_option_sha256 or "UNKNOWN",
                                    "immutable": True},
        "technology_comparison": comparison_rows,
        "structural_disposition": structural,
        "quality_level": "REVIEW_REQUIRED" if not blocked else "BLOCK",
        "handoff_ready": False, "professional_reviewed": False,
        "technical_context": (technology_context_requirements(project_context or {})
                              if kind == "technology_options" else None),
        "owner_review_required": True,
        "external_api_used": False, "source_mutations_performed": False,
    }


def handoff_packet(assessment: Mapping[str, Any], markdown: str,
                   *, locked_section_ids: tuple[str, ...] = ()) -> dict[str, Any]:
    """Machine-readable, section-focused handoff; no automatic approval."""
    body = logical_text(markdown)
    if assessment.get("schema_id") != CONTRACT or (
        logical_sha256(body) != assessment.get("candidate_sha256")
    ):
        raise ValueError("UX01_A_HANDOFF_SOURCE_DRIFT")
    sections = assessment["sections"]
    known = {x["section_id"] for x in sections}
    if not set(locked_section_ids).issubset(known):
        raise ValueError("UX01_A_LOCKED_SECTION_UNKNOWN")
    tasks = [
        {"finding_id": f["id"], "section_id": f["section_id"],
         "severity": f["severity"], "instruction": f["suggested_fix"],
         "source_ref": f["source_ref"],
         "acceptance": "La brecha específica queda resuelta sin modificar decisiones Owner ni otras secciones."}
        for f in assessment["findings"] if f["severity"] == "REVIEW_REQUIRED"
    ]
    blockers = [f for f in assessment["findings"] if f["severity"] == "BLOCK"]
    return {
        "schema_id": CONTRACT + ".handoff", "candidate_id": assessment["candidate_id"],
        "document_id": assessment["document_id"],
        "revision_id": assessment["revision_id"],
        "runtime_status": assessment["runtime_status"],
        "provenance": assessment["provenance"],
        "quality_snapshot_phase": assessment["owner_phase"],
        "candidate_sha256": assessment["candidate_sha256"], "markdown": body,
        "sources": assessment["sources"], "section_map": sections,
        "requirements_by_section": assessment["requirement_trace"],
        "unknowns": assessment["assumptions_and_unknowns"],
        "owner_decision": assessment["selected_owner_decision"],
        "comparative_technology_axes": assessment["technology_comparison"],
        "locked_section_ids": list(locked_section_ids),
        "findings": assessment["findings"], "section_tasks": tasks,
        "blocking_issues": blockers,
        "eligible_for_external_handoff": not blockers,
        "owner_questions": [f["why"] for f in assessment["findings"]
                            if f["source_ref"] or "UNKNOWN" in f["why"]],
        "acceptance_criteria": [
            "No drift de fuentes FROZEN/decisiones Owner verificadas",
            "Solo se cambia la sección autorizada; demás hashes/IDs permanecen idénticos",
            "El Owner revisa diffs y decide un nuevo estado mediante el lifecycle",
        ],
        "provider_transfer_boundary": "OFFLINE_ONLY; no ejecución ni permiso API delegado",
        "quality_level": assessment["quality_level"],
        "requires_authenticated_owner_review": True,
        "external_api_used": False, "project_source_mutations": 0,
    }


def scoped_section_refinement(packet: Mapping[str, Any], *,
                              section_id: str, replacement: str) -> str:
    """Propose only an H2 body replacement; never write or approve source."""
    body = logical_text(packet.get("markdown", ""))
    if logical_sha256(body) != packet.get("candidate_sha256"):
        raise ValueError("UX01_A_HANDOFF_SOURCE_DRIFT")
    if packet.get("blocking_issues"):
        raise ValueError("UX01_A_HANDOFF_BLOCKING_ISSUES")
    sections = markdown_sections(body)
    matches = [x for x in sections if x["section_id"] == section_id]
    if len(matches) != 1 or section_id in packet.get("locked_section_ids", []):
        raise ValueError("UX01_A_REFINEMENT_TARGET_DENY")
    new_content = logical_text(replacement)
    if (not new_content.strip() or _SECTIONS.search(new_content)
            or _PLACEHOLDER.search(new_content)
            or _asserts_unauthorized_action(new_content, _UNSAFE)):
        raise ValueError("UX01_A_REFINEMENT_CONTENT_INVALID")
    chosen = matches[0]
    old_content = body[chosen["body_start"]:chosen["end"]]
    amended = "\n" + new_content.strip() + "\n"
    if amended == old_content:
        raise ValueError("UX01_A_REFINEMENT_NO_CHANGE")
    return body[:chosen["body_start"]] + amended + body[chosen["end"]:]
