---
doc_id: "DEVPL-GSDLC-10"
title: "DEVPL-GSDLC-10 — Integrated Quality, Tests, Git and Evidence workflow"
status: "approved"
version: "1.4.2"
owner: "Ordóñez"
updated: "2026-09-09"
approval: "approved_by_owner/rebound_repo417_after_GSDLC-10-B-corrective-104"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_417_DEVPL_GSDLC_10_B_JOB_CONSOLE_LIVE_REFRESH_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "e8560099596f5d8d006ef37786f60abedb32acf9"
source_repo_sha256: "ca26d91a2f38a4bbdf17a9b68fd1a8894c0545479973ffabfd08bb9156b915bf"
source_repo_role: "current-execution-source/GSDLC-10-B-windows-validated-successor-corrective-104"
canonical_product_baseline_repo: "repo_DevPilot_Local_413_DEVPL_GSDLC_09_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip"
canonical_product_baseline_commit: "b27f50c1747cae3462e6d689fa00bfd1b8ead6c9"
canonical_product_baseline_sha256: "61a7753ff4d87947b34112aa8aef33902a5e3ee6380ba2c4f003fb542ab6a3fb"
canonical_product_baseline_role: "GSDLC-09-final-functional-closure-baseline"
design_origin_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_origin_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_origin_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
execution_source_policy: "cumulative-successor-repo417; preserve repo416/repo415/repo414/repo413 as predecessor history; never regress execution source"
predecessor_backlog: "DEVPL-GSDLC-09/CLOSED-PASS-WINDOWS-VALIDATED-COMPOSITE-RECOVERY"
activation_requires_owner_adjudication: false
activation_mode: "integrated-into-GSDLC-10-A/no-standalone-repo"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-10"
r01_research_binding: "CLOSED/PASS"
r01_research_authority_repo: "repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip"
r01_research_authority_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"
r01_research_authority_sha256: "68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d"
r01_binding_scope: "architecture-and-security-input; historical design origin remains unchanged"
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
backlog_status: "APPROVED/ACTIVE/GSDLC-10-C"
micro_sprints_total: 5
validation_policy: "A-D cumulative-selective+TestImpact, no routine Full; E exactly-one-logical-Full; no rerun after functional failure; composite recovery"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
documentation_drift_policy: "bounded non-critical drift repaired in active/next micro-sprint; no standalone sprint/operator/repo"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
---
# 0.0 Owner APPROVE, predecessor adjudication y execution rebind — 2026-09-09

`GSDLC-09-E = CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY` y `DEVPL-GSDLC-09 = CLOSED/PASS/WINDOWS-VALIDATED` quedan adjudicados como predecessor de esta ola.

La fuente acumulativa que debe usarse físicamente para no perder ningún cambio es `repo_DevPilot_Local_414_DEVPL_GSDLC_09_FINAL_AUTHORITY_POINTERS_WINDOWS_VALIDATED_CANDIDATE.zip` / commit `adccda6a8fe296a96511bc313be5b883dad32767` / SHA-256 `1ab8b2d38a243ae04caffbf3cd62360c6e613eda3f181cb9d5210b25d549bfe3`. Repo414 contiene únicamente la última conciliación de dos punteros current-authority. El **baseline funcional canónico** de cierre de GSDLC-09 continúa siendo `repo_DevPilot_Local_413_DEVPL_GSDLC_09_FINAL_CLOSURE_RECONCILIATION_WINDOWS_VALIDATED_CANDIDATE.zip` / commit `b27f50c1747cae3462e6d689fa00bfd1b8ead6c9` / SHA-256 `61a7753ff4d87947b34112aa8aef33902a5e3ee6380ba2c4f003fb542ab6a3fb`.

Por tanto:

- repo414 = execution source acumulativo de GSDLC-10;
- repo413 = canonical product baseline del predecessor;
- no se permite iniciar desde repo413 ignorando el delta administrativo ya Windows-validado de repo414;
- tampoco se debe crear un repo/operator independiente por cada drift documental menor.

La activation/rebind inicial de GSDLC-10 se ejecuta como fase inicial del micro-sprint 10-A y queda absorbida en el mismo source delta, commit, bundle Windows y evidencia de 10-A. No es un micro-sprint separado.

## 0.0.1 Política de drift documental proporcional

