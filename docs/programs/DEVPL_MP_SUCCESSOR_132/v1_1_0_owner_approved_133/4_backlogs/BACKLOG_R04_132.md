---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R04_132
title: "Backlog R4 — MIASI contextual y planificación continua"
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

# Backlog R4 — MIASI contextual y planificación continua

## Resultado y gate de ola

**Ola R4 — MIASI contextual y planificación continua.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R4-01 | P0 | Auditoría MIASI/readiness y gobierno de estados cross-stage | Gates solo cuando aplican; no `BLOCK` prematuro ni summaries contradictorios |
| MP131-R4-02 | P1 | Candidate D/L para Roadmap/Backlog/Sprint, con decisión humana | Pruebas RF coverage, dependencias, slicing, priorización y criterios de aceptación verificables |
| MP131-R4-03 | P0 | Reconciliar `SprintPlan` FROZEN y metadata/proyección humana | Wrapper y proyección canónica coherentes, sin dual authority ni overwrite de FROZEN |
| MP131-R4-04 | P0 | Pilot B B3: Planning y stories | Roadmap/Backlog/Sprint FROZEN; backlog RF→stories trazable, story READY con DoR y tests-intent |
| MP131-R4-05 | P1 | Datasets y tests de planificación adversarial | No se aceptan estimaciones/prioridades opacas o contraindicadas sin rationale/Owner |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R4-06 | P0 | Backlog/roadmap/sprint Markdown durable y versionado | Canonical planning vinculado a docs, paridad en reinicio y Git sin outputs-only |
| MP132-R4-07 | P0 | Evolución de planificación y dependencias tras release | ChangeRequest modifica roadmap/backlog futuro con Owner approval, sin reabrir Frozen |
| MP132-R4-08 | P1 | MIASI aplicable por componente, no a todo proyecto | Agent/Tool/Eval Cards condicionales con compliance coverage y waiver restringido |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

B3: roadmap/backlog/sprint/stories y cambios de alcance se derivan, editan, aprueban, versionan y recuperan por UI. Un documento generado fuera de DevPilot no satisface acceptance.

---

## Enmienda programática post-R02-06 · 187

**Planning de software entregable:** `MP131-R4-02` migra de candidato D/L por defecto a candidato L opcionalmente alternativo y perfil profesional de roadmap/outcomes, dependencias, priorización justificada y slicing. `MP131-R4-03` conserva JSON canónico; Owner revisa Markdown con round-trip explícito y sin doble autoridad. `MP131-R4-04`/`MP132-R4-06` incorporan **Release/Increment Plan** vinculado al roadmap/backlog/sprint, con outcomes, métricas, `IN/OUT`, dependencias, acceptance scenarios, test refs y evidence; no confundir FROZEN del Sprint con incremento aceptado. `MP132-R4-07` habilita planificación continua con successor al cambiar release, sin congelar todos los sprints futuros. `MP132-R4-08` aplica MIASI a componentes agentic de Pilot B solo cuando correspondan. Aceptación M4: primer incremento y sprint realizables, prioridad/estimates con explicación y read-only markdown portable.

---

## Enmienda 188 — criterios prospectivos R04

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Owner de esta ola:** Especializar Planning: hitos, story slicing, DoR/DoD, dependencias y capacidades trazables a alcance/arquitectura; no convertir recomendaciones de calendario en bloqueos materiales ni obligar modelos E.
