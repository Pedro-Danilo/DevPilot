---
doc_id: "DEVPL-GSDLC-03-E-CLOSURE-REPORT"
title: "DEVPL-GSDLC-03-E — Project Home and browser acceptance closure report"
status: "closed/PASS"
version: "1.0.16"
owner: "Ordóñez"
updated: "2026-08-20"
approval: "CLOSED/PASS"
---

# DEVPL-GSDLC-03-E — Closure report candidate

03-E materializes the visible backlog milestone without replacing historical `ui.dashboard`: `/` remains `ui.dashboard`, but Project Home is now the primary post-login surface and the legacy operational dashboard is a collapsed advanced section.

## Product journey

`login → Project Home → Create/Open/Import → dry-run → preimage revalidation → approval (owner mutation only) → execute → verify → Project Status`.

The normal Project Entry journey does not require the legacy local API token or PowerShell.

## UX hardening

- three explicit entry cards;
- mode deep links and progressive disclosure;
- client-side Project ID syntax feedback;
- any parameter change invalidates plan/approval state;
- approval ID is server-derived/read-only;
- non-owner sessions see explicit execution role gating;
- recovery/rollback evidence is visible when execution fails;
- success exposes an explicit Project Status continuation;
- acceptance-only rollback controls are Vite DEV gated and server fault-injection gated.

## Historical preservation

GSDLC-03-D API/RBAC/UI registries are frozen at close before E changes. No historical snapshot is rewritten. Current top-level route count remains 11; no new route is introduced.

## Validation policy

Pre-Windows work may run focal/cumulative/impact/historical guards but **must not execute the backlog full regression**. Windows 03-E executes the single full exactly once after browser acceptance. On failure, the marker/log are immutable and recovery is composite/selective without a second full.

## Closure status

Windows validation, composite recovery, clean successor generation and explicit owner adjudication are complete. `GSDLC-03-E = CLOSED/PASS`; repo364 is the owner-adjudicated successor and GSDLC-04 is authorized. Historical browser/full evidence remains sealed and is not re-executed during the GSDLC-04 activation rebind.

## PRE-WINDOWS validation performed

The candidate was validated without executing the backlog full regression:

- focused + cumulative + selected historical/security pytest: `124 passed, 0 failed, 0 errors, 0 skipped`;
- Project State: PASS;
- Documentation Governance: PASS, `0 blocking_findings`;
- Test Contract Registry v1: PASS, `284 contracts`;
- Test Contract Registry v2: PASS, `284 contracts`;
- GSDLC-03-E UI static smoke: PASS, `15 checks`;
- TypeScript explicit entry graph: PASS;
- Test Impact v2: PASS/analyze-only, `28 changed paths`, `144 matched contracts`, `74 P0`, `61 P1`, `237 recommended tests`;
- Vite production build: deferred to Windows because clean source authority intentionally excludes `node_modules`;
- full regression runs: `0`.

## Preliminary production limitations

This remains a first industrial browser-journey closure, not a claim that every bootstrap dependency can be installed offline. Dependency installation requiring network remains deferred unless an exact approved lock/cache authority exists. Remote Git execution remains disabled-by-default. The final `CLOSED/PASS` decision additionally requires the real Windows browser matrix and the single authorized full/composite regression evidence.

## Corrective Windows C1 v1.0.2

La primera corrida Windows v1.0.1 bloqueó antes de browser/full porque dos tests acumulativos de 03-D dependían del discovery real y `npm` agotó el timeout default de 3 s al ejecutar `node + npm-cli.js --version`. Node, ruta npm y demás prerrequisitos estaban resueltos; no hubo fallo de approval/RBAC. El corrective eleva el timeout default read-only a 8 s, todavía bounded por el límite interno de 15 s y sin red, installers ni shell. La validación del operador se segmenta para preservar checkpoints PASS y evitar repetir un agregado amplio por un fallo ambiental puntual.

## UX corrective — project-context navigation v1.0.5

Windows browser inspection of the first Home screenshot identified a product-journey gap before formal acceptance: `/` rendered the intended Project Home content but the shell still labelled the active route as `Dashboard` and exposed all operational surfaces before a project-entry journey completed. The corrective preserves the historical `ui.dashboard` route id/path `/` but changes the product-facing title to `Project Home` and applies progressive-disclosure navigation.

