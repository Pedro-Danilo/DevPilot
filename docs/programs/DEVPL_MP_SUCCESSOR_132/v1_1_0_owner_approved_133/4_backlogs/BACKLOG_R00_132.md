---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R00_132
title: "Backlog R0 — Autoridad y topología Git"
version: "1.1.1-r00-succ"
status: "OWNER_APPROVED_PROGRAM"
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
---

# Backlog R0 — Autoridad y topología Git

## Resultado y gate de ola

**Ola R0 — Autoridad y topología Git.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R0-01 | P0 | Ratificación administrativa G5, si se desea cerrar formalmente el expediente histórico | Decisión Owner separada, referida a SHA G5 y sin modificar recibos históricos |
| MP131-R0-02 | P0 | Aprobar programa sucesor y supersession documental acotada | Owner aprueba hashes y HEAD; mapa de documentos previos vigente/superseded; Source Registry successor |
| MP131-R0-03 | P0 | Resolver política Git/worktree y ejecutar preflight read-only | Branch canónica y upstream explícitos; root/venv/runtimes sin contaminación; ninguna rama perdida |
| MP131-R0-04 | P0 | Aplicar `AUDIT-FIRST` como gate de todo sprint/corrective futuro | Auditoría focal, Reuse/Delta Map, allowlist y tests como prerrequisitos; `NO-OP` soportado |
| MP131-R0-05 | P1 | Baseline de métricas, riesgos y UX-P1 | Ledger actual, referencias, baseline de test/cobertura/perf y presupuesto de ejecución sin números inventados |

**Rebind v1.1:** MP131-R0-03 constituye un **gate de selección/migración B**, no sólo un preflight sin decisión; si falla se conserva worktree MP.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R0-06 | P0 | Gate B Git para traslado a DevPilot_Local o permanencia en MP | Owner acepta preflight read-only tracked/untracked/ignored/process/.venv/upstream, backup/rollback y decisión sin rama perdida |
| MP132-R0-07 | P0 | Registrar aprobación integral 132, supersession 131, ratificación G5/COR-130 y levantamiento global STOP | Actas 133 emitidas; PENDIENTE publicación gobernada Source Registry/authority index con pruebas de paridad; STOP global OWNER_LIFTED, controles por incremento preservados |
| MP132-R0-08 | P0 | Auditoría Settings/UI y ledger por fuente viva antes de cambio | Mapa UI→API→stores/policy, hallazgos S2 contextualizados y allowlist propuesta |
| MP132-R0-09 | P1 | Estado de evaluación/hardware inicial, métricas y presupuestos | Dataset/hardware/latencia medidos o `NOT_AVAILABLE`, no cifras inventadas |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Backlog R00.
- **Actualización concreta:** 9 ítems: 8 DONE_ACCEPTED y R0-09 DEFERRED_TO_R2_WITH_REASON; gate M0 cerrado por COR-151 sin modificar fuente histórica.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.
