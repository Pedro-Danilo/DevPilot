---
doc_id: DEVPL-MP-SUCCESSOR-132-BACKLOG_R03_132
title: "Backlog R3 — Arquitectura, riesgo y scaffold"
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

# Backlog R3 — Arquitectura, riesgo y scaffold

## Resultado y gate de ola

**Ola R3 — Arquitectura, riesgo y scaffold.** Ver `0_program/02_ROADMAP_INDUSTRIAL_132.md` y `2_contratos/PROGRAM_DEPENDENCY_REGISTER_132.md` para dependencias. Cada fila es una capacidad **propuesta**, no una orden de implementación. Antes de tocar source se exige Audit-first, head y Owner approval.

## Ítems heredados v131 — preservados por ID, authority sucesora 132

| ID original estable | Prioridad | Resultado conservado | AC original — sujeto a clarificaciones 132 |
|---|---|---|---|
| MP131-R3-01 | P0 | `TECHNICAL_RAG_SOURCE_PROFILE` y restricciones de autoridad | ContextPack prioriza ADR/RF/security vigentes; changelog histórico no se trata como decisión técnica actual |
| MP131-R3-02 | P0 | TechnicalDesignCandidate tipado D/L y quality gates cruzados | Schema+renderer; RF→Architecture→ADR→Security→Tests consistente; unsupported assertions bloquean |
| MP131-R3-03 | P0 | ADR companion gobernado y selección tecnológica | ADR standalone approval-bound, profile tecnológico con alternativas/rationale; sin decidir stack antes de Architecture |
| MP131-R3-04 | P0 | Technical Scaffold & Dependency Provisioning separado de authoring | Plan/diff/approval/execute, constraints/red/policy, locks y rollback; sin instalación manual del Owner |
| MP131-R3-05 | P0 | Pilot B B2: baseline técnico FROZEN y proyecto listo | Architecture, Security, Test Strategy, Traceability y ADRs FROZEN; scaffold reproducible y verificado |
| MP131-R3-06 | P1 | Evals de arquitectura y threat model de IA/RAG | Fixtures falsos, decisiones no grounded y payload injection rechazados; métricas registradas |

**Rebind v1.1:** Preservar el objetivo y criterio de aceptación de los ítems heredados, rebindeados al baseline/contratos 132 y sin prompts históricos ejecutables.

## Nuevas capacidades v1.1 asignadas a esta ola

| ID nuevo | Prioridad | Capacidad / entrega | AC verificable |
|---|---|---|---|
| MP132-R3-07 | P0 | Catálogo condicional de datos/API/UX/domain/interfaces | Activación comprobada por proyecto; schemas, diagramas, API/test y N/A rationale |
| MP132-R3-08 | P0 | Layout/TechnicalScaffold independiente del documento | Stack decidido en Architecture, plan/diff, aprobación e imports/lockfile reproducibles |
| MP132-R3-09 | P0 | Markdown técnico publicado y reconciliado | Architecture, ADR, Security, Test y Traceability con lineage, sin source of truth duplicado |
| MP132-R3-10 | P1 | Cambios sucesores de ADR/TechnologyProfile | Nuevo ADR no instala dependencias ni reescribe diseño FROZEN |

## Reglas de estado y aceptación

- Estados por ítem: `PROPOSED`, `READY_AFTER_AUDIT`, `AUTHORIZED`, `IN_PROGRESS`, `BLOCKED`, `DONE_ACCEPTED`, `DEFERRED_WITH_REASON`, `NO_OP_ACCEPTED`. La versión 1.1 **no declara ninguna ejecución nueva**.
- Un ID tiene una sola ola propietaria. Dependencias a otra ola se referencian por ID, no se copian. Un auditor puede proponer `REUSE/NO-OP`; no se fuerza código.
- Una ola se cierra con gate, evidencia y Owner adjudication, no por sumar checkboxes ni terminar un listado de archivos. Tests de UI/sistema/modelo reales si esa ola promete verticalidad.
- No crear sprints/prompts por adelantado. El sprint futuro se rebindea a HEAD, incluye análisis de compatibilidad, presupuesto y allowlist exacta.


## Aclaración de autoridad Owner-133

Este backlog está **aprobado para priorización y planificación**. Sus ítems aún no equivalen a tareas ejecutables o aceptadas. La auditoría focal y una orden de alcance específica determinan `READY_AFTER_AUDIT` y `AUTHORIZED`. Los ítems R0 de ratificación se consideran satisfechos **documentalmente** por Owner-133, pero la publicación operativa de autoridad todavía debe verificarse en Windows.

## Adenda Owner UI-first 179 — UI_FIRST_PILOT_B_V1

B2: decisiones de arquitectura, stack y ADRs se proponen/revisan/aprueban/materializan exclusivamente en UI, sin edición manual de documentos ni terminal para instalar scaffold; el backend puede ejecutar herramientas tipadas autorizadas.

---

## Enmienda programática post-R02-06 · 187

**Reforzar M3 sin crear ítems:** `MP131-R3-03`/`MP132-R3-07`: Technology Decision Workbench dentro de Architecture, drivers/riesgos/calidad/alternativas justificadas (solo cuando son materiales), ADRs independientes; aprobación del Architecture cubre la decisión explicitada. `MP131-R3-04`/`MP132-R3-08`: scaffold **posterior**, gobernado e idempotente, manifests/lockfiles, dependencias/costos/red y comandos test/build/run + health; no instalar stack por FROZEN. `MP131-R3-05`: M3 requiere al menos startup reproducible + smoke sobre scaffold y Technical Baseline FROZEN. Introducir `ConstructionReadiness` como proyección derivada de los componentes existentes; no nuevo rol de aprobación trivial. Aplicar MIPSoftware drivers y MIASI condicional por componente.