Cuando se detecte drift documental/current-state durante GSDLC-10:

- si es puntual y no rompe seguridad, permisos, authority binding, evidencia sellada, trazabilidad requerida por DoD, integridad Git ni la invariante funcional de la ola, se corrige dentro del micro-sprint activo o del siguiente micro-sprint natural;
- no se monta por sí solo un sprint, operador Windows ni successor repo;
- si sí rompe una de esas invariantes críticas, puede bloquear y exigir corrective explícito con justificación.

## 0.0.2 Política de regresión current-active

- 10-A→10-D: full regression = **0** por rutina; Test Impact + focal + bounded cumulative + Historical Contract Authority/Contract Reconciliation proporcional.
- 10-E: exactamente una logical Full del backlog, salvo hard-trigger previo owner-approved que ya haya consumido el único budget.
- El operador no configura planner/max_nodeids/workers/nodeid transport; invoca el `FullRegressionExecutionProfile` current-active.
- FAIL/ERROR funcional: preservar la Full original; **no rerun**; exact failed/error retest + bounded impacted retest + Historical Regression Guard + post-recovery gates + composite adjudication.
- Interrupción de infraestructura: resume únicamente la misma logical session y solo `UNEXECUTED`.

## 0.0.3 Rebind GSDLC-10-B — repo415

GSDLC-10-A quedó `CLOSED/PASS/WINDOWS-VALIDATED`; GSDLC-10-B se ejecuta acumulativamente sobre repo415 / commit `ca3fadb3febf12fa5b405712d5611bbd96d7905f` / SHA-256 `39e83d8d55434f3201597cac41196c862d241bc1219a2b05d24be3000c5cd910`.

FRX v2.4 A/B permanece current-active: drift documental no crítico se absorbe en el micro-sprint activo/siguiente; Full Regression = 0 en 10-B y solo 10-E consume ordinariamente la única logical Full del backlog.


## 0.0.4 Rebind GSDLC-10-C — repo417

GSDLC-10-B quedó `CLOSED/PASS/WINDOWS-VALIDATED/CORRECTIVE-104`; GSDLC-10-C se ejecuta acumulativamente sobre `repo_DevPilot_Local_417_DEVPL_GSDLC_10_B_JOB_CONSOLE_LIVE_REFRESH_WINDOWS_VALIDATED_CANDIDATE.zip` / commit `e8560099596f5d8d006ef37786f60abedb32acf9` / SHA-256 `ca26d91a2f38a4bbdf17a9b68fd1a8894c0545479973ffabfd08bb9156b915bf`.

FRX v2.4 A/B continúa current-active: drift determinista/current-active se reconcilia antes de validación, drift documental no crítico se absorbe proporcionalmente dentro del micro-sprint, y GSDLC-10-C consume `Full Regression = 0`. El único budget ordinario de Full de DEVPL-GSDLC-10 permanece reservado para 10-E.

# 0. Política de binding de ejecución

Este backlog conserva como **origen de diseño** el baseline histórico desde el que fue redactado, pero **no puede ejecutarse contra ese baseline congelado**.

Antes de cualquier mutación de DEVPL-GSDLC-10 debe existir una adjudicación reproducible:

- `DEVPL-GSDLC-09 = CLOSED/PASS`;
- successor repo + Git commit + SHA-256 del backlog predecessor;
- owner adjudication del micro-sprint de cierre y del backlog;
- rebind de Project State / Source Registry / README / roadmap al successor predecessor.

El `source_repo` de frontmatter se conserva únicamente como `design-origin`; la autoridad efectiva se resuelve en la activación del backlog mediante `execution_source_policy = predecessor-owner-adjudicated-successor`.

No está permitido volver a repo341 o a otro parent histórico para “simplificar” implementación. La evolución es acumulativa.

## 0.1 Invariantes heredadas

1. La navegación project-scoped solo opera con proyecto activado por el journey GSDLC-03.
2. La sesión/RBAC/approval server-side sigue siendo autoridad; storage browser es UX-only.
3. Stores `runtime-ephemeral` (`auth.db*`, `devpilot.db*`, etc.) no se copian a fixtures/sandboxes.
4. Mutaciones son typed operations gobernadas; no arbitrary shell.
5. Los contratos históricos se preservan como hechos scoped y evolucionan mediante successors.
6. El backlog debe incorporar cualquier adjudicación externa del predecessor antes de cambios funcionales.


