---
doc_id: DEVPL-MP-SUCCESSOR-132-ARTIFACT_CATALOG_AND_COVERAGE_CONTRACT_132
title: "Catálogo profesional, cobertura por etapa y pruebas"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
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
