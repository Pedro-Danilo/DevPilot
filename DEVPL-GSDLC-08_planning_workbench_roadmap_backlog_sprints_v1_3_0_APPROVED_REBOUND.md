---
doc_id: "DEVPL-GSDLC-08"
title: "DEVPL-GSDLC-08 — Planning Workbench — roadmap, backlog and sprint construction"
status: "closed"
version: "1.3.0"
owner: "Ordóñez"
updated: "2026-09-03"
approval: "approved_by_owner/rebound_repo397"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "ba1a87adf7d7b17a2f41f1c5821b86a86b762877"
source_repo_sha256: "109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a"
source_repo_role: "execution-authority/windows-validated-canonical"
execution_source_policy: "repo397/current-canonical-successor-of-FRX-v2.3"
predecessor_backlog: "DEVPL-GSDLC-07"
activation_requires_owner_adjudication: false
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-08"
backlog_status: "CLOSED/PASS"
micro_sprints_total: 5
closure_repo: "repo_DevPilot_Local_403_DEVPL_GSDLC_08_E_PLANNING_TRACEABILITY_BROWSER_ONE_FULL_WINDOWS_VALIDATED_CANDIDATE.zip"
closure_decision: "CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY"
validation_policy: "A-D impact+focal+cumulative; E exactly-one-logical-full; default workers=1; safe-parallel opt-in <=2 only by pre-full owner adjudication; no rerun; composite recovery"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
---


## 0.0 Owner approval y rebind current-active — 2026-09-03

Este `v1.3.0 APPROVED_REBOUND` sustituye como autoridad ejecutable al `v1.2.0 proposed` sin borrar su valor como origen de diseño.

Autoridad canónica de ejecución:

- repo: `repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`;
- commit: `ba1a87adf7d7b17a2f41f1c5821b86a86b762877`;
- SHA-256: `109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a`;
- predecessor funcional `DEVPL-GSDLC-07 = CLOSED/PASS`;
- Full Regression v2.2 = `CLOSED/PASS`;
- Full Regression v2.3 = `CLOSED/PASS/WINDOWS-VALIDATED`;
- FRX-v2.3-E = `CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY`;
- parallel disposition heredada = `PASS/AVAILABLE-NOT-DEFAULT`;
- `DEVPL-GSDLC-08-A` queda autorizado después del activation/rebind no funcional descrito por el prompt `00`.

La referencia histórica repo341 permanece únicamente como design-origin en el documento v1.2.0. **Está prohibido ejecutar GSDLC-08 contra repo341.**

### Full regression heredada

- A→D: no consumen full por rutina.
- E: consume exactamente una logical full después de Contract Reconciliation Sweep, gates baratos y browser/capability acceptance.
- Modo por defecto: temporal/coarsened serial, `workers=1`.
- Safe parallel `workers<=2`: capacidad disponible, no default; requiere adjudicación owner explícita **antes** de iniciar la única full.
- Si una full falla, queda inmutable y no se repite. Correctives: exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard + composite recovery.
- Tests nuevos forman parte de la colección global automáticamente; nacen `UNCLASSIFIED/parallel_safe=false` y permanecen seriales hasta promoción explícita sustentada en evidencia.


## 0.2 Cierre Windows de la ola — 2026-09-04

`DEVPL-GSDLC-08 = CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY` después de GSDLC-08-E Windows browser acceptance, required planning coverage 100%, S0/S1=0 y exactamente una logical full regression consumida 1/1. La full original se preserva inmutable con 2968/2968 accounted, 2917 PASS / 46 FAIL / 0 ERROR / 5 SKIP; el cierre se obtiene únicamente por recovery selectivo autorizado: exact failed-nodeid 46/46 PASS + bounded impacted PASS + Historical Regression Guard PASS + gates post-recovery PASS. No hubo segunda full. El successor canónico es `repo_DevPilot_Local_403_DEVPL_GSDLC_08_E_PLANNING_TRACEABILITY_BROWSER_ONE_FULL_WINDOWS_VALIDATED_CANDIDATE.zip`. GSDLC-09 queda formalmente autorizado; el inicio funcional queda sujeto al hardening/preflight FRX v2 recomendado para impedir bypasses del perfil current-active; las secciones históricas de activación/rebind permanecen como registro y no se reinterpretan como autoridad current-active.

