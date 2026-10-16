---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R02_132
title: "Backlog R2 — Product Definition y modelo local real"
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

# Backlog R2 — Product Definition y modelo local real

## Resultado y gate de ola

**Ola R2 — Product Definition y modelo local real.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R2-01 | P0 | Auditoría focal y contrato Product Definition D/L | Rutas ya existentes inventariadas; equivalencia determinística sin regresión; RAG source scopes correctos |
| MP131-R2-02 | P0 | Ollama local opt-in para Product Definition | Modelo local instalado y realmente llamado; salida estructurada validada; sin API key, sin cloud ni source writes |
| MP131-R2-03 | P1 | LM Studio local opt-in y paridad funcional acotada | Health, endpoint loopback, request, timeout, structured output, error y fallback medidos; D disponible offline |
| MP131-R2-04 | P0 | Selección/comparación D/L de Vision/Scope/Requirements | Candidates comparables en UI, origen+linaje, Owner decide; semantic RF gate y approvals antes de FROZEN |
| MP131-R2-05 | P0 | Pilot B B0–B1: greenfield, constraints, Product Definition | Workspace nuevo; Project Entry→Vision→Scope→Requirements FROZEN en UI; `operator_project_writes=0` |
| MP131-R2-06 | P1 | Fallas local real: desconexión, JSON malo, model unavailable | Sin cambios no autorizados ni doble candidate; fallback explícito/denegación; trazas sin secretos |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R2-07 | P0 | Readiness de modelo local en Settings | SUPPORTED/HEALTHY/EVALUATED/ELIGIBLE separados; modelo real probado; no requiere API paga |
| MP132-R2-08 | P0 | Documentos Pre-code humanos persistentes | Vision/Scope/Requirements publicadas Markdown FROZEN, authority/hashes y portable |
| MP132-R2-09 | P1 | PESP, Coverage Gate y revisión semántica por primera app | No se exigen artefactos técnicos aún no decididos; gated business artifact quality |
| MP132-R2-10 | P1 | Home/Entry UX/Resume y trazabilidad de idea real | Owner entra necesidad y constraints, no stack hardcoded ni terminal |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

## Actualización operativa MP132 post-M1 — R02-01

**Autoridad R02 y progreso.** R02 desagregado en 10 incrementos aprobados únicamente para planificación. **Solo R02-01** tiene aprobación Owner individual para ejecutarse en cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc. R02-02..10 conservan ejecución denegada; modelo L real `NOT_TESTED`, externas `DENIED`.

**Autoridad:** esta sección actualiza el *estado operativo*, no modifica el `status: OWNER_APPROVED_PROGRAM` de la aprobación histórica Owner-133, ni autoriza R02-02. Source Registry mantiene el `doc_id` y `path` originales.


## Adenda de estado operativo — R02-03/COR-176 (sucesora, no retroactiva)

- **Predecesores acreditados:** R02-01 `CLOSED/WINDOWS_PASS` en `4a4443f1631acdbfcd19e1e2fca4be36f707daf9`; R02-02 `CLOSED/WINDOWS_PASS` en `8a9b1cf915f8cfb9d08b35d6d1c13467d0bd08fc`. Las adendas R02-01 anteriores se conservan como historia, no son la autoridad de ejecución actual.
- **Autorización individual vigente:** únicamente `R02_03_OLLAMA_REAL_CANDIDATE_SPRINT.md` = `SPRINT_EXECUTION_APPROVED` y su prompt = `OWNER_APPROVED`; baseline R02-02 acreditado y rama `evolution/multiprovider-v2`. Este bloque NO constituye recepción Windows de R02-03.
- **Gate de salida R02-03:** al menos tres candidatas sintéticas generadas mediante invocación **real** a Ollama en loopback, con procedencia, hashes, recibos JSON, revisión browser, negativas y ninguna publicación FROZEN ni cambio de enabled global. Hasta observarlo, `LOCAL_PASS/WINDOWS_PENDING`; `EVALUATED`/`ELIGIBLE` NO se conceden automáticamente.
- **Límites:** R02-04 a R02-10 = `DRAFT/NOT_AUTHORIZED`; proveedores externos y MP-1B = `DENIED/NOT_AUTHORIZED`; M2 no declarado. Se conservan todos los `doc_id`, el status histórico `OWNER_APPROVED_PROGRAM` y los 1.752 registros del Source Registry.
