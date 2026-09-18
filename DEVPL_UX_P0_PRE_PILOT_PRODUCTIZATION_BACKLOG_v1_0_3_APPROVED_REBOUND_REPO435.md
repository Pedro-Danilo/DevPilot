---
doc_id: "DEVPL-UX-P0"
title: "DEVPL-UX-P0 — Pre-pilot frontend productization foundation"
status: "approved"
version: "1.0.3"
owner: "Ordóñez"
updated: "2026-09-17"
approval: "approved_by_owner"
source_repo: "repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_git_commit: "f1e4c5b8dc1882f7dc724ba87755cdd894f274c8"
source_repo_sha256: "3b07e305c1acf2980f9299d09a1f78c90f6420a070b9b57c3ad24d083fa32805"
requires_remote_sync: "DEVPL-POST-GSDLC-GIT-REMOTE-SYNC/PASS"
strategy_binding: "DEVPL_UI_UX_PRODUCTIZATION_STRATEGY_v1_0_0_APPROVED"
transition_binding: "DEVPL_POST_GSDLC_TRANSITION_DECISION_v1_0_0_APPROVED"
audit_binding: "DEVPL_UX_P0_FRONTEND_NAVIGATION_AUDIT_v1_0_0"
program_origin_repo: "repo_DevPilot_Local_430_DEVPL_GSDLC_12_E_LOCAL_RC_WINDOWS_VALIDATED_CANDIDATE.zip"
rebound_after_b_corrective: true
local_first: true
dry_run_default: true
micro_sprints_total: 5
full_regression_policy: "A-D selective/TestImpact only; E exactly one logical Full; functional FAIL preserved/no rerun/composite recovery"
---

# Owner approval — 2026-09-15

El owner aprueba este artefacto como autoridad operativa para DEVPL-UX-P0. Repo430 permanece inmutable; toda mutación inicia en su successor.

## Rebound operativo — 2026-09-15

UX-P0-B cerró mediante corrective Windows-validado sobre repo433. Este rebound preserva repo430 como origen histórico del programa y establece repo433 como baseline inmediato de ejecución para UX-P0-C. Debido a que el correctivo B consumió repo433, los successors operativos se desplazan: C→repo434, D→repo435 y E→repo436. La política de Full Regression no cambia.

## Rebound de cierre D — 2026-09-17

UX-P0-D está `CLOSED/PASS/WINDOWS-VALIDATED` sobre `repo_DevPilot_Local_435_DEVPL_UX_P0_D_CROSS_SURFACE_OPERATIONAL_PATTERNS_WINDOWS_VALIDATED_CANDIDATE.zip` (`f1e4c5b8dc1882f7dc724ba87755cdd894f274c8`, SHA-256 `3b07e305c1acf2980f9299d09a1f78c90f6420a070b9b57c3ad24d083fa32805`). UX-P0-E queda current-active y conserva el successor desplazado `repo436`. La única Full lógica del backlog sigue sin consumirse al iniciar E (`0/1`).

# DEVPL-UX-P0 — Pre-pilot frontend productization foundation

## 1. Objetivo

Elevar el frontend desde un conjunto de superficies funcionalmente completas hacia una experiencia transversal coherente y suficientemente productizada para que el siguiente piloto greenfield mida el valor de DevPilot y no la tolerancia del usuario frente a deuda UX.

UX-P0 es una fase **acotada**. No pretende alcanzar polish final ni rediseñar cada detalle.

## 2. Autoridad de entrada

- repo430 es immutable closure artifact de GSDLC-12;
- commit `a415504bbf021566243ef4000b1a27d4c8846fee`;
- SHA `969f7d6b...388a`;
- Git remote synchronization debe estar PASS antes del primer source mutation;
- los documentos de transición y estrategia UX están owner-approved;
- la primera mutación source ocurre en un successor de repo430, nunca en repo430.

## 3. Invariantes

1. Backend policy/RBAC/approval/tool/model authority no cambia por presentación.
2. Guided y Expert difieren en densidad y progressive disclosure, no en permisos.
3. Route IDs y paths existentes se preservan salvo successor contractual explícito; UX-P0 no necesita cambiarlos.
4. Browser storage nunca se convierte en execution authority.
5. Blockers críticos siempre son visibles.
6. Evidence pasa de dominante a disponible/progresiva, nunca se elimina.
7. No framework migration durante UX-P0.
8. No dependencia externa nueva salvo owner-approved hard need; preferir TypeScript/CSS actual.
9. Operadores Windows pequeños, state-aware, idempotentes; Python preferido.
10. LF/CRLF no es autoridad de cambio.