Pre-project navigation now exposes Project Home plus global Account/Settings only, and the legacy operational Dashboard body is not rendered until a project context reaches PASS. `Approval Center` becomes contextual during entry; Project Status/Documents/Reports/Traces/Jobs/Quality/AI become visible after Create/Open/Import execute reaches PASS. Direct browser navigation to a project-scoped route without the browser project context is redirected to Project Home with an explicit disabled reason. The context is session-scoped UX state, cleared on logout/session invalidation; it is not a new authorization boundary and does not replace server RBAC/PolicyEngine/PathGuard.

The existing 03-D target-local workspace registration contract is not rewritten by this corrective. Server-side binding of the new target as the portfolio active workspace is therefore not claimed here; this corrective is deliberately limited to the 03-E guided browser journey and truthful navigation hierarchy.

Pre-Windows corrective validation: selected 03-E/historical UI/docs pytest `37 passed`; Project State PASS; Documentation Governance PASS (`907/907`, 0 warning/block/drift); TCR v1/v2 PASS (`284/284`); 03-E static smoke PASS (`21 checks`); current route-enforcement smoke PASS (`9/9`); TypeScript explicit entry graph PASS. Vite production build for these final bytes remains required in Windows R6 using the already-provisioned local `node_modules`. Full regression runs remain `0`.

## Browser runtime corrective — Project Entry timeout budget v1.0.6

La corrida Windows posterior a `GSDLC-03-E-UX-001` confirmó que Project Home y la navegación contextual funcionan, pero el primer `CREATE_NEW` quedó bloqueado al generar dry-run porque la UI conservaba el timeout HTTP ordinario de 8000 ms mientras el backend ejecuta discovery local secuencial y el corrective C1 ya había elevado el probe tolerante a Windows a 8 s. La API permaneció levantada; el log alcanzó el preflight `OPTIONS /api/v1/project-entry/dry-run`, y no existe evidencia de write, network, approval o execute antes del timeout.

`GSDLC-03-E-RUNTIME-002` mantiene `DEFAULT_REQUEST_TIMEOUT_MS=8000` para operaciones ordinarias y agrega un presupuesto específico y bounded para Project Entry: probe backend solicitado por UI `8.0 s`, request browser de planning/revalidation/approval `90000 ms`, y execute conserva `240000 ms`. Esto evita convertir una operación deliberadamente más costosa en una relajación global de los contratos históricos UOC/POST-H-EVAL-002. Dry-run/revalidation siguen read-only/fail-closed; el banner de execute bloqueado es comportamiento de seguridad esperado cuando todavía no existe plan vigente.

La evidencia browser previa al corrective se conserva como forense y no puede contarse como PASS final. Browser acceptance debe reiniciarse desde escenario 1 con screenshots posteriores al marker del corrective. Full regression permanece en `0` ejecuciones.

## Backend timeout authority propagation — GSDLC-03-E-RUNTIME-003 v1.0.7

La validación Windows v1.0.6 bloqueó antes de browser porque el corrective RUNTIME-002 elevó correctamente el budget HTTP específico de Project Entry y el `EnvironmentDiscoveryService` tenía default 8 s, pero varias capas intermedias conservaban defaults históricos `3.0`. En particular, `ProjectEntryPlanningBody` de la API y ApplicationService/dispatch reenviaban 3 s cuando el caller omitía `timeout_seconds`; el test API 03-D demostró el efecto al devolver `PROJECT_ENTRY_REQUIRED_TOOL_BLOCK` por timeout de npm.

RUNTIME-003 elimina esa divergencia sin elevar límites globales ni introducir retries: `DEFAULT_TIMEOUT_SECONDS=8.0` en `workspace.environment_discovery` queda como única autoridad y se propaga por Project Entry dry-run/planning, ApplicationService, dispatch, request model API y revalidaciones de approval/execute. El clamp máximo permanece 15 s, `shell=False`, red/installers siguen deshabilitados y el presupuesto browser ordinario permanece 8000 ms.

La evidencia v1.0.6 BLOCK se conserva; no se repite C1 ni la full regression. La recuperación Windows debe validar primero el contrato estático de propagación, después el nodeid API causal en aislamiento y solo entonces el conjunto impactado y gates determinísticos. Browser acceptance permanece pendiente y la full regression continúa en 0 ejecuciones.

## GSDLC-03-E-UX-002 — Approval Center cross-tab handoff corrective

