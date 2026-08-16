---
doc_id: "DEVPL-GSDLC-01"
title: "DEVPL-GSDLC-01 — Guided SDLC State Engine and persistent Project Status"
status: "approved"
version: "1.2.0"
owner: "Ordóñez"
updated: "2026-08-16"
approval: "approved_by_owner"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip"
source_git_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"
source_repo_sha256: "68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-01"
backlog_status: "approved/executable-design"
micro_sprints_total: 5
approved_at: "2026-08-16"
source_authority_rebound: true
canonical_branch: "eval/post-h-eval-002-02-a-onboarding"
design_source_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_source_git_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_source_repo_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
execution_baseline_kind: "canonical-successor"
r01_dependency_for_execution: "not-required"
r01_context_present_in_baseline: true
pilot_execution_status_required: "paused-before-02-b"
---

# DEVPL-GSDLC-01 — Guided SDLC State Engine and persistent Project Status

## 0. Aprobación, rebind y autoridad de ejecución

**Decisión owner:** `APPROVED / EXECUTABLE-DESIGN`.

Esta versión `1.2.0` aprueba el alcance funcional de `v1.1.0` y lo rebindea a la fuente canónica vigente:

```text
repo
repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip

commit
3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d

SHA-256
68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d

canonical branch
eval/post-h-eval-002-02-a-onboarding
```

La fuente original repo341 queda preservada como **design source histórica**; no se reescribe ni se presenta como baseline actual.

### 0.1 Condición de entrada

El backlog puede iniciar porque `DEVPL-GSDLC-00 = CLOSED/PASS` y la línea GSDLC autoriza `DEVPL-GSDLC-01`. R01 no es dependencia de GSDLC-01; su contenido dentro de repo348 es contexto acumulativo, no gate de entrada para esta ola.

### 0.2 Regla importante sobre snapshots internos

repo348 contiene snapshots históricos/mutables donde `.devpilot/project_state.json.current_repo` todavía puede referenciar repo342 y los artefactos R01-E internos pueden conservar semántica pre-owner. **Eso no invalida repo348 como autoridad externa de ejecución.**

La identidad de entrada de 01-A se acredita por:

1. SHA-256 del ZIP canónico;
2. commit Git real de Windows;
3. rama canónica;
4. worktree limpio;
5. cadena de autoridad GSDLC-00.

No se debe modificar una aserción histórica únicamente para hacer coincidir `current_repo` con repo348.

### 0.3 ADRs de arquitectura consumidos

La aprobación de este backlog autoriza usar como inputs de implementación, sin reescribir su frontmatter histórico:

- `ADR-GSDLC-001 — Guided SDLC Engine boundary`;
- `ADR-GSDLC-002 — Platform, workspace engineering and runtime state separation`;
- `ADR-GSDLC-004 — UI-complete normal journey and project-centric shell`;
- `.devpilot/gsdlc/architecture_target_contract.json`.

La implementación debe mantener:

```text
UI
→ Local API
→ ApplicationService
→ GuidedSDLCService
→ WorkflowEngine
→ typed domain services
→ Policy / Approval / Jobs
→ Evidence / Traces
```

y debe conservar `PlatformState != WorkspaceEngineeringState != RuntimeOperationalState`.

### 0.4 Política de implementación acumulativa

A→E se ejecutan secuencialmente. Cada micro-sprint:

- parte de la autoridad canónica cerrada por su predecesor;
- genera delta exacto, tests, `historical_contract_sweep`, evidencia Windows y owner adjudication;
- no autoriza el siguiente hasta `CLOSED/PASS`;
- usa feature branch propia y promoción `ff-only`;
- genera baseline sucesor canónico limpio;
- no toca el workspace piloto `inventory-sales-local` salvo que un prompt posterior lo autorice expresamente; para GSDLC-01 se usarán fixtures/workspaces sintéticos.


## 1. Objetivo

Crear la máquina de estados determinística que guía un proyecto y una proyección UI persistente de fase, paso, indicadores, blockers y próxima acción.

## 2. Invariante de producto que esta ola debe demostrar

> El usuario no explora documentos para adivinar qué hacer: DevPilot conoce el estado de ingeniería del workspace y siempre puede explicar `dónde estoy`, `qué falta`, `qué está bloqueado` y `qué sigue`.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-00 CLOSED/PASS

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- WorkspaceEngineeringState
- transition/gate engine
- NextAction engine
- filesystem/Git reconciler
- Project Status API/UI

### 4.2 Fuera de alcance

- auth/login
- bootstrap writes
- agent execution
- planning/coding

## 5. Superficies y fuentes que probablemente serán afectadas

