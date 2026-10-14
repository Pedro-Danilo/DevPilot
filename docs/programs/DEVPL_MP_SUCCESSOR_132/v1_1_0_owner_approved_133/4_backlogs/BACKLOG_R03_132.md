---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R03_132
title: "Backlog R3 — Arquitectura, riesgo y scaffold"
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

# Backlog R3 — Arquitectura, riesgo y scaffold

## Resultado y gate de ola

**Ola R3 — Arquitectura, riesgo y scaffold.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R3-01 | P0 | `TECHNICAL_RAG_SOURCE_PROFILE` y restricciones de autoridad | ContextPack prioriza ADR/RF/security vigentes; changelog histórico no se trata como decisión técnica actual |
| MP131-R3-02 | P0 | TechnicalDesignCandidate tipado D/L y quality gates cruzados | Schema+renderer; RF→Architecture→ADR→Security→Tests consistente; unsupported assertions bloquean |
| MP131-R3-03 | P0 | ADR companion gobernado y selección tecnológica | ADR standalone approval-bound, profile tecnológico con alternativas/rationale; sin decidir stack antes de Architecture |
| MP131-R3-04 | P0 | Technical Scaffold & Dependency Provisioning separado de authoring | Plan/diff/approval/execute, constraints/red/policy, locks y rollback; sin instalación manual del Owner |
| MP131-R3-05 | P0 | Pilot B B2: baseline técnico FROZEN y proyecto listo | Architecture, Security, Test Strategy, Traceability y ADRs FROZEN; scaffold reproducible y verificado |
| MP131-R3-06 | P1 | Evals de arquitectura y threat model de IA/RAG | Fixtures falsos, decisiones no grounded y payload injection rechazados; métricas registradas |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R3-07 | P0 | Catálogo condicional de datos/API/UX/domain/interfaces | Activación comprobada por proyecto; schemas, diagramas, API/test y N/A rationale |
| MP132-R3-08 | P0 | Layout/TechnicalScaffold independiente del documento | Stack decidido en Architecture, plan/diff, aprobación e imports/lockfile reproducibles |
| MP132-R3-09 | P0 | Markdown técnico publicado y reconciliado | Architecture, ADR, Security, Test y Traceability con lineage, sin source of truth duplicado |
| MP132-R3-10 | P1 | Cambios sucesores de ADR/TechnologyProfile | Nuevo ADR no instala dependencias ni reescribe diseño FROZEN |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.
