---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R09_132
title: "Backlog R9 — Productización, UX y resiliencia real"
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
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Backlog R9 — Productización, UX y resiliencia real

## Resultado y gate de ola

**Ola R9 — Productización, UX y resiliencia real.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R9-01 | P1 | Launcher/instalador unificado y settings persistentes | Inicio API+UI, readiness, shutdown, log y root authorization sin variables temporales cambiantes |
| MP131-R9-02 | P0 | Fault injection real: kill API/worker, timeout HTTP y post-commit interruption | Recuperación sin doble source/Git, sin locks robados ni sesiones con authority residual |
| MP131-R9-03 | P1 | UX-P1: next-action, approval, feedback y densidad Guided/Expert | Tests browser por estado; mejoras basadas en hallazgos reales, no retoques cosméticos arbitrarios |
| MP131-R9-04 | P1 | Telemetría y performance: latencia, token/cost, bundle UI y storage | Thresholds fijados contra baseline medido; la advertencia Vite se mide, no se etiqueta build FAIL |
| MP131-R9-05 | P0 | Lifecycle uniforme `FROZEN→successor` y recuperación | Versionamiento y downstream impact sin editar artefactos FROZEN in-place |
| MP131-R9-06 | P1 | Release de DevPilot: instalación/upgrade/backup/restore propios | Distribución reproducible del producto DevPilot separada del Git del proyecto piloto |

**Rebind v1.1:** Los ítems heredados R9-01 (Settings), R9-03 (UX) y R9-05 (FROZEN) **no comienzan en R9**: su foundation se mueve a R0/R1–R6; R9 conserva consolidación, endurance y productización. Sus IDs permanecen para trazabilidad sin duplicar autoridad.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R9-07 | P0 | Fault injection proceso/browser/HTTP/Git post-commit | Crash real, locks, reentrada idempotente, sesión revocada, rollback ensayado |
| MP132-R9-08 | P1 | UX longitudinal y estado de configuración basado en criterios | Medir journey, Settings modular, performance Vite y launcher sin reabrir S2 resueltos |
| MP132-R9-09 | P1 | Refinamiento avanzado de FROZEN y release successors | R1–R6 implementan base; R9 endurance/cross-release recovery |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

El launcher/instalador DevPilot de R9 es una evolución de operación de la plataforma. Mientras no exista, se autoriza consola únicamente para levantar API/UI, auditoría y correctivos de DevPilot, no para implementar ni desplegar Pilot B.

---

## Enmienda programática post-R02-06 · 187

Productizar Guided para mantener tareas principales cerca de sus acciones: generación L, edición/revisión Markdown, mensajes PASS/BLOCK locales y recuperación tras caducidad de sesión sin perder borrador; laboratorios comparativos en Expert/Settings y **opcionales**. Proyectar progreso por objetivo/incremento/sprint/story/release; conservar historiales D/L y no mostrar estados PENDING contradictorios con aprobaciones. Reinicios/resume/crash/no-double submit y falso drift por LF/CRLF son regresiones focales de operador y producto, no motivos de adjudicaciones repetitivas.

---

## Enmienda 188 — criterios prospectivos R09

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Owner de esta ola:** Proteger UX/recuperación y discoverability de hallazgos de calidad: reportes material vs editorial, recibos y reproceso focal; evitar loops autónomos, falsos bloqueos y exceso de autorizaciones.