- src/devpilot_core/guided_sdlc/*
- docs/schemas/workspace_engineering_state*.json
- ApplicationService
- API routes
- UI project shell

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-01-A — WorkspaceEngineeringState schema and lifecycle vocabulary

**Objetivo.** Definir estado durable por workspace sin reutilizar Platform State.

**Entradas obligatorias**
- GSDLC-00 baseline
- MIPSoftware lifecycle

**Actividades**
1. definir macro phases and artifact substate
2. version/schema migration strategy
3. persistencia source-controlled mínima vs runtime fields
4. workspace_id/repo identity binding
5. invariants de state

**Entregables verificables**
- workspace_engineering_state.schema.json
- state vocabulary doc
- migration contract

**Pruebas / validadores**
- schema positive/negative
- no platform-state coupling tests

**Evidencia mínima**
- fixture states
- schema report

**Seguridad operacional específica**
- no secrets/session/job IDs persistidos como source state
- atomic write plan

**PASS**
- schema cubre NEW→RELEASED y REVALIDATION_REQUIRED

**BLOCK**
- state mezcla runtime volatile
- project_state platform reutilizado

**Salida / autorización**
- autoriza 01-B


### GSDLC-01-B — Deterministic transition and gate engine

**Objetivo.** Implementar transiciones autorizadas por prerequisites/gates.

**Entradas obligatorias**
- 01-A PASS

**Actividades**
1. transition catalog
2. pure evaluator
3. reason codes/blockers
4. approval requirement metadata
5. idempotent advance preview

**Entregables verificables**
- workflow_engine.py
- transition registry
- transition report schema

**Pruebas / validadores**
- transition matrix tests
- illegal skip negative tests
- idempotency

**Evidencia mínima**
- transition_eval_cases.json
- coverage report

**Seguridad operacional específica**
- LLM no participa en PASS/BLOCK
- no source mutation en evaluate

**PASS**
- saltos obligatorios bloqueados
- explicación reproducible

**BLOCK**
- skip permitido
- resultado depende de prompt/modelo

**Salida / autorización**
- autoriza 01-C


### GSDLC-01-C — Progress projection and NextAction engine

**Objetivo.** Derivar Project Status y siguiente acción explicable.

**Entradas obligatorias**
- 01-B PASS

**Actividades**
1. calcular phase/current_step/progress
2. blocker aggregation
3. pending approvals/quality summary references
4. next action priority
5. expose recommended action kind placeholder

**Entregables verificables**
- project_progress.py
- project_status schema
- next_action schema

**Pruebas / validadores**
- projection fixtures
- blocker ordering
- 100% deterministic

**Evidencia mínima**
- status snapshots

**Seguridad operacional específica**
- no revelar secret/runtime payloads
- read-only

**PASS**
- phase/step/indicators/next action siempre definidos o reason=unknown

**BLOCK**
- status contradicts state
- next action no explicable

**Salida / autorización**
- autoriza 01-D


### GSDLC-01-D — Filesystem/Git reconciliation and revalidation

**Objetivo.** Detectar cambios externos sin perder gobernanza.

**Entradas obligatorias**
- 01-C PASS

**Actividades**
1. hash governed artifacts
2. git branch/head/dirty awareness
3. detect external edit/delete/rename
4. move APPROVED→REVALIDATION_REQUIRED
5. conflict report and safe recovery

**Entregables verificables**
- reconciler.py
- reconciliation_report schema

**Pruebas / validadores**
- external edit fixtures
- branch switch fixtures
- approved drift negative tests

**Evidencia mínima**
- reconciliation reports

**Seguridad operacional específica**
- read-only Git commands bounded/timeouts
- no auto-reset/checkout

**PASS**
- drift detected without mutation
- no data loss

**BLOCK**
- approved artifact stays APPROVED after changed hash
- Git destructive action

**Salida / autorización**
- autoriza 01-E


### GSDLC-01-E — Project Status shell and browser acceptance

**Objetivo.** Exponer estado de proyecto como experiencia primaria.

**Entradas obligatorias**
- 01-D PASS

**Actividades**
1. crear project-centric route/shell
2. mostrar fase, paso, MIPSoftware/MIASI, progress, blockers, next action, repo status
3. CTA `Continuar` usa NextAction
4. estados empty/error/revalidation
5. browser accessibility acceptance

**Entregables verificables**
- ProjectStatusView
- API route
- browser matrix

**Pruebas / validadores**
- frontend tests
- API contract
- browser real

**Evidencia mínima**
- screenshots
- HAR sanitized summary
- state/API/UI parity matrix

**Seguridad operacional específica**
- sin acciones mutantes aún
- context isolation

**PASS**
- UI muestra estado correcto 100% fixtures
- 0 console errors S0/S1

**BLOCK**
- status contradicts API
- navigation requires CLI

**Salida / autorización**
- CLOSED/PASS autoriza GSDLC-02


## 7. Alcance transversal específico de esta ola

- Project Status es una superficie permanente reutilizada por todas las olas posteriores.
- La navegación futura debe pivotar sobre proyecto/workflow; Reports/Traces/Jobs/Quality quedan como vistas transversales.

## 8. Política de contratos históricos específica

- No modificar `ui_operational_console_final_*` ni las 9 rutas UOC como hecho histórico; tests deben permitir nuevas rutas post-UOC.
- No reutilizar tests que exigen `current_repo==repo340/341` como invariante futuro.

Antes del cierre de **cada** micro-sprint se debe generar un `historical_contract_sweep` que clasifique los tests/contratos impactados como:

1. `historical-freeze`: valida únicamente el hecho histórico;
2. `current-active`: debe evolucionar con la capacidad vigente;
3. `successor-needed`: requiere nuevo contrato sin reescribir el anterior;
4. `deprecated-after-proof`: solo puede retirarse después de demostrar reemplazo equivalente.

No se permite modificar una aserción histórica únicamente para “hacer pasar pytest”; la modificación debe quedar justificada por esta clasificación.

## 9. Seguridad operacional específica

- Reconciler exclusivamente read-only en esta ola.
- Bloquear symlinks/path escape y repos no registrados.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- schema/unit transition suite
- ApplicationService/API tests
- reconciliation negative suite
- browser acceptance Project Status

Regla de regresión:

- Test Impact y pruebas focales en A→D.
- Browser acceptance en el micro-sprint que introduce/cierra UX.
- Full regression solo si Test Impact lo exige o en el cierre industrial expresamente indicado; no se repite por rutina.

## 11. Evidencia autoritativa esperada

- state fixtures
- transition matrix
- reconciliation evidence
- browser screenshots/parity

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- state engine determinístico
- Project Status funcional
- revalidation externa
- S0/S1=0

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-02 solo si el project shell puede representar actor-neutral state sin auth aún.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

