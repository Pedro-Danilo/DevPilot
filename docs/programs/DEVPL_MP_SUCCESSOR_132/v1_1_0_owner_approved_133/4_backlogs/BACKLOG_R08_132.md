---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R08_132
title: "Backlog R8 — Proveedores externos y Pilot C"
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

# Backlog R8 — Proveedores externos y Pilot C

## Resultado y gate de ola

**Ola R8 — Proveedores externos y Pilot C.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R8-01 | P0 | Sucesor ADR-010 y threat model de egress/privacy | Riesgo legal/PII, consentimiento, budget, secrets-by-reference y retention definidos/Owner approved |
| MP131-R8-02 | P0 | Adaptador remoto real con network toggle explícito | Unauthorized/no budget/no credential→BLOCK antes de HTTP; egress real solo con autorización y recibo |
| MP131-R8-03 | P0 | CostGuard por token/llamada y kill switch | Cuotas, idempotency/retry bounded, redacción y gasto máximo; cancelación/circuit breaker |
| MP131-R8-04 | P1 | Paridad de candidate E vs D/L y fallback consensuado | Schema, provenance y errors; proveedor fallido no crea outputs falsamente aprobados |
| MP131-R8-05 | P0 | Pilot C separado para aceptación de seguridad externa | Endpoint controlado, datos sintéticos, fallo de red, cuota y rechazo; no contamina Pilot B |
| MP131-R8-06 | P1 | Comparativa de costo, latencia, calidad y privacidad por proveedor | Evals con condiciones/hardware/precios registrados en evidencia, sin benchmarks inventados |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R8-07 | P0 | ADR external exacta antes de habilitación | Owner define provider, data, egress, secrets refs y máximos; BLOCK antes de HTTP |
| MP132-R8-08 | P1 | Comparativa providers sin false fallback | Dataset y costo real medido; External ENABLED sólo con Pilot C PASS |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.
