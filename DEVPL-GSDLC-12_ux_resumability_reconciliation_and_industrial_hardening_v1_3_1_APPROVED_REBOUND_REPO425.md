---
doc_id: "DEVPL-GSDLC-12"
title: "DEVPL-GSDLC-12 — UX, resumability, reconciliation and industrial hardening"
status: "approved"
version: "1.3.1"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner/rebound_repo425_after_GSDLC-11_windows_composite_closure"
program_id: "DEVPL-GSDLC"
source_repo: "repo_DevPilot_Local_425_DEVPL_GSDLC_11_E_CLEAN_INSTALL_BROWSER_RELEASE_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "b341370633e66355add6bb2611879b32f277ad0f"
source_repo_sha256: "d4a9cf4b3b8d544b71ee9b568e7ba3388cf39e74ce8d213d3b0e9f9d2946695d"
source_repo_role: "current-execution-source/GSDLC-11-E-windows-validated-composite-closure-successor"
canonical_product_baseline_repo: "repo_DevPilot_Local_425_DEVPL_GSDLC_11_E_CLEAN_INSTALL_BROWSER_RELEASE_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip"
canonical_product_baseline_commit: "b341370633e66355add6bb2611879b32f277ad0f"
canonical_product_baseline_sha256: "d4a9cf4b3b8d544b71ee9b568e7ba3388cf39e74ce8d213d3b0e9f9d2946695d"
canonical_product_baseline_role: "GSDLC-11-final-Windows-validated-composite-closure-baseline"
design_origin_repo: "repo_DevPilot_Local_341_POST_H_EVAL_002_PILOT_TRANSITION_REBIND.zip"
design_origin_commit: "cff43e8d992ff6139bd13bb1809ce4d497ae0952"
design_origin_sha256: "e28cd2bae08d099a2b62c4869c83b6e5a647f3f780ca1572727b7c80f6eeea3b"
execution_source_policy: "cumulative-successor-repo425; predecessor DEVPL-GSDLC-11 closed; never regress to historical design origin"
predecessor_backlog: "DEVPL-GSDLC-11/CLOSED-PASS-WINDOWS-VALIDATED-COMPOSITE-RECOVERY"
activation_requires_owner_adjudication: false
activation_mode: "absorbed-into-GSDLC-12-A/no-standalone-sprint-repo-operator"
local_first: true
ui_complete_normal_journey: true
dry_run_default: true
backlog_id: "DEVPL-GSDLC-12"
r01_research_binding: "CLOSED/PASS"
r01_research_authority_repo: "repo_DevPilot_Local_348_DEVPL_GSDLC_R01_E_RESEARCH_CLOSURE.zip"
r01_research_authority_commit: "3d7fda44d7ab5feefadd2eb4a7b9d20680eb1b5d"
r01_research_authority_sha256: "68487b2d210a0fd8fb6f2c46f2f70f205f925aeda7d556e13af205de4583515d"
r01_binding_scope: "architecture-and-security-input; historical design origin remains immutable"
backlog_status: "APPROVED/READY-FOR-GSDLC-12-A"
micro_sprints_total: 5
frx_execution_profile_id: "frx-v2.4-current"
frx_execution_profile_sha256: "2339df5fd79134fa8a675092e71ed71c8c11300b46747f055e86628e72679219"
validation_policy: "A-D cumulative-selective+TestImpact; no routine Full; E exactly-one-logical-Full unless already consumed by owner-approved hard trigger; no rerun after functional failure; composite recovery"
documentation_contract_policy: "DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED"
documentation_drift_policy: "bounded non-critical drift repaired in active/next micro-sprint; no standalone sprint/operator/repo"
runtime_ephemeral_fixture_policy: "exclude auth.db*, devpilot.db* and equivalent runtime stores"
---

# 0.0 Owner APPROVE, predecessor closure adjudication y execution rebind — 2026-09-12

Se adjudica reproduciblemente la entrada de DEVPL-GSDLC-12:

