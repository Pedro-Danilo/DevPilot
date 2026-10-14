---
doc_id: DEVPL-MP-SUCCESSOR-132-00_INDICE_BACKLOGS_Y_PRIORIDADES_132
title: "Índice derivado de backlogs por ola — IDs únicos y dependencias"
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
