---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R01_132
title: "Backlog R1 — Kernel, estándares, artefactos y configuración"
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


---

## Addendum operacional M0→R1 — sucesor de planificación (14-10-2026)

- **Asunto:** Backlog R01.
- **Actualización concreta:** 16 IDs conservados y asignados a 15 incrementos; M1/ejecución aún no autorizados; primer source mutation incluye reconcile heredada M0.
- **Evidencia vinculada:** COR-143 (migración B), R00-03/COR-145 (publicación 57 documentos), R00-04/COR-147 (auditoría Settings), COR-150 (paridad 1752), COR-151 (cierre Owner M0).
- **HEAD de autoridad técnica:** `66ab2e6227072c951b5bd2ac9160e8515b1b9fc0`. Las referencias a `8db5b44694abcced3231183e05731e732f5b8f24` y los indicadores `STOP ACTIVE` en secciones históricas no se reescriben como si fueran estados presentes.
- **Autoridad:** copia sucesora propuesta para adopción documental posterior; no constituye un commit, promoción Git, autorización de R1, de MP-1B, de modelo/API externa ni una aceptación funcional de Settings.
- **Transferencias vigentes:** `MP132-R0-09` → R2 para mediciones reales; UX Settings pendiente de reproducción y validación; egress externo DENY; no duplicar ownership entre olas.


---

## Adenda sucesora post-M1 — 15-10-2026 (no retroactiva)

- **Baseline Git publicado:** `cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc` (`evolution/multiprovider-v2`), sucesor de `feaac2723c1f8a467f5cdb7d456e4e7679dd0f82` por R01-15/COR-171. - **R01:** 15/15 incrementos aceptados; 16 IDs propietarios cubiertos; cierre M1 `PASS_WITH_FINDINGS` con 108 tests focales y 8 del operador PASS en Windows. - **Evidencia:** `RESULT_171.json`, `M1_REPORT_171.json`, `R01_15_EVIDENCE.zip`, `repo_R01_15_CLEAN.zip` y SHA256. - **Autoridad:** R02 se desagrega sólo para planificación. Ningún `SPRINT_EXECUTION_APPROVED`, ningún push, bootstrap Pilot B, inferencia local, external egress o MP-1B queda autorizado por esta adenda. - **Limitaciones:** `model_local_real=NOT_TESTED`, `semantic_llm_judge=NOT_TESTED`, `rag_groundedness_real=NOT_TESTED`, `external_real=DENIED`; no confundir pruebas de servicio con un recorrido completo Product Definition UI.
- **Disposición de 16 IDs:** `MP131-R1-01..07` y `MP132-R1-08..16` cubiertos por R01-01..15 según `PLAN_DESAGREGACION_R01_152.md`, cada uno con evidencia Windows, incluidas las integraciones COR-166 y CONT-169. `MP132-R1-13` abarca R01-10 + R01-11.
- **Dictamen del backlog:** `CLOSED_PASS_WITH_FINDINGS` para servicios deterministas/primera vertical; hallazgos rotulación de recibos R01-04/09, R01-12 indicator legacy y ausencia de modelo real se heredan como riesgos trazados, **no como ítems reabiertos**.
- R2 es explícitamente NO autorizado; ids de R2 no se contabilizan para cierre R1.

## Registro histórico R02 conservado — recuperación R03-01 COR2

Esta sección conserva literalmente antecedentes R02 del repositorio predecesor `1f15fa5b770d` que fueron omitidos al reconciliar R03. **Es historia, no autoridad operativa vigente**: los estados y las autorizaciones actuales son los establecidos por las adendas R03/A189 anteriores y el estado de ejecución de DevPilot. No revive sprints ni concede permisos.

## Actualización operativa MP132 post-M1 — R02-01

**Cierre de ola R01.** R01-01..15 y los 16 IDs de backlog: `CLOSED_PASS_WITH_FINDINGS` desde Windows COR171, HEAD cd0bce59ec2bf4a7ae7e50a555c1c8a1bd85facc. Sus 3 browser attestations no demuestran uso de LLM real; hallazgos históricos permanecen en recibos, no se reescriben.

**Autoridad:** esta sección actualiza el *estado operativo*, no modifica el `status: OWNER_APPROVED_PROGRAM` de la aprobación histórica Owner-133, ni autoriza R02-02. Source Registry mantiene el `doc_id` y `path` originales.