- `GSDLC-11-E = CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY`;
- `DEVPL-GSDLC-11 = CLOSED/PASS/WINDOWS-VALIDATED/COMPOSITE-RECOVERY`;
- successor canónico y fuente acumulativa: `repo_DevPilot_Local_425_DEVPL_GSDLC_11_E_CLEAN_INSTALL_BROWSER_RELEASE_CLOSURE_WINDOWS_VALIDATED_CANDIDATE.zip`;
- commit de cierre/promoción: `b341370633e66355add6bb2611879b32f277ad0f`;
- SHA-256 del successor: `d4a9cf4b3b8d544b71ee9b568e7ba3388cf39e74ce8d213d3b0e9f9d2946695d`;
- browser release acceptance de 11-E = `PASS/REAL-BROWSER`, una ejecución, sin replay por correctives que no modificaron la superficie demostrada;
- tag local `v0.1.1` annotated y exact-commit sobre `5e57bfd5670525981da77ac16ec3bf924cd187a4`, sin push/publish/deploy;
- única Full de GSDLC-11 = `1/1`, sesión `DEVPL-GSDLC-11-E-FULL-01-R1`, FAIL histórico preservado `3077 PASS / 65 FAIL / 0 ERROR / 5 SKIP / 3147 accounted (100%)`;
- recuperación compuesta = `65/65` exact failed-nodeid PASS + `93/93` bounded impacted PASS + Historical Regression Guard PASS + deterministic post-gates PASS;
- segunda Full de GSDLC-11 = `0`;
- S0/S1 abiertos = `0`;
- packaging final = `git-archive-exact-commit`, tracked-only, sin rutas prohibidas;
- Project State y Source Registry de repo425 declaran GSDLC-11 cerrado y GSDLC-12 autorizado.

La Full histórica de GSDLC-11 **no consume** el presupuesto de DEVPL-GSDLC-12. Este backlog comienza con su propio budget `0/1`, reservado para 12-E salvo hard trigger owner-approved; si un hard trigger consume esa única corrida antes de 12-E, 12-E queda obligado a cerrar con la evidencia de esa misma Full y, si falla, con recuperación compuesta selectiva. Nunca se autoriza una segunda Full.

## 0.0.1 Gap heredado que GSDLC-12 debe absorber sin reabrir GSDLC-11

La evidencia browser final de 11-E demuestra `Lifecycle RELEASED` y release closure hash-bound PASS, pero la vista agregada `Project Status` todavía puede mostrar `BLOCKED` por artefactos/MIASI/planning incompletos del fixture de aceptación. El cierre de 11-E lo trató correctamente como no autoritativo para el lifecycle release, pero **GSDLC-12 debe reconciliar esta divergencia UX/estado** para que un usuario no reciba mensajes contradictorios después de restart/recovery. Este gap se absorbe en 12-A/12-B como current-active reconciliation; no reescribe la evidencia sellada de 11-E ni crea un sprint administrativo separado.

## 0.0.2 Política operativa reforzada para GSDLC-12
 
1. La activación/rebind se integra en GSDLC-12-A; no crea sprint, repo u operador Windows independiente.
2. 12-A→12-D usan Test Impact, pruebas focales/acumulativas y gates determinísticos; `Full Regression = 0` por rutina.
3. 12-E consume exactamente una logical Full después de browser matrix, HCA/Contract Reconciliation, current-authority coherence, security/performance gates y preflight FRX current-active, salvo que un hard trigger owner-approved ya haya consumido ese único budget.
4. Un FAIL/ERROR funcional de la única Full se preserva inmutable; no hay rerun. Recuperación permitida: exact failed/error retest + bounded impacted retest + Historical Regression Guard + post-recovery gates + adjudicación composite.
5. Browser acceptance se ejecuta cuando el micro-sprint cambia UX o debe demostrar comportamiento; un corrective que no cambia la superficie demostrada reutiliza evidencia hash-bound y no repite browser.
6. Los operadores Windows deben ser pequeños, reentrantes, state-aware y derivar dependencias/runtime del contrato vigente. No deben depender de cwd, `git common-dir`, semántica accidental de PowerShell ni nombres históricos de repos.
7. LF/CRLF nunca constituye autoridad de cambio. Comparar contenido Git o texto normalizado UTF-8/LF.
8. Runtime stores, secretos y caches no entran en fixtures ni packages finales.
9. API/UI, cuando se necesiten, se ejecutan foreground y en consolas separadas; nunca background.
10. Cualquier mutación sensible exige `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`.


# 0. Política de binding de ejecución

Este backlog conserva el baseline histórico únicamente en los campos `design_origin_*`. El `source_repo` de esta versión rebound es repo425 y constituye la autoridad efectiva de ejecución. **No puede ejecutarse contra el baseline histórico congelado**.

La adjudicación reproducible requerida para activar DEVPL-GSDLC-12 **ya fue satisfecha** por el cierre Windows composite de GSDLC-11 y por este APPROVE owner. Debe verificarse antes de cualquier mutación:

- `DEVPL-GSDLC-11 = CLOSED/PASS`;
- successor repo + Git commit + SHA-256 del backlog predecessor;
- owner adjudication del micro-sprint de cierre y del backlog;
- rebind de Project State / Source Registry / README / roadmap al successor predecessor.

El origen de diseño histórico se conserva en `design_origin_repo/commit/sha256`; la autoridad efectiva de ejecución es repo425 y sus successors acumulativos, conforme a `execution_source_policy`.

No está permitido volver a repo341, repo420 ni a otro parent histórico para “simplificar” implementación. La evolución es acumulativa y parte de repo425.

## 0.1 Invariantes heredadas

1. La navegación project-scoped solo opera con proyecto activado por el journey GSDLC-03.
2. La sesión/RBAC/approval server-side sigue siendo autoridad; storage browser es UX-only.
3. Stores `runtime-ephemeral` (`auth.db*`, `devpilot.db*`, etc.) no se copian a fixtures/sandboxes.
4. Mutaciones son typed operations gobernadas; no arbitrary shell.
5. Los contratos históricos se preservan como hechos scoped y evolucionan mediante successors.
6. El backlog debe incorporar cualquier adjudicación externa del predecessor antes de cambios funcionales.


# DEVPL-GSDLC-12 — UX, resumability, reconciliation and industrial hardening

## 1. Objetivo

Endurecer el producto completo para reinicios, conflictos Git, accesibilidad, performance, permisos, seguridad y recuperación.

## 2. Invariante de producto que esta ola debe demostrar

> Un usuario puede cerrar/reabrir DevPilot, cambiar branch o editar externamente y la aplicación recupera contexto, explica conflictos y conserva gobernanza sin perder trabajo.

Esta invariante es parte del criterio de cierre. No basta con que existan clases, endpoints o archivos: debe demostrarse el comportamiento de producto descrito.

## 3. Dependencias y precondiciones de entrada

- GSDLC-11 CLOSED/PASS

Si alguna precondición no puede verificarse de forma reproducible, el backlog entra en `BLOCK` antes de mutar source.

Precondición transversal adicional: debe existir un proyecto activo/server-validado proveniente del journey GSDLC-03 para toda superficie project-scoped; Settings/Account globales no sustituyen project context.

## 4. Alcance funcional y técnico

### 4.1 Incluido

- durable workflow resume
- locks
- crash recovery
- branch/external edits
- Guided/Expert
- accessibility/help
- performance
- security red-team
- full browser matrix

### 4.2 Fuera de alcance

- enterprise deployment
- cloud multi-tenant

## 5. Superficies y fuentes que probablemente serán afectadas

- all Guided SDLC/UI subsystems

La lista es orientativa para Test Impact. Cada micro-sprint debe cerrar su manifest exacto antes de ejecutar cambios.

## 6. Micro-sprints secuenciales

### GSDLC-12-A — Persistent resumability, crash/restart recovery and locks

**Objetivo.** Hacer durable el workflow completo frente a cierres y fallos.

**Entradas obligatorias**
- GSDLC-11 CLOSED/PASS

**Actividades**
1. Checkpoint engineering state y correlación runtime.
2. Recuperar drafts, current step y pending safe work tras restart.
3. Implementar locks/stale lock recovery por workspace/action.
4. Reconciliar jobs/approvals interrumpidos.
5. Requerir nueva confirmación para cualquier sensitive action no completada.

**Entregables verificables**
- ResumeService
- WorkspaceLockService
- RecoveryView

**Pruebas / validadores**
- kill/restart
- stale lock
- duplicate execution negative
- draft recovery

**Evidencia mínima**
- resume_matrix.json
- recovery traces

**Seguridad operacional específica**
- no auto-resume mutable operation without revalidation
- lock ownership by session/actor

**PASS**
- restart returns safe reproducible state
- no duplicate side effects

**BLOCK**
- duplicate mutation
- lost draft
- stale approval auto-used

**Salida / autorización**
- autoriza GSDLC-12-B


### GSDLC-12-B — Branch/external edit reconciliation and conflict UX

**Objetivo.** Resolver drift entre Git/filesystem y engineering state sin acciones destructivas.

**Entradas obligatorias**
- GSDLC-12-A PASS