# 0. Política de binding de ejecución

El v1.2.0 conserva como **origen de diseño** repo341. Este v1.3.0 ya está rebíndeado a repo397 y **solo puede ejecutarse contra la autoridad current-active declarada en frontmatter o sus successors Windows-validados**.

La adjudicación requerida por v1.2.0 ya fue satisfecha por este rebound:

- `DEVPL-GSDLC-07 = CLOSED/PASS`;
- Full Regression v2.2 = `CLOSED/PASS`;
- Full Regression v2.3 = `CLOSED/PASS/WINDOWS-VALIDATED`;
- successor canónico = `repo_DevPilot_Local_397_FRX_V2_3_E_ONE_FULL_SAFE_PARALLEL_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`;
- commit = `ba1a87adf7d7b17a2f41f1c5821b86a86b762877`;
- SHA-256 = `109045dccb59fe235c60aac688dcee17e169dae174428df04fb3e1925dbff72a`;
- owner approval = este `v1.3.0 APPROVED_REBOUND`.

El `source_repo` de este frontmatter **sí es execution authority**. El prompt `00` únicamente materializa el rebind dentro del repo y reconcilia Project State / Source Registry / README / roadmap antes de la primera mutación funcional. Cada micro-sprint posterior debe encadenarse al successor Windows-validado del anterior.

No está permitido volver a repo341 o a otro parent histórico para “simplificar” implementación. La evolución es acumulativa.

## 0.1 Invariantes heredadas

1. La navegación project-scoped solo opera con proyecto activado por el journey GSDLC-03.
2. La sesión/RBAC/approval server-side sigue siendo autoridad; storage browser es UX-only.
3. Stores `runtime-ephemeral` (`auth.db*`, `devpilot.db*`, etc.) no se copian a fixtures/sandboxes.
4. Mutaciones son typed operations gobernadas; no arbitrary shell.
5. Los contratos históricos se preservan como hechos scoped y evolucionan mediante successors.
6. El backlog debe incorporar cualquier adjudicación externa del predecessor antes de cambios funcionales.


# DEVPL-GSDLC-08 — Planning Workbench — roadmap, backlog and sprint construction

## 1. Objetivo

Convertir artefactos aprobados en planning trazable y editable desde UI: milestones→epics→stories→sprints, manual o agent-assisted.

## 2. Invariante de producto que esta ola debe demostrar

> Al alcanzar PRE_CODE_READY, DevPilot propone `Construir roadmap`; el usuario puede escribir, importar o usar agente y mantiene cobertura requirement→planning.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-07 CLOSED/PASS
- Full Regression v2.3 CLOSED/PASS/WINDOWS-VALIDATED

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- planning state
- roadmap
- backlog
- sprint planning
- coverage/dependencies
- approval/freeze

### 4.2 Fuera de alcance

- coding
- test execution
   
## 5. Superficies y fuentes que probablemente serán afectadas

- workspace planning artifacts
- Guided state
- Artifact/Agent Workbench
- traceability

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-08-A — Planning domain schemas and lifecycle

**Objetivo.** Definir entidades planning y su trazabilidad antes de generar contenido.

**Entradas obligatorias**
- GSDLC-07 CLOSED/PASS
- PRE_CODE_READY

**Actividades**
1. Definir Milestone, Epic, Story, Sprint, Dependency y PlanningState schemas.
2. Definir IDs estables, lifecycle y ownership por rol.
3. Vincular requirements, risks, ADRs y test intent.
4. Implementar dependency graph con cycle detection.
5. Definir planning approval/freeze semantics.

