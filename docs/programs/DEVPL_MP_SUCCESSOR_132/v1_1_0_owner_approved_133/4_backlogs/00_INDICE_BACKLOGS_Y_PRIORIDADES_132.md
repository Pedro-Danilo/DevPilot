---
doc_id: DEVPL-MP-SUCCESSOR-132-00_INDICE_BACKLOGS_Y_PRIORIDADES_132
title: "Índice derivado de backlogs por ola — IDs únicos y dependencias"
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
current_execution_baseline: "cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc"
r01_gate: "CLOSED_PASS_WITH_FINDINGS"
r02_execution_authority: false
planning_amendment_id: "MP132-AMENDMENT-POST-R02-06-187"
planning_amendment_date: "2026-10-17"
planning_amendment_baseline: "b666c5641c1b8231c5b609216f64490a72ff1763"
planning_amendment_execution_authority: false
---

# Índice derivado de backlogs por ola — IDs únicos y dependencias

## 1. Política de autoridad

**Un backlog por ola**, responsable únicamente de los ítems cuyo ID le pertenece. Este índice es un agregador navegable; no mantiene otra copia de tareas y prioridades. La suma de los **66 ítems originales MP131** se conserva por ID sin excepción; los nuevos `MP132` refinan el programa y no son prompts/sprints.

| Ola | Backlog propietario | IDs 131 preservados | IDs 132 añadidos |
|---|---|---:|---:|
| R0 | [BACKLOG_R00_132.md](BACKLOG_R00_132.md) | 5 | 4 |
| R1 | [BACKLOG_R01_132.md](BACKLOG_R01_132.md) | 7 | 9 |
| R2 | [BACKLOG_R02_132.md](BACKLOG_R02_132.md) | 6 | 4 |
| R3 | [BACKLOG_R03_132.md](BACKLOG_R03_132.md) | 6 | 4 |
| R4 | [BACKLOG_R04_132.md](BACKLOG_R04_132.md) | 5 | 3 |
| R5 | [BACKLOG_R05_132.md](BACKLOG_R05_132.md) | 7 | 4 |
| R6 | [BACKLOG_R06_132.md](BACKLOG_R06_132.md) | 5 | 3 |
| R7 | [BACKLOG_R07_132.md](BACKLOG_R07_132.md) | 6 | 2 |
| R8 | [BACKLOG_R08_132.md](BACKLOG_R08_132.md) | 6 | 2 |
| R9 | [BACKLOG_R09_132.md](BACKLOG_R09_132.md) | 6 | 3 |
| R10 | [BACKLOG_R10_132.md](BACKLOG_R10_132.md) | 7 | 3 |

## 2. Epics vs waves

La ola es agrupación programática. Cada una puede contener múltiples épicas/features/stories tras auditoría; **una ola no equivale a un único Sprint Backlog**. Los 66 IDs antiguos son requirements/features de programa, no tareas listas para ejecutar. No asignar estimates ficticios ni ejecutar por leer esta tabla.

## 3. Consolidación y cambio

IDs inmutables, `owner_wave`, `priority`, `depends_on`, `status`, `baseline_binding`, `evidence_refs`, `decision_ref`. Los cross-wave blockers se registran en `PROGRAM_DEPENDENCY_REGISTER`, no duplicando filas. El Owner puede cambiar orden mediante successor aprobado y registrar justificación y efecto en critical path; nunca sincronización manual conflictiva entre 11 autoridades.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Índice backlogs.
- **Actualización concreta:** R00 cerrado con findings, R01 desagregado para planificación; R02 se mantiene planificado no ejecutado; no doble ownership.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- `BACKLOG_R01_132.md`: `CLOSED_PASS_WITH_FINDINGS`, 16 IDs en 15 micro-sprints; R01-11 COR-166 y R01-13 CONT-169 forman parte de la cadena de aceptación.
- `BACKLOG_R02_132.md`: `OWNER_APPROVED_PROGRAM / EXECUTION_NOT_AUTHORIZED`, 10 IDs repartidos en 10 sprints propuestos. Los dos backlogs tienen authorities distintas; no migrar tareas R02 a R01 cerrado.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

**Transversal:** `UI_FIRST_PILOT_B_V1` exigible a B0–B7. R02-05/COR-179 audita identidad post-UI; R03/R04/R05/R06 implementan workflow UI de sus acciones y R10 audita la cadena. R9 se limita al launcher de la plataforma; ninguna fase acepta terminal humana para ejecutar el piloto.

---

## Enmienda programática post-R02-06 · 187

Mantener sin cambios IDs, prioridades históricas y propiedad de los ítems. **Lectura prospectiva:** R2→`ADR_MP132_013_SEMANTIC_AUTHORING_187`; R3→`ADR_MP132_015_TECH_CONSTRUCTION_187`; R4/R5/R6→`ADR_MP132_014_INCREMENT_DELIVERY_187` y `SOFTWARE_INCREMENT_AND_DELIVERY_CONTRACT_132.md`. La comparación D/L R02-06 permanece cerrada como evidencia, pero no se transforma en requisito repetido. Enmiendas de backlog afectan la planificación futura, no reabren R00/R01 ni R02-01..06.

---

## Continuidad de propiedad por ola — A188

No cambian los 66 IDs originales ni los propietarios R0–R10. ADR-016 y contrato transversal 188 informan los AC futuros: R2 Product Definition/segundo dominio; R3 Architecture; R4 Planning; R5 Construction; R6 Release; R7–R8 agentes/E opcionales; R9 resiliencia UX; R10 aceptación. R02-07 cerrado, R02-08 DRAFT sin autorización ejecutable por adoptar A188.