Windows browser acceptance exposed a successor-navigation defect after CREATE dry-run/revalidation: `Abrir Approval Center ↗` opened a new tab, but the entry journey context was stored only in `sessionStorage`. The new tab therefore had no Project Entry UX context and `/approvals` was redirected to Project Home even though Approval Center is intentionally allowed during entry.

The corrective preserves the original Project Entry tab and its in-memory plan/preimage state while allowing the approval surface in a separate tab. A short-lived `localStorage` handoff is armed **only after the server creates an approval request**. The handoff is bound to `actor_id` plus the authenticated session `created_at`, expires after 30 minutes, is read only for `/approvals`, and is cleared when a new entry begins, project context becomes active, or the authenticated shell is cleared. It is an **UX routing hint only**: approval/deny/execute authority continues to be enforced by the server human-session, RBAC, CSRF, exact approval binding, PolicyEngine and PathGuard.

The Approval Center link remains hidden until a concrete approval request exists, which removes the previous ambiguous operator path. Direct `/approvals` navigation without an entry/project context or a valid handoff remains guarded. No backend, approval authority, PathGuard, execution or network contract is relaxed. Full regression remains at zero and is still reserved for the final post-browser gate.


## Corrective GSDLC-03-E-UX-003 / HARNESS-006 / RUNTIME-004 — v1.0.11

El browser retest de UX-002 demostró que el cross-tab route handoff ya abre `/approvals`, pero la superficie seguía dependiendo de la lista global `/approvals?limit=100`, portfolio y capabilities antes de poder actuar sobre el Approval ID exacto. Esa dependencia agotó el timeout ordinario de 8 s y bloqueó el journey aunque `execution-approval-request` ya había respondido 200.

Corrective:
- el handoff se liga a `actor_id + session.created_at + approval_id` exacto y TTL 30 min;
- Approval Center entra en modo dirigido y consulta primero `/approvals/{approval_id}`; lista global/portfolio/Action Launcher no son prerequisitos del Project Entry handoff;
- la autoridad visible se deriva de `AuthSessionContext`, mientras `auth/capabilities` queda suplementario en modo general;
- approvals read/decision usan budget bounded de 30 s;
- `normalizeTimeout` deja de truncar silenciosamente planning 90 s / execute 240 s a 60 s;
- `MANUAL_BROWSER_OBSERVATIONS_v1_0_11.md` se inicializa automáticamente e idempotentemente antes del browser retest; nunca se sobrescribe evidencia diligenciada;
- se reconcilian dos oracles históricos de POST-H con successor-aware assertions y se normaliza el status schema-valid del current UI route registry, sin alterar snapshots frozen.

### Gate
Browser acceptance y full regression permanecen pendientes. Full regression runs: **0**.

## GSDLC-03-E-UX-004 / HARNESS-008 — resumable Project Entry and guided return v1.0.13

El browser v1.0.12 demostró que el Approval Center dirigido ya carga y aprueba el Approval ID exacto server-side, pero también expuso una fragilidad de journey: `ProjectEntryDryRunView` conservaba intake/plan/preimage/approval únicamente en variables JavaScript en memoria. Si el operador usaba la navegación visible `Project Home` en vez de seleccionar la pestaña CREATE original, la fase `entry` sobrevivía en `sessionStorage` pero el detalle del plan se perdía y la vista Home no ofrecía un CTA de reanudación.

Corrective:
- el estado de reanudación de Project Entry se conserva en `sessionStorage` durante 30 minutos, ligado a `actor_id + session.created_at`; nunca usa `localStorage` ni otorga autoridad;
- persiste únicamente contexto UX de intake/dry-run/bootstrap-plan/plan_hash/preimage_hash/approval_id; al restaurar, `Verify approval` y `Execute` permanecen bloqueados hasta una nueva `Revalidar preimage` server-side;
- cualquier cambio de parámetros limpia resume state y cross-tab handoff, preservando stale-plan fail-closed;
- Project Home muestra `Retomar <ENTRY_MODE>` cuando existe un estado recuperable;
- la pestaña auxiliar Approval Center oculta el enlace/brand navegable a Project Home y presenta `Cerrar esta pestaña y volver a CREATE`, reduciendo el error humano que originó el incidente;
- la documentación reconcilia el delta acumulativo real en `38 paths` y reconoce RUNTIME-003 como `PASS/windows-validated` según la evidencia Windows ya obtenida.