**Entregables verificables**
- planning schemas
- PlanningState
- dependency graph service

**Pruebas / validadores**
- schema
- duplicate ID
- cycle detection
- orphan trace link

**Evidencia mínima**
- planning_contract_report.json

**Seguridad operacional específica**
- agent generation nunca bypassa approval
- no code mutation en planning

**PASS**
- entities versionables y trazables
- dependency graph válido

**BLOCK**
- orphan story
- cycle
- ID collision

**Salida / autorización**
- autoriza GSDLC-08-B


### GSDLC-08-B — Roadmap authoring/generation/review

**Objetivo.** Crear roadmap desde requirements aprobados por ruta manual/import/agent.

**Entradas obligatorias**
- GSDLC-08-A PASS

**Actividades**
1. Crear Roadmap Workbench y StepActionAdvisor específico.
2. Permitir manual, paste/import y agent-assisted generation.
3. Definir milestones, outcomes, dependencies y exit criteria.
4. Calcular requirement/risk coverage y findings.
5. Review, RBAC approval y freeze del roadmap.

**Entregables verificables**
- RoadmapWorkbench
- roadmap schema/validator bindings

**Pruebas / validadores**
- coverage fixtures
- browser editor
- agent structured output
- role approval

**Evidencia mínima**
- roadmap_coverage.json
- roadmap approval record

**Seguridad operacional específica**
- draft only before approval
- no hidden auto-prioritization

**PASS**
- roadmap cubre scope obligatorio
- findings visibles

**BLOCK**
- critical requirement omitido sin finding
- agent output auto-approved

**Salida / autorización**
- autoriza GSDLC-08-C


### GSDLC-08-C — Backlog derivation and prioritization

**Objetivo.** Derivar epics/stories con cobertura y prioridad explicables.

**Entradas obligatorias**
- GSDLC-08-B PASS

**Actividades**
1. Derivar o crear epics/stories.
2. Vincular acceptance criteria, requirements, ADRs, risks y test intent.
3. Aplicar priority/value/risk fields con racional.
4. Detectar unmapped requirements, duplicated stories y dependency gaps.
5. Review/approve/freeze backlog.

**Entregables verificables**
- BacklogWorkbench
- RequirementCoverageService

**Pruebas / validadores**
- 100% coverage fixtures
- duplicate/orphan negative
- priority schema

**Evidencia mínima**
- requirement_to_story_matrix.json
- backlog_validation_report.json

**Seguridad operacional específica**
- planning suggestions no ejecutan código
- role approval

**PASS**
- required traceability=100%
- unmapped blockers=0

**BLOCK**
- orphan requirement
- story sin acceptance criteria

**Salida / autorización**
- autoriza GSDLC-08-D


### GSDLC-08-D — Sprint planning, capacity and dependencies

**Objetivo.** Construir sprints ejecutables y no solo listas de historias.

**Entradas obligatorias**
- GSDLC-08-C PASS

**Actividades**
1. Seleccionar stories y capacity.
2. Validar prerequisite/dependency order.
3. Definir Definition of Ready/Done, test intent y risk focus.
4. Mostrar warnings de overcommit y unresolved blockers.
5. Solicitar approval product-owner/owner y freeze sprint.

**Entregables verificables**
- SprintPlanner
- SprintPlan schema
- capacity/dependency report

**Pruebas / validadores**
- dependency violation
- capacity warning
- blocked story scheduling
- role approval

**Evidencia mínima**
- sprint_plan.json
- dependency_check.json

**Seguridad operacional específica**
- no runtime action todavía
- sprint approval role-bound

**PASS**
- sprint ordered y executable
- all selected stories READY

**BLOCK**
- story scheduled before prerequisite
- blocked story silently included

**Salida / autorización**
- autoriza GSDLC-08-E


### GSDLC-08-E — Planning traceability and Project Status browser closure

