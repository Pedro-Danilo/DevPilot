---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R05_132
title: "Backlog R5 — Construcción generalizable, Quality y Git"
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

# Backlog R5 — Construcción generalizable, Quality y Git

## Resultado y gate de ola

**Ola R5 — Construcción generalizable, Quality y Git.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R5-01 | P0 | Story GenerationAdapter generalizable y rutas D/L | Candidate sobre historia nueva no RF001..003, esquema tipado, edición Owner, provenance; sin hardcoding del piloto |
| MP131-R5-02 | P0 | Plan de cambio único, preimage, atomic apply, approval | SourceChangePlan exact-path; drift bloquea; modelos/agentes no hacen writes ni editan policy |
| MP131-R5-03 | P0 | Test Impact/StoryTestPlan/jobs/Quality fundamentados | Tests reales, unknown impact tratado fail-closed, approved targets ejecutados en workspace correcto |
| MP131-R5-04 | P0 | Git tres estados, stage+commit approval y rollback controlado | Dos decisiones humanas distintas; sin `git add .`, sin force; outputs preservados; recibo Git por story |
| MP131-R5-05 | P0 | Pilot B B4: ≥1 ciclo completo de story y repetición en otra | Source funcional, tests/Quality PASS, commit(s), reacceso tras restart y una story adicional |
| MP131-R5-06 | P1 | Boundary de agente/code review read-only | Findings y recomendaciones sin ejecutar shell/Git ni aprobación encubierta |
| MP131-R5-07 | P0 | Negativos source/Git/approval | Intentos de path traversal, patch drift, duplicate apply, dirty index, approval mismatch y lock concurrente bloqueados |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R5-08 | P0 | Story arbitraria vía modelo local y bridge tipado | Nuevo dominio, no templates por RF, schema-valid, tests, Quality, Git y receipts |
| MP132-R5-09 | P0 | Traces y estados terminales de Story/Jobs/Quality | No PENDING vs PASS contradictorio, evidencias visibles tras DONE, session recovery |
| MP132-R5-10 | P0 | ChangeImpact durante construcción y autorización precisa | Cambio RF upstream reevalúa delta de historias/tests y no duplica apply/commit |
| MP132-R5-11 | P1 | Tratar UX del ledger sobre controles sensibles | Issues D05/D03 se reproducen y se cierran con evidencia por ID o se difieren justificadamente |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

B4: escritura de código, pruebas, jobs, Quality Gate, SourceChangePlan y Git stage/commit/push del **proyecto** solo a través de UI y acciones internas gobernadas, con recibos exactos. Consola auditora nunca hace git add/commit al Pilot B.

---

## Enmienda programática post-R02-06 · 187

**Construction Readiness → slices funcionales:** `MP131-R5-01` y `MP132-R5-08` generan propuestas L para stories arbitrarias sin plantillas RF-specific, con código/tests de tecnología aprobada. `MP131-R5-02..04` reutilizan plan/preimage/approval/apply y jobs/Quality/Git. `MP131-R5-05` exige al menos una story funcional y la prueba integrada del incremento previsto, no solo source/test unit. `MP132-R5-10` extiende impacto a Release/Increment Plan y documentación; tareas técnicas conocidas pueden seguir con D/scaffold, no generan semantic code equivalent. `INCREMENT_ACCEPTED` exige escenarios E2E y negativos relevantes, más evidencia/trazas tras restart. No crear otro engine de Quality.

---

## Enmienda 188 — criterios prospectivos R05

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Owner de esta ola:** Especializar Construction: cambios source, pruebas ejecutables, negativos, code review, calidad de integración y trazabilidad con Requirements/Architecture; no sustituir tests por juicio del modelo ni publicar sin gates.