# DEVPL-GSDLC-10 — Integrated Quality, Tests, Git and Evidence workflow

## 1. Objetivo

Completar el ciclo de historia con Test Impact, jobs, quality remediation, stage/commit RBAC y evidence correlacionada.

## 2. Invariante de producto que esta ola debe demostrar

> Desde Story Workbench el usuario pulsa `Validar`; DevPilot propone pruebas, ejecuta jobs, muestra fallos, permite corregir, obtiene Quality PASS y ofrece commit gobernado.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-09 CLOSED/PASS

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- Test Impact UI
- test/build/lint jobs
- logs
- Quality Gate
- review/remediation
- stage/commit
- traceability/evidence

### 4.2 Fuera de alcance

- force push
- rebase/reset-hard
- deploy
  
## 5. Superficies y fuentes que probablemente serán afectadas

- Test Impact
- Job Console
- Quality
- Git governed ops
- Evidence Graph

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-10-A — Test Impact and test contract UI-native workflow

**Objetivo.** Determinar pruebas requeridas a partir del delta real de la story.

**Entradas obligatorias**
- GSDLC-09 CLOSED/PASS
- story CHANGES_READY

**Actividades**
1. Ejecutar Test Impact v2 sobre changed paths.
2. Mostrar matched contracts/rules, required/recommended tests y full-regression signal.
3. Permitir review/approval de test plan y waiver solo si política lo permite.
4. Escalar unknown/sensitive impact.
5. Vincular test plan a story/change plan hash.

**Entregables verificables**
- TestImpactPanel
- StoryTestPlan

**Pruebas / validadores**
- impact fixtures
- unknown path escalation
- sensitive delta
- waiver expiry

**Evidencia mínima**
- test_impact_report.json
- story_test_plan.json

**Seguridad operacional específica**
- no free-form test command from user
- waiver role-bound

**PASS**
- recommended tests explainable
- under-testing sensitive change blocked

**BLOCK**
- required test omitted silently
- unsafe command

**Salida / autorización**
- autoriza GSDLC-10-B


### GSDLC-10-B — Governed test/build/lint jobs and live logs

**Objetivo.** Ejecutar validaciones como jobs tipados con lifecycle observable.

**Entradas obligatorias**
- GSDLC-10-A PASS

**Actividades**
1. Start/cancel/retry approved test/build/lint jobs.
2. Capture bounded sanitized logs and structured result.
3. Support JUnit/artifact references.
4. Enforce timeout/resource limits and process-tree cancellation.
5. Reconcile orphan jobs after restart.

**Entregables verificables**
- StoryValidationJobs
- live logs UI
- structured job result

**Pruebas / validadores**
- job lifecycle
- cancel tree
- timeout
- log redaction
- orphan recovery

**Evidencia mínima**
- job logs
- job_results.json

**Seguridad operacional específica**
- command allowlist
- no arbitrary shell
- resource ceiling

**PASS**
- all required jobs PASS or actionable FAIL
- logs redacted

**BLOCK**
- job escapes contract
- secret in log
- orphan process

**Salida / autorización**
- autoriza GSDLC-10-C


### GSDLC-10-C — Quality Gate and remediation loop

**Objetivo.** Integrar findings→fix→retest hasta COMMIT_READY.

**Entradas obligatorias**
- GSDLC-10-B PASS/FAIL controlled

**Actividades**
1. Aggregate tests, review, security, traceability and policy findings.
2. Show blockers by severity and source.
3. Offer manual/agent remediation through StepActionAdvisor.
3a. Agent remediation produce proposal/`ToolIntent`; Quality Gate, PolicyEngine, RBAC y approval producen la decisión ejecutable. Model/provider routing nunca puede conceder waiver ni permiso Git.
4. Rerun only impacted validations when safe.
5. Produce deterministic Quality decision.

**Entregables verificables**
- StoryQualityGate
- RemediationLoop

**Pruebas / validadores**
- false-PASS negatives
- waiver rules
- retest scope
- agent remediation policy
- route/tool/waiver authority separation

**Evidencia mínima**
- story_quality_report.json
- remediation_trace.json