---

## Enmienda 188 — criterios prospectivos R03

**Enmienda 188 Owner-approved (2026-10-22)**. Autoridad `MP132-OWNER-DECISION-188`; contrato `2_contratos/ARTIFACT_AUTHORING_QUALITY_CONTRACT_188.md` y ADR-MP132-016. Complementa 187/ADR-013; se aplica prospectivamente por olas, sin alterar recibos históricos, ni autorizar ejecución de un sprint o proveedor E.

**Owner de esta ola:** Especializar el perfil de Architecture: drivers, ADR materiales, decisiones de datos/API/UX, riesgos y grounding en Vision/Scope/Requirements FROZEN; no obligar técnicas que PESP descarte. Evaluación focal por impacto y sin usar Pilot B como requisito global.

---

## Adenda de cierre R02 → planificación R03 — 2026-10-22

La desagregación R03 queda especificada en `7_ Execution_packages-sprints_prompts/BACKLOG_R03/00_PLAN_R03_189.md`: **11 micro-sprints** más 11 prompts `DRAFT`; referencia factual `1f15fa5b770db37c684e870a49572dcb569bd3a4` / M2 `PASS_WITH_FINDINGS`, sin inferir aprobación individual. Se preservan los diez IDs originales `MP131-R3-01..06`, `MP132-R3-07..10`. R03_01 audita y corrige drift activo del baseline canónico antes de autoría técnica. A188/ADR-016 exige perfiles específicos pero generalizables y un segundo dominio no sensible; PESP decide obligatoriedad condicional. Pilot B no es un gate universal y su TechnologyProfile no puede predeterminarse desde este plan.

**Actualización de autorización 2026-10-23:** el Owner aprobó individualmente `R03_01_DOC_RECONCILIATION` (`SPRINT_EXECUTION_APPROVED`) y su prompt (`OWNER_APPROVED`), limitados al baseline `1f15fa5b...`. Su ejecución y cierre Windows aún no están probados; R03_02..11 siguen DRAFT. El párrafo anterior describe el estado histórico de la planificación A189 del 2026-10-22.

**Sucesor de cierre y autorización individual, 2026-10-23:** la afirmación anterior era verdadera antes de COR3; quedó superada por evidencia Windows y el cierre técnico R03-01 `PASS_WITH_FINDINGS` (HEAD `9c51d987a696...`). Owner aprobó ahora solo R03-02, rebindeado al mismo HEAD y en espera de validación Windows. R03-03..11 siguen sin autorización. Autoridad trazable: `6_trazabilidad/17_R03_01_CLOSURE_R03_02_AUTHORITY.md`. No se reescriben evidencias históricas.

## A190 y checkpoint de ejecución — 2026-10-24

La política A190 quedó activada en R03_03 y será especializada en R03_04–R03_07 por el sprint propietario; no confiere aprobación a los futuros. R03_03 cerró `PASS_WITH_FINDINGS` con C11 Windows, commit/push `df6a5dcbb6eeb112008db1373d2e975cbc60b18f` y ZIP baseline `git archive HEAD` verificado. Architecture Pilot B continúa en revisión semántica, sin aprobación/apply/freeze del artefacto. El Owner autorizó individualmente **solo R03_04** sobre ese baseline para propuestas tecnológicas y ADR materiales dentro del mismo approval Architecture, sin instalar dependencias. R03_05+ permanecen no autorizados.

## Decisión Owner R03_04_C02 — 2026-10-25

C01 (tarjetas abatibles en Pre-code Guided/Expert) queda PASS/CLOSED. Se amplía el **mismo sprint R03_04** antes de cerrarlo: Ollama local debe generar un Technology Options independiente con 2–3 stacks y una ADR material, Owner selecciona una opción en UI, una revisión sucesora Architecture DRAFT invalida el plan anterior y la publicación de documentos `technology_options.md` y `adrs/ADR-001-*.md` se hace bajo el publisher multiarchivo y approval normal ya existente. Prohibido confundir candidata con FROZEN, publicar automáticamente, instalar dependencias, suponer calidad semántica o delegar redacción Owner. La siguiente ola R03_05+ no queda autorizada. Fuente: `R03_04_C02_PROPOSAL.md` aprobado por Owner, sprint/prompt R03_04 v1.0.2.

## Decisión Owner R03_04_C02 — 2026-10-25

C01 (tarjetas abatibles en Pre-code Guided/Expert) queda PASS/CLOSED. Se amplía el **mismo sprint R03_04** antes de cerrarlo: Ollama local debe generar un Technology Options independiente con 2–3 stacks y una ADR material, Owner selecciona una opción en UI, una revisión sucesora Architecture DRAFT invalida el plan anterior y la publicación de documentos `technology_options.md` y `adrs/ADR-001-*.md` se hace bajo el publisher multiarchivo y approval normal ya existente. Prohibido confundir candidata con FROZEN, publicar automáticamente, instalar dependencias, suponer calidad semántica o delegar redacción Owner. La siguiente ola R03_05+ no queda autorizada. Fuente: `R03_04_C02_PROPOSAL.md` aprobado por Owner, sprint/prompt R03_04 v1.0.2.