**Objetivo.** Integrar planning en el wizard y demostrarlo en navegador.

**Entradas obligatorias**
- GSDLC-08-D PASS

**Actividades**
1. Mover Project Status PRE_CODE_READY→PLANNING→IMPLEMENTING_READY.
2. Mostrar graph requirement→milestone→epic→story→sprint.
3. Integrar StepActionAdvisor en planning.
4. Ejecutar browser roadmap→backlog→sprint.
5. Verificar manual/import/agent choices y freeze.

**Entregables verificables**
- Planning UI
- traceability graph
- browser acceptance

**Pruebas / validadores**
- browser full planning
- traceability 100%
- state transitions
- accessibility

**Evidencia mínima**
- screenshots
- trace graph export
- approval records

**Seguridad operacional específica**
- no direct source/code writes
- roles respected

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- UI-complete planning
- mandatory CLI bridge=0
- S0/S1=0

**BLOCK**
- planning state contradicts files
- requirement coverage incomplete

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-09


## 7. Alcance transversal específico de esta ola

- Planning artifacts son del workspace seleccionado; no deben confundirse con el roadmap canónico de DevPilot salvo que DevPilot sea el workspace.
- Todos los modos de autoría comparten el mismo schema/gates.

## 8. Política de contratos históricos específica

- Tests históricos de `docs/00_product/product_roadmap.md` y backlogs DevPilot deben scopearse al repo DevPilot; no deben considerar cualquier workspace roadmap como fuente canónica de DevPilot.

Antes del cierre de **cada** micro-sprint se debe generar un `historical_contract_sweep` que clasifique los tests/contratos impactados como:

1. `historical-freeze`: valida únicamente el hecho histórico;
2. `current-active`: debe evolucionar con la capacidad vigente;
3. `successor-needed`: requiere nuevo contrato sin reescribir el anterior;
4. `deprecated-after-proof`: solo puede retirarse después de demostrar reemplazo equivalente.

No se permite modificar una aserción histórica únicamente para “hacer pasar pytest”; la modificación debe quedar justificada por esta clasificación.

### Contract Reconciliation Sweep obligatorio

La política `docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md`, materializada durante GSDLC-03-E, es transversal para esta ola.

Además del `historical_contract_sweep` de cada micro-sprint, antes de la full regression de cierre debe ejecutarse un `contract_reconciliation_sweep` que bloquee si detecta cualquiera de estas condiciones:

1. schema estricto inválido o metadata `current-active` contradictoria;
2. summary/counter/registry derivado desincronizado de su colección viva;
3. sensitive action sin RBAC/approval/MIASI/tool binding cuando aplique;
4. UI route/capability sin mapping current correspondiente;
5. `source_registry`, Project State, README, roadmap o CURRENT en estados incompatibles;
6. test histórico consultando un `current-active` mutable cuando existe snapshot `*_at_close`;
7. reutilización de un puntero histórico por otra ola;
8. fixture/sandbox que copie stores `runtime-ephemeral`, incluidos `auth.db*`, `devpilot.db*` o equivalentes;
9. evidencia sellada reescrita después de calcular su hash;
10. contrato successor agregado sin actualizar el historial/registry que deba reconocerlo.

La clasificación mínima continúa siendo `historical-freeze`, `current-active`, `successor-needed` y `deprecated-after-proof`; se añade la distinción explícita `derived` y `runtime-ephemeral`.

**Regla:** corregir drift determinista antes de consumir la única full regression del backlog.

## 9. Seguridad operacional específica

- Planning no ejecuta instalaciones/código.
- Approval de roadmap/backlog/sprint por roles configurados.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- planning schemas
- coverage
- dependency graph
- state transitions
- browser

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- roadmap/backlog/sprint artifacts
- coverage reports
- approvals
- screenshots

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- roadmap/backlog/sprints desde UI
- 100% required coverage
- approved sprint
- Project Status actualizado

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-09 solo con sprint approved que contenga al menos una story READY.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