**Seguridad operacional específica**
- S0/S1 cannot be waived by agent
- waivers have role+expiry
- model/agent route cannot create, approve or widen a waiver

**PASS**
- blockers=0 before COMMIT_READY

**BLOCK**
- commit-ready with failed required test
- critical finding waived improperly

**Salida / autorización**
- autoriza GSDLC-10-D


### GSDLC-10-D — RBAC-governed stage and commit with traceability

**Objetivo.** Cerrar la story con un commit exacto y auditable.

**Entradas obligatorias**
- GSDLC-10-C PASS
- COMMIT_READY

**Actividades**
1. Build exact staging plan from approved change set.
2. Require approval according to Git policy/role.
3. Suggest/edit commit message.
3a. Un agente puede sugerir mensaje/plan, pero `ToolIntent` de Git debe resolverse por Git policy/RBAC; ninguna selección de modelo habilita stage/commit.
4. Bind requirement/story/tests/quality/evidence IDs to commit record.
5. Stage exact paths, commit and verify worktree clean.

**Entregables verificables**
- CommitPlan
- GitCommitRecord
- traceability payload

**Pruebas / validadores**
- exact staging
- wrong role
- dirty unexpected
- commit identity/message

**Evidencia mínima**
- staging_manifest.json
- commit_record.json
- Git hash

**Seguridad operacional específica**
- no force push/rebase/reset-hard
- no unapproved file staging

**PASS**
- commit exact approved delta
- repo clean

**BLOCK**
- unexpected file staged
- unauthorized role commits

**Salida / autorización**
- autoriza GSDLC-10-E


### GSDLC-10-E — End-to-end story cycle browser closure

**Objetivo.** Demostrar planning→code→tests→quality→commit desde UI.

**Entradas obligatorias**
- GSDLC-10-D PASS

**Actividades**
1. Ejecutar fixture story end-to-end.
2. Inyectar un fallo de test y completar remediation.
3. Commit final governed.
4. Verify trace graph requirement→story→files→tests→quality→commit.
5. Advance Project Status to next story/sprint.

**Entregables verificables**
- story_cycle_e2e_report
- trace graph

**Pruebas / validadores**
- real browser
- Git
- traceability
- agent remediation ToolIntent/ToolExecutionDecision parity
- focal regression

**Evidencia mínima**
- screenshots
- trace graph
- commit hash
- job/quality artifacts

**Seguridad operacional específica**
- redacted evidence
- no operator project writes

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- one complete story zero-PowerShell
- S0/S1=0

**BLOCK**
- external operator performs code/test/commit
- traceability broken

**Salida / autorización**
- CLOSED/PASS
- autoriza GSDLC-11


## 7. Alcance transversal específico de esta ola

- GSDLC-10 es el milestone donde una story completa se vuelve UI-native.
- CLI queda para automatización/diagnóstico, no required normal journey.

## 8. Política de contratos históricos específica

- UOC-006 restricciones Git destructivas siguen no-go.
- POST-H-029 testing tiers/full-regression logic se reutiliza; no se reemplaza por test commands ad hoc.

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

- Command allowlists, log redaction, Git exact staging, RBAC, waiver governance.
- R01 boundary: Model Gateway no posee Quality/Git authority; Agent Runtime no puede auto-waive ni auto-commit.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- impact
- jobs
- quality gate
- Git stage/commit
- traceability
- browser E2E

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- impact report
- job artifacts
- quality report
- commit record
- trace graph

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 11.1 Regla operativa de entregables por micro-sprint

Cada micro-sprint A→E debe producir, como corresponda al impacto real: source delta manifest; implementation report; tests focales/acumulativos; Test Impact; historical/contract reconciliation; Git pre/post identity; evidence machine-readable; Windows validation bundle; ZIP de repo completo limpio y ZIP de components después de PASS Windows; SHA-256; guía única Windows; riesgos/limitaciones; S0/S1; y commit sugerido/real. El operador debe ser pequeño, reentrante y no validar dependencias o superficies ajenas al delta.

No incluir en ZIP final `.git/`, `.venv/`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`, ni `.devpilot/devpilot.db`/runtime stores equivalentes.

## 12. Definition of Done del backlog

- story committed con tests+quality+evidence desde UI
- clean repo
- S0/S1=0

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-11 solo después de story E2E repetible.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.