**Actividades**
1. Detect branch switch/head divergence/rewind.
2. Detect external edits/renames/deletes.
3. Represent conflict/revalidation states en Project Status.
4. Ofrecer review and safe recovery plans.
5. Prohibir reset-hard/rebase automáticos.

**Entregables verificables**
- ConflictResolutionView
- advanced reconciliation report

**Pruebas / validadores**
- branch fixtures
- dirty worktree
- renames/deletes
- divergent commit

**Evidencia mínima**
- conflict_matrix.json
- screenshots

**Seguridad operacional específica**
- no data loss
- no auto-destructive Git

**PASS**
- all drift leads to explicit state
- user can recover safely

**BLOCK**
- silent overwrite
- hidden destructive Git

**Salida / autorización**
- autoriza GSDLC-12-C


### GSDLC-12-C — Guided vs Expert modes, accessibility and help

**Objetivo.** Hacer usable el producto para personal no experto sin debilitar controles para expertos.

**Entradas obligatorias**
- GSDLC-12-B PASS

**Actividades**
1. Implementar Guided mode con progressive disclosure y next-action focus.
2. Implementar Expert mode con vistas transversales y diagnostics.
3. Agregar contextual help, glossary, recovery instructions y plain+technical error messages.
4. Mejorar keyboard navigation, ARIA, focus management y responsive layout.
5. Ejecutar usability scripts con usuario no técnico.

**Entregables verificables**
- GuidedMode
- ExpertMode
- HelpSystem
- accessibility report

**Pruebas / validadores**
- WCAG-oriented automated/manual checks
- navigation
- mode policy parity
- usability task completion

**Evidencia mínima**
- a11y_report.json
- usability_session_report.md

**Seguridad operacional específica**
- Expert mode no bypasses server policies
- help no expone secretos

**PASS**
- no-tech scripted journey complete
- same policies both modes

**BLOCK**
- Expert mode grants extra unauthorized action
- critical a11y blockers

**Salida / autorización**
- autoriza GSDLC-12-D


### GSDLC-12-D — Performance, security red-team and resource/cost hardening

**Objetivo.** Someter el producto a cargas, ataques y abuso de recursos realistas.

**Entradas obligatorias**
- GSDLC-12-C PASS

**Actividades**
1. Test large repo/docs performance and UI responsiveness.
2. Red-team auth/session/CSRF/RBAC/approval.
3. Test upload/path/prompt/tool injection.
4. Test job/resource exhaustion and model budget abuse.
5. Test dependency-install supply-chain protections.
6. Ejecutar red-team R01 específico: model-route→tool escalation, forbidden-tool intent (`filesystem.delete`), autonomous recovery after tool error, hidden external fallback, stale provider evidence, consumer-session piggyback y real MCP/write attempt.
7. Verificar que Guided y Expert mode, incluido AI Control Center, aplican la misma autoridad server-side.

**Entregables verificables**
- industrial_hardening_report
- performance_budget
- red-team findings

**Pruebas / validadores**
- security negative suites
- load/perf
- resource ceilings
- cost hard stops
- model-route/tool-permission separation negatives
- provider freshness/fallback negatives
- MCP/write-capability negatives

**Evidencia mínima**
- red_team_report.json
- performance_results.json

**Seguridad operacional específica**
- S0/S1=0 mandatory
- no real harmful package/provider use

**PASS**
- critical threats blocked
- budgets met or justified

**BLOCK**
- auth/RBAC bypass
- path escape
- unbounded spend
- critical exploit

**Salida / autorización**
- autoriza GSDLC-12-E


### GSDLC-12-E — Full browser matrix, full regression and local release candidate

**Objetivo.** Cerrar la macro-evolución con evidencia completa antes de tocar el piloto.

**Entradas obligatorias**
- GSDLC-12-D PASS

**Actividades**
1. Ejecutar browser matrix de login, Home, Project Status, pre-code, AI Control Center, planning, story, quality, release y roles.
2. Ejecutar full DevPilot regression una sola vez tras estabilización.
3. Ejecutar clean-install/smoke del producto.
4. Validar docs governance, Project State, TCR y historical contract migration.
5. Generar RC autoritativo y adjudicación.

**Entregables verificables**
- GSDLC local RC
- browser matrix
- full regression evidence
- RC manifest

**Pruebas / validadores**
- full pytest
- browser real
- install smoke
- docs/TCR/project-state

**Evidencia mínima**
- full_regression.log
- browser_evidence.zip
- RC SHA/commit

**Seguridad operacional específica**
- credentials/tokens redacted
- no stale runtime artifacts

