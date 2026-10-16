---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R01_132
title: "Backlog R1 — Kernel, estándares, artefactos y configuración"
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

# Backlog R1 — Kernel, estándares, artefactos y configuración

## Resultado y gate de ola

**Ola R1 — Kernel, estándares, artefactos y configuración.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R1-01 | P0 | Auditar y unificar el bridge Story con `GenerationRequest/ArtifactCandidateEnvelope` | Un adapter tipado enlaza Story→Envelope; no duplicate source/apply authority; pruebas en ≥2 dominios |
| MP131-R1-02 | P0 | Estado candidate lifecycle, idempotencia, lineage y provenance comunes | Reintento terminal no duplica; hashes input/context/output/provider/prompt/version; comparación reproducible |
| MP131-R1-03 | P0 | `ModelAdapter` proveedor-independiente y capability negotiation | D/L/E se distinguen por capacidad, output, tool/streaming/timeout; failure de un provider no habilita otro silenciosamente |
| MP131-R1-04 | P0 | Routing/policy/budget fallback único y default-deny | Política negada bloquea antes de ejecutar; fallback requiere permiso y registra causal/latencia |
| MP131-R1-05 | P1 | Artifact Profiles v2, dependency profiles y versionado FROZEN | required/recommended/conditional/N-A justificable; inmutabilidad y successor documentados |
| MP131-R1-06 | P0 | Reusable eval harness de candidates y código | Datasets versionados; schema, semantic gates, groundedness, fallos negativos, trazas y reports reproducibles |
| MP131-R1-07 | P1 | Observabilidad provider/agent y UX de origen/costo | Provider, modelo, fuente, elección, fallback, error y costo visibles en Guided/Expert sin secretos |

**Rebind v1.1:** R1-05 deja de ser solo perfil documental: PESP/Catalog/Coverage y successor básico se exigen tempranamente; no implementar todo el catálogo en R1.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R1-08 | P0 | Project Engineering Standards Profile — esquema y primera vertical | MIPSoftware required, MIASI conditional, Owner profile approval y prueba N/A/waiver |
| MP132-R1-09 | P0 | Artifact Catalog con Coverage Gate y dependencia | Required/conditional/recommended/N-A, blocking meaningful, no empty templates |
| MP132-R1-10 | P0 | Document Authority + Markdown Publication mínima | Doc aprobado visible en docs y referenciado desde Source Registry, drift no silencioso |
| MP132-R1-11 | P0 | FROZEN successor + ChangeImpact primera vertical | Revisión sucesora preserva histórica y marca dependencias stale selectivamente |
| MP132-R1-12 | P0 | GenerationRoutePolicy D/L/E y fallback semántico | Selección por tarea, `MODEL_REQUIRED` sin template equivalente y provenance/deny |
| MP132-R1-13 | P0 | Settings configuración persistente, policy y runtime separados | Effective value/origin, restart/approval, runtime kill distinto de setting plan-only, tests browser |
| MP132-R1-14 | P1 | WorkflowStatusProjection y feedback in situ | Mismo objeto gate refleja estado en UI header/panel; terminal CTAs deshabilitados |
| MP132-R1-15 | P1 | Project Layout lógica vs TechnologyProfile | Bootstrap neutral, documentos lazy, scaffold futuro bajo Owner |
| MP132-R1-16 | P0 | Madurez y gates por alcance verificable | Fixture/service/UI/E2E diferenciados, ninguna declaración por mera clase o pantalla |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

## Actualización operativa MP132 post-M1 — R02-01

**Cierre de ola R01.** R01-01..15 y los 16 IDs de backlog: `CLOSED_PASS_WITH_FINDINGS` desde Windows COR171, HEAD cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc. Sus 3 browser attestations no demuestran uso de LLM real; hallazgos históricos permanecen en recibos, no se reescriben.

**Autoridad:** esta sección actualiza el *estado operativo*, no modifica el `status: OWNER_APPROVED_PROGRAM` de la aprobación histórica Owner-133, ni autoriza R02-02. Source Registry mantiene el `doc_id` y `path` originales.
