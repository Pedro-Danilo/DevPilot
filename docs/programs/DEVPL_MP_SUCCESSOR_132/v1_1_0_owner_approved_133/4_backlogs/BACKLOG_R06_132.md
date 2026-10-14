---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R06_132
title: "Backlog R6 — Release, portabilidad y operación"
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

# Backlog R6 — Release, portabilidad y operación

## Resultado y gate de ola

**Ola R6 — Release, portabilidad y operación.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R6-01 | P0 | Release plan tipado con risk review y determinismo | Candidate semántico revisable; plan de release no se ejecuta por salida LLM |
| MP131-R6-02 | P0 | Packaging reproducible, SBOM y controles secrets | Artefacto instalable con hashes y versionado; sin DB/secretos/runtime prohibidos |
| MP131-R6-03 | P0 | Arranque, health, logs, observabilidad y update/rollback | Pilot B realmente inicia/funciona; fallo de actualización y reversión ensayados |
| MP131-R6-04 | P0 | Backup/restore del producto y estado DevPilot | Pérdida/fallo controlado, restore validado y consistencia verificable |
| MP131-R6-05 | P1 | Documentación operativa para Owner Beginner/medio | Una guía coherente de ejecución, preguntas/respuestas para fallos y evidencia de operator-only |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R6-06 | P0 | Manifiestos separados de aplicación y evidencia | ZIP aplicable limpio sin secrets/venv/runtime, evidence hashes apuntan a store |
| MP132-R6-07 | P0 | Portabilidad tecnológica y arranque autónomo de app | El entregable corre sin DevPilot, dependencias/infra/runbook aprobadas |
| MP132-R6-08 | P0 | Release evolutivo y rollback desde successor | Nuevo release tras cambio aprobado, deploy y recuperación sin sobrescribir anterior |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.