**Cierre de regresión obligatorio**
- ejecutar gates baratos + Contract Reconciliation Sweep + browser/capability acceptance;
- consumir la única full regression del backlog exactamente una vez, salvo que un hard-trigger anterior ya haya consumido esa corrida;
- ante FAIL no repetir full: aplicar recuperación compuesta selectiva y Historical Regression Guard.

**PASS**
- CLOSED/PASS
- S0=0
- S1=0
- UI-complete journey proven

**BLOCK**
- critical regression
- normal journey still needs external operator
- historical contract false blocker unresolved

**Salida / autorización**
- autoriza GSDLC-13


## 7. Alcance transversal específico de esta ola

- Esta ola prioriza calidad industrial y no añade nuevas capacidades salvo fixes requeridos.
- Guided journey acceptance incluye perfiles no expertos.

## 8. Política de contratos históricos específica

- Historical route-count/UI snapshots se congelan en UOC; no pueden bloquear nuevas rutas/navegación.
- Full regression se concentra aquí para evitar repetirla durante cada ola.

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

- Red-team cubre auth/RBAC, uploads, filesystem, Git, model/tool injection, cost abuse y supply chain.
- Debe demostrar expresamente que un `ModelRouteDecision` no puede producir `ToolExecutionDecision`, que external routes no se habilitan por fallback silencioso y que la policy determinista bloquea tool intents prohibidos aunque el modelo los seleccione.

Toda acción mutante debe seguir `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`. Cualquier excepción requiere ADR o backlog correctivo separado.

## 10. Estrategia de pruebas de la ola

- recovery
- conflict
- accessibility
- performance/security
- R01 agentic/provider escalation negatives
- full regression
- full browser

Regla de regresión:

- A→D usan Test Impact, pruebas focales, acumulativas y validadores determinísticos; **full regression = NO por rutina**.
- El micro-sprint E ejecuta la **única full regression del backlog exactamente una vez**, después de gates baratos, Contract Reconciliation Sweep y browser/capability acceptance pertinente.
- Una full intermedia solo puede ocurrir por hard trigger de riesgo explícito, owner-approved y documentado; si ocurre, **consume la única corrida full permitida** y E debe cerrar mediante evidencia compuesta sin lanzar otra.
- Si la full falla: preservar log/JUnit/marker inmutables, prohibir rerun, diagnosticar causa, ejecutar exact failed-nodeid retest + bounded impacted retest + Historical Regression Guard y cerrar solo con `composite-full-regression-selective-retest = PASS`.
- Browser acceptance se ejecuta únicamente cuando el micro-sprint introduce/cierra UX; no se repite por correctives que no cambian comportamiento browser demostrado.

## 11. Evidencia autoritativa esperada

- recovery matrix
- red-team report
- browser matrix
- full regression log
- RC manifest

Además, cada micro-sprint debe conservar:

- manifest de source delta;
- identidad Git pre/post;
- resultados PASS/BLOCK machine-readable;
- lista de S0/S1;
- browser screenshots cuando corresponda;
- hashes de artefactos empaquetados;
- declaración explícita `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 12. Definition of Done del backlog

- resumability
- a11y
- security/performance
- full regression/browser PASS

El backlog solo puede adjudicarse `CLOSED/PASS` si todos los micro-sprints A→E han cerrado en secuencia y no quedan S0/S1 abiertos.

## 13. Criterio de autorización del siguiente backlog

- GSDLC-13 solo desde RC autoritativo.

Un `PASS-WITH-GAPS` solo puede autorizar el siguiente backlog cuando los gaps estén clasificados S2/S3, tengan owner, evidencia y no invaliden la invariante de producto de esta ola.


## 0.0.3 GSDLC-12-A Windows closure adjudication

- `GSDLC-12-A = CLOSED/PASS/WINDOWS-VALIDATED`; browser restart/recovery acceptance = PASS/1.
- Durable checkpoint/lock authority remains server-side metadata-only; no runtime DB snapshot or browser authority.
- S0/S1 = 0; Full Regression in 12-A = 0; GSDLC-12 budget remains 0/1 reserved for 12-E.
- Successor: `repo_DevPilot_Local_426_DEVPL_GSDLC_12_A_PERSISTENT_RESUMABILITY_RECOVERY_LOCKS_WINDOWS_VALIDATED_CANDIDATE.zip`.
- `GSDLC-12-B` is authorized after this Windows PASS.
