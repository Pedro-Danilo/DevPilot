---
doc_id: DEVPL-MP-SUCCESSOR-132-ARTIFACT_CATALOG_AND_COVERAGE_CONTRACT_132
title: "Catálogo profesional, cobertura por etapa y pruebas"
version: "1.1.1-r00-succ"
status: "SUCCESSOR_DRAFT_FOR_OWNER_REVIEW"
baseline_commit: "66ab2e6227072c951b5bd2ac9160e8515b1b9fc0"
historical_baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
successor_execution_authority: false
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Catálogo profesional, cobertura por etapa y pruebas

## Catálogo y perfil por tipo

Clave `(artifact_type,profile_version)`. Campos `standard_refs`, `stage`, `applicability_rule`, `required_sections`, `dependencies`, `ownership`, `generation_routes`, `semantic_checks`, `schema_checks`, `evidence_checks`, `approval_required`, `publish_path_template`, `successor_policy`, `coverage_gate`. Categorías `REQUIRED`, `CONDITIONAL`, `RECOMMENDED`, `NOT_APPLICABLE`; `WAIVED` como decisión excepcional independiente.

Cobertura base por etapas: Intake/business/vision/scope; Requirements/traceability; Architecture/ADRs/domain/data/integrations/UX/security/test strategy; Planning roadmap/backlog/release/sprint/story; Source tests/build/Quality/Git; Release SBOM/installation/rollback/health; Operations/incident/evolution; MIASI Cards/evals/policies sólo donde aplique.

## Resultado del Coverage Gate

`artifact_type`, `requirement_rule`, `applicability_evidence`, `current_revision`, `lifecycle`, `structural_pass`, `semantic_review`, `dependency_freshness`, `evidence_refs`, `risk`, `result PASS|WARN|BLOCK|N/A`, `owner_action`. `REQUIRED` faltante o semántica obligatoria no acreditada → BLOCK; `RECOMMENDED` ausente → WARN; `CONDITIONAL` sin hechos suficientes → REVIEW_REQUIRED, no N/A automático.

No se decide PASS por archivo existente. Los modelos evalúan contradicciones como insumo; verificación verificable/citas, schema, tests y humano completan el gate. No crear perfiles ni templates sin necesidad real, no llenar carpetas vacías.

## Prueba representativa

Architecture con datos relacionales requiere `Data Model`; AI agent inexistente → Agent Card N/A. Requisito FROZEN alterado → dependientes stale; se muestra exactamente cuáles requieren revalidación. El gate debe expresar al usuario qué falta, por qué y cómo remediarlo sin ejecutar acciones.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Catalog/Coverage.
- **Actualización concreta:** Asociar primera vertical verificable R01-06; no crear templates vacíos ni bloqueo por catálogo universal.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.

---

## Enmienda programática post-R02-06 · 187

**Aplicación stage-aware antes de FROZEN:** Vision requiere problema, destinatarios, propuesta de valor, outcomes y criterios de éxito; Scope requiere `IN/OUT/DEFERRED`, límites, prioridades, dependencias, entregables y condiciones de aceptación; Requirements requiere RF únicos, acciones observables, actores, reglas/precondiciones/excepciones, AC verificables y trazas a Scope/decisiones. Comparar contenido semántico upstream, no solo `source_context_sha256`.

Architecture requiere drivers no funcionales, decisiones de stack justificadas, ADR materiales, Data/API/UX/Security/Test condicionales y operabilidad; Planning requiere milestones/outcomes, Release/Increment Plan, dependencias, métricas, slicing, sprint goal y story DoR/DoD. Construction/Release requieren builds/tests/SBOM/runbook/deploy/restore según PESP. Falta `REQUIRED` → BLOCK; `CONDITIONAL` desconocido → REVIEW; no deducir PASS por longitud/encabezados ni imponer perfiles no aplicables. Guardar `quality_gate_version`, motivo recuperable, hash de candidata y downstream dependencias; Quality Gate inicial en R02-07; revisión extendida R02-08.


---
## Enmienda 188 aprobada — contrato operativo por perfil (ADOPTADA — autoridad programática)

Además de los campos existentes, resolver `authoring_contract_ref`, `input_fact_schema`, `context_selection_policy`, `expected_semantic_obligations`, `cross_artifact_invariants`, `testability_checks`, `unsupported_claim_rules`, `repair_policy`, `evidence_quality_requirements`, `materiality_threshold_policy` y `owner_decision_surface`. La selección es por `artifact_type + profile_version + project facts`, nunca un identificador de Pilot B. Un hook de perfil permite reglas específicas sin crear un evaluador paralelo. Aplicabilidad MIPSoftware/MIASI sigue en el registro PESP y no implica crear archivos vacíos. El reporte distingue `BLOCK / REVIEW_REQUIRED / WARN / PASS` con fuentes y remediación; una observación cosmética no retrasa FROZEN. Probar cobertura/diferencias en un segundo dominio.

**Autoridad:** `MP132-A188`, aprobada por Owner el 2026-10-22; aplicación según `ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. No constituye ejecución R02-08 ni habilitación de E.