## 4. Métricas baseline

- main routes: 23;
- unique UI route IDs incluyendo auth: 25;
- operational registry routes: 22;
- Guided core paths: 12;
- explicit guided next-action copy: 11/23 rutas;
- `styles.css`: 1359 líneas;
- unique hard-coded hex values: 187;
- páginas >400 LOC: Approval Center, Workspace Documents, Settings, Project Status;
- componentes >390 LOC: DocumentValidationPanel, WorkspaceGitOperationsPanel, DocumentEditPlanner.

La fuente machine-readable es `DEVPL_UX_P0_FRONTEND_BASELINE_v1_0_0.json`.
   
## 5. Micro-sprints

### UX-P0-A — Authority rebind, frontend identity and design-system foundation

**Objetivo:** crear el primer successor de repo430, absorber drift documental S3, materializar los documentos owner-approved y establecer design/IA contracts antes de cambiar el shell.

**Incluye:**

- rebind Project State / Source Registry / CURRENT/README/roadmap al programa UX-P0;
- corregir metadata current-active stale detectada tras GSDLC-12;
- incorporar los dos documentos APPROVED en `docs/00_product`;
- reconciliar `ui/web/package.json` current-active metadata;
- crear semantic design tokens para color, type, spacing, radius, elevation, state y focus;
- documentar current route inventory + target information architecture;
- crear/actualizar ADR solo si la separación shell/navigation/presentation cambia una decisión arquitectónica;
- no rediseñar todavía cada vista.

**Validación:** build UI, route enforcement, a11y smoke, state matrix, docs/TCR, Test Impact, visual baseline targeted. No Full.

**PASS:** successor limpio; autoridad current-active coherente; tokens/IA contract existen; comportamiento/guards sin regresión.

**Salida esperada:** repo431 candidate.

### UX-P0-B — Product App Shell, grouped navigation and persistent project context

**Objetivo:** convertir el shell en una guía de producto coherente.

**Incluye:**

- navigation por dominios/workflow;
- responsive navigation;
- breadcrumbs / location context;
- persistent Project Context Strip;
- authoritative Next Action projection;
- integrar Session, Guided/Expert y recovery indicator sin duplicar chrome;
- mover route IDs/raw diagnostics de Guided a Expert/Evidence;
- conservar route guards y handoffs.

**Validación:** auth/project guards, project entry handoff, route visibility, keyboard/focus, responsive targeted browser. No Full.

**PASS:** usuario identifica proyecto, etapa, estado, blocker y next action en todas las rutas project-scoped.

**Salida esperada:** repo432 candidate.

### UX-P0-C — Greenfield critical-path surfaces

**Objetivo:** productizar las superficies que el piloto greenfield usará primero.

**Incluye:**

- Project Home;
- Create/Open/Import;
- Project Status;
- Pre-code;
- Documents entry/overview solo en lo necesario para journey;
- Planning/Roadmap;
- common page header, stage progress, blocker explanation, primary action y recovery copy;
- copy Guided simple + secondary technical labels.

**Fuera de alcance:** refactor profundo de cada editor/document tool; eso permanece para UX-P1/P2 salvo blocker.

**Validación:** real-browser critical path, role-negative, keyboard, no-tech task script parcial, route/API parity. No Full.

**PASS:** las siete preguntas del pre-pilot gate se responden visualmente durante el tramo idea→planning.

**Salida esperada:** repo434 candidate.

### UX-P0-D — Cross-surface operation patterns and progressive evidence

**Objetivo:** homogeneizar los patrones operacionales que aparecen después de planning sin rediseñar cada surface exhaustivamente.

**Incluye primitives/patterns comunes:**

- `OperationState` / status semantics;
- `PrimaryAction` / action hierarchy;
- `ApprovalSummary`;
- `GateSummary`;
- `DiffSummary`;
- `LongRunningOperation` feedback;
- progressive `Evidence/Diagnostics` container;
- error/block/recovery explanation;
- responsive density.