La persistencia es explícitamente una conveniencia UX. El servidor continúa siendo autoridad para sesión, RBAC, approval, plan/preimage y execute. Browser acceptance debe reiniciarse con screenshots posteriores a UX-004. La full regression continúa en `0` ejecuciones.


## Full regression exactly-once failure and REG-001 recovery

The single authorized backlog full regression was executed in Windows after browser acceptance and is immutable evidence. It completed with `2418 passed / 67 failed / 0 errors / 4 skipped`, source postimages remained intact and no unexpected Git change was produced. A second full regression is prohibited.

The 67 residuals are not treated as 67 unrelated product defects. `GSDLC-03-E-REG-001` classifies them into inherited contract-reconciliation families: runtime auth-state isolation, current API registry counters/schema, sensitive-action/RBAC/MIASI total mapping, derived UI capability mapping, mutable documentation pointers versus frozen history, and obsolete successor UI static oracles.

Recovery mode is `composite-full-regression-selective-retest`: apply only the controlled reconciliation delta, run causal gates, run the exact 67 failed nodeids, run bounded impact/historical governance guards, preserve the original full marker and write composite recovery evidence. Browser acceptance remains authoritative and is not repeated because the recovery does not modify browser product source.

The transversal documentation policy is `docs/02_architecture/governance/DEVPL_DOCUMENTATION_CONTRACT_RECONCILIATION_POLICY_v1_0_0_APPROVED.md`. It becomes a mandatory pre-full deterministic sweep for successor backlogs so future full regressions are not the first detector of registry/document drift.

**Current decision:** recovery candidate only; not CLOSED/PASS until Windows composite evidence is PASS and owner adjudication is completed.

## Windows browser acceptance and composite closure — v1.0.15

Authoritative Windows evidence:

```text
DEVPL_GSDLC_03_E_REG_002_COMPOSITE_WINDOWS_EVIDENCE_v1_0_15.zip
SHA-256: a0a418d9cad544d3c10cac40e257d41baf01f9cb4df9c12d67005d1a7a6ece33
source fingerprint: 8c698d63a75938267b6f9b8028b1cfbec9a54be9e2375da15d3b509f6822772a
```

Validated facts:

- browser acceptance: `PASS`, 14 scenarios, 12 screenshots;
- normal user PowerShell required: `0`;
- external operator project writes: `0`;
- S0/S1: `0/0`;
- full regression executed exactly once: `2489 tests = 2418 PASS / 67 FAIL / 0 ERROR / 4 SKIP`;
- second full regression: `false`;
- REG-001 exact-67 selective retest: `56 PASS / 11 FAIL`;
- REG-002 causal validation: `7/7 PASS`;
- REG-002 exact residual retest: `11/11 PASS`;
- REG-002 bounded impact guard: `13/13 PASS`;
- Test Impact v2: `PASS`;
- Historical Regression Guard: `PASS`;
- Documentation Governance: `PASS`, `0 warnings`, `0 blocking`, `0 drift`;
- TCR v1/v2: `PASS`;
- unexpected Git paths: `0`;
- network/external APIs during REG-002 recovery: `false/false`.

The original failed full regression remains immutable historical evidence. Closure is valid through the approved composite recovery policy; it is not reinterpreted as a green full run.

### Browser manual evidence metadata note

`MANUAL_BROWSER_OBSERVATIONS_v1_0_13.md` is intentionally preserved byte-for-byte because its SHA-256 is bound into the authoritative browser report. Its body contains 14 PASS scenario rows, the three approval IDs, required cross-tab/resume facts and `OVERALL = PASS`; the browser recorder machine-verifies those facts.

The historical frontmatter still says `status: pending_execution` and `approval: pending_browser_operator`. That is a harness metadata-finalization defect, not a failed browser scenario. Altering the file now would invalidate the evidence hash. The discrepancy is therefore recorded here and must be fixed in future browser-record generators by finalizing frontmatter before hashing, not by rewriting this immutable evidence.

### Final candidate decision

`DEVPL-GSDLC-03-E` is now a **Windows composite PASS candidate / pending owner adjudication**. No functional corrective, browser rerun, exact-67 rerun or second full regression is required.

Remaining governance sequence:

```text
final metadata reconciliation
→ focused deterministic validation
→ commit candidate
→ clean successor repo + SHA-256
→ explicit owner adjudication
→ DEVPL-GSDLC-03 CLOSED/PASS
→ DEVPL-GSDLC-04 authorized
```

