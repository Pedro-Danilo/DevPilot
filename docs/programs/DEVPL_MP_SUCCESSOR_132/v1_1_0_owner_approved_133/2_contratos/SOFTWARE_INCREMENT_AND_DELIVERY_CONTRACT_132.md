---
doc_id: MP132-SOFTWARE-INCREMENT-DELIVERY-187
title: "Plan de incrementos y aceptación de software entregable"
version: "1.0.0-programmatic-187"
status: "PROGRAMMATIC_AMENDMENT"
planning_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
execution_authority: false
---
# Software Increment / Release Delivery Contract (MP132)

## Propósito y autoridad

Traducir baselines de Producto y Técnica FROZEN en **entregas ejecutables medibles**, no añadir una segunda fuente de Planning. El JSON canónico de Planning y su lifecycle siguen siendo autoridad; Markdown se revisa y publica como proyección gobernada. La implementación del contrato pertenece principalmente a R4/R5/R6, no a R02-07.

## Modelo mínimo: `SoftwareIncrementPlan`

`increment_id`, `plan_revision`, `project_id`, `release_target`, `goal`, `business_outcome`, `success_metrics`, `scope_in[]`, `scope_out[]`, `deferred[]`, `requirement_refs[]`, `story_refs[]`, `dependency_refs[]`, `architecture_refs[]`, `risk_refs[]`, `integration_boundary`, `acceptance_scenarios[]`, `negative_scenarios[]`, `test_refs[]`, `quality_profile_ref`, `documentation_refs[]`, `deliverables[]`, `state`, `approval_ref`, `evidence_refs[]`, `accepted_at`, `successor_ref`. Identificadores son proyecto-scoped; referencias incluyen revision/hash y son verificables.

## Secuencia y estados

1. Product+Technical Baselines `FROZEN`, PESP vigente, TechnologyProfile aprobado y scaffold preparado.
2. Roadmap define resultados/capacidades y horizonte; Release/Increment Plan define secuencia, dependencias y criterios medibles.
3. Backlog descompone requerimientos en vertical slices; cada sprint define objetivo y selecciona stories `READY`, capacidad justificada y dependencias satisfechas.
4. Cada story aplica `DRAFT → plan/diff/approval/atomic apply → tests/Quality/Git → DONE` sin escribir el proyecto desde terminal Owner.
5. La integración del incremento ejecuta escenarios E2E positivos/negativos, vincula evidencia y registra `ACCEPTED` solo cuando se cumple el outcome.
6. Release candidate agrega incrementos aceptados y pasa build/supply chain/security/docs/deploy/restore/rollback antes de `RELEASE_READY`.
7. Feedback crea `ChangeRequest` y successor; los anteriores `FROZEN/ACCEPTED` permanecen inmutables.

**Regla:** `STORY_DONE ≠ INCREMENT_ACCEPTED ≠ RELEASE_READY`; un Sprint FROZEN no garantiza un producto listo. Se aprueba una decisión material por su gate existente, sin approvals humanos duplicados de índices o comprobaciones automáticas.

## Quality y documentación aplicables

MIPSoftware siempre; estrategia test por riesgo (unit, integration, E2E, security, performance si aplica), AC comprobables y trazabilidad. MIASI por componente agéntico real con control de tools/autonomía, no por usar LLM de autoría. `DocumentationCoverage` condiciona ADR/API/data/user/runbook/release notes/backup-restores a la arquitectura/riesgo y a cambios de cada incremento. No exigir carpetas ficticias.

## Negativos y recuperación

Dependencia no satisfecha, story sin RF, plan stale, aprobación no vinculada, QA sin tests reales, falta de build/deploy/rollback cuando aplica o evidencia divergente → BLOCK del estado correspondiente; no reabrir compromisos FROZEN ni simular métricas. Detectar LF/CRLF con contenido Git y policy, no bytes físicos de worktree vs blobs. Full Regression solo bajo excepción de riesgo explícita.

## Implementación futura

R4 es propietario de `SoftwareIncrementPlan` y sincronización con Planning; R5 de aceptación integrada de incremento; R6 de Release. La existencia de este documento **no** significa que el servicio ya opere ni autoriza implementarlo antes de su sprint.

---

## Continuidad de calidad de incrementos — A188

El contrato transversal `ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` gobierna la **calidad de autoría** de Release/Increment Plan y artefactos dependientes: propósito, outcomes, referencias FROZEN, obligaciones específicas, negativos y evidencia de testabilidad. `SoftwareIncrementPlan` sigue siendo la entidad canónica: no surge un segundo plan ni un segundo publisher. La prueba de aceptación real del incremento prevalece sobre un texto bien formateado. R04–R06 continúan como olas propietarias; A188 no autoriza su implementación anticipada.