**Adopción prioritaria:** Story/Code, Approvals, Jobs, Quality, Release, Recovery/Reconciliation, AI; Reports/Traces permanecen Expert/diagnostic-heavy.

**Validación:** targeted browser matrix sobre estas superficies, existing contract smokes, accessibility, Test Impact. No Full.

**PASS:** mismo estado/acción significa lo mismo visualmente en todas las superficies críticas.

**Salida esperada:** repo435 candidate.

### UX-P0-E — Pre-pilot real-browser, usability and regression closure

**Objetivo:** demostrar que UX-P0 está lista para un piloto greenfield y cerrar el backlog.

**Incluye:**

- real-browser matrix del normal journey P0;
- scripted no-tech usability session;
- responsive viewport matrix acotada;
- accessibility critical-path closure;
- frontend performance budget;
- route/API/policy parity;
- docs/current-authority reconciliation;
- exactamente una logical Full para DEVPL-UX-P0 después de todos los gates baratos.

**Full policy:** una vez. Functional FAIL se preserva y no se repite; usar composite selective recovery.

**PASS:** siete preguntas respondibles; terminal escapes=0 en normal journey demostrado; S0/S1=0; critical a11y blockers=0; Full/composite PASS; second Full=0.

**Salida esperada:** repo436 local pre-pilot productization RC, que se convierte en authority para el greenfield pilot/rebaseline siguiente.

## 6. Test strategy

A-D:

- Test Impact;
- focal/impacted suites;
- UI build/smoke;
- route registry enforcement;
- auth/project guards;
- a11y targeted;
- browser solo cuando la superficie cambie.

E:

- gates baratos primero;
- browser/usability/accessibility/performance;
- HCA + Contract Reconciliation;
- una Full;
- composite recovery si aplica.

## 7. Evidencia transversal

Cada micro-sprint debe conservar:

- source delta manifest;
- Test Impact;
- current/historical contract sweep proporcional;
- screenshots mínimos cuando exista cambio visible;
- keyboard/focus observations;
- UX findings ledger;
- Git pre/post;
- S0/S1;
- `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`.

## 8. UX findings severity

- **UX-S0:** pérdida de datos, security/authority bypass, destructive action hidden.
- **UX-S1:** normal journey imposible, critical route inaccessible, critical a11y blocker.
- **UX-S2:** alta fricción/confusión con workaround dentro de producto.
- **UX-S3:** polish/copy/secondary consistency sin invalidar tarea.

UX-P0 cierra con UX-S0/S1=0. UX-S2 puede quedar solo con owner + plan UX-P1 si no invalida el piloto.

## 9. Definition of Done

- A→E cerrados secuencialmente;
- shell/IA/context/next-action coherentes;
- critical path productizado;
- cross-surface patterns consistentes;
- browser/usability/a11y/perf PASS;
- una Full/composite PASS;
- second Full=0;
- S0/S1=0;
- successor RC limpio.

## 10. Autorización del piloto

El greenfield pilot solo inicia desde el successor Windows-validado de UX-P0-E. Repo430 permanece congelado como baseline histórico de GSDLC-12.


## Rebound operativo repo434 — 2026-09-17

- UX-P0-C: `CLOSED/PASS/WINDOWS-VALIDATED` sobre `repo_DevPilot_Local_434_DEVPL_UX_P0_C_GREENFIELD_CRITICAL_PATH_WINDOWS_VALIDATED_CANDIDATE.zip` / `75dbead73c6c6aaf1f792e02f3659ee2b6c0b927` / `e1117ba5e9c3bace2de482940d6b447b0150acb2e26ba1647f9677939f5faf39`.
- UX-P0-D: current-active, successor esperado `repo435`.
- UX-P0-E: siguiente micro-sprint, successor esperado `repo436`.
- Full Regression: `0/1`, reservada exclusivamente para UX-P0-E.

# UX-P0 final closure — composite recovery

UX-P0-E and UX-P0 are `CLOSED/PASS/WINDOWS-VALIDATED`. The unique Full is preserved as FAIL-once evidence and closure is adjudicated `PASS/COMPOSITE-FULL-PLUS-SELECTIVE-RECOVERY` after exact 50/50 recovery, bounded impact and Historical Regression Guard PASS. Successor authority is repo436. No second Full was executed.
