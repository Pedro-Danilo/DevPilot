---
doc_id: "DEVPL-GSDLC-09-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-09-B — Bounded Code/File Workspace Viewer-Editor — implementation report"
status: "closed/pass/windows-validated"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-07"
approval: "windows-live-browser-evidence-gated"
---

# DEVPL-GSDLC-09-B — Implementation report

## Objetivo
Implementar exclusivamente el Code Workbench manual: source tree bounded, visor/editor textual y `SourceDraftBuffer`. 09-B **no** implementa SourceChangePlan, apply, rollback, terminal, arbitrary shell, CodingAgent ni TestAgent; esas capacidades pertenecen a 09-C/D.

## Autoridad
- Parent: `repo_DevPilot_Local_408_DEVPL_GSDLC_09_A_STORY_EXECUTION_CONTEXT_WINDOWS_VALIDATED_CANDIDATE.zip`.
- Parent commit: `fede10c963d7af571fc0fd062f76323d647877f7`.
- Parent SHA-256: `c077fcba424527a179773e9f2b155700c357fecd0e7d9af8e40533374d290e59`.
- FRX profile authority: `frx-v2.4-current`; `full=0` en 09-B.

## Implementación
- `CodeWorkbenchApplicationService` server-side con source discovery bounded, opaque IDs, UTF-8 text read y policy allowlist.
- `SourceDraftBuffer` runtime-only para CREATE/EDIT/RENAME con revision hash y preimage SHA-256.
- External edit invalida draft/preimage y produce `CONFLICT`.
- API `/api/v1/story/code/*` protegida por sesión humana/RBAC; no existe endpoint Apply. API/RBAC registries quedan reconciliados a 169/169 rutas y UI route registry a 14 rutas.
- UI `/story/code` con source tree, text editor, draft state, recheck/discard y mensajes explícitos `DRAFT ONLY` / `APPLY NO DISPONIBLE HASTA 09-C` / `SIN TERMINAL`.

## Seguridad
Workspace-root enforcement, no follow symlink/reparse, hidden/runtime/secret paths bloqueados, binary/unsupported/oversize bloqueados, SecretGuard, owner/developer authoring y demás roles read-only. El service no expone método apply y `source_mutations_performed=false`.

## Browser
La herramienta local bloquea navegación HTTP localhost en Chromium (`ERR_BLOCKED_BY_ADMINISTRATOR`). Se ejecutó Chromium real sobre el componente real con transporte determinista mockeado: `7/7 PASS`, cinco screenshots y source restaurado. Esta evidencia **no sustituye** el browser live Windows. El operador Windows requiere API/UI foreground en tres consolas y browser live PASS antes del cierre.

## Validación
- Focal backend/security: `8/8 PASS`.
- UI static smoke: `PASS`.
- Chromium component acceptance: `7/7 PASS`.
- API contract drift: `PASS/169`; UI route enforcement: `PASS/8`.
- Bounded current A→B/API/RBAC/UI/governance: `61/61 PASS`.
- Bounded historical/authority: `25/25 PASS`.
- Project State/TCR v1/TCR v2/Docs Governance/Evidence Freshness: `PASS`.
- Test Impact: `45 paths`, `203 contracts`, `313 tests recommended`, `unmatched=0`, dry-run.
- Historical Regression Guard: `PASS/WAIVER/5-of-5`, 0 warnings, 0 blockers.
- Full Regression: `0`.

## Riesgos y limitaciones
Primera versión del editor manual. No aplica cambios al filesystem source y no es un IDE: no hay terminal, debugging, extensiones ejecutables ni arbitrary uploads. 09-C debe añadir plan/diff/approval/atomic apply/rollback sin degradar estas fronteras.

## PASS/BLOCK
PASS solo si source real permanece byte/semanticamente sin cambios durante draft, path escape/binary/oversize/secret/rol inválido bloquean, external edit produce conflict, API/RBAC/UI registries son coherentes, browser live Windows pasa y S0/S1=0. BLOCK ante cualquier uncontrolled write, path escape, apply prematuro, terminal/shell o browser live no demostrado.

## Windows closure contract

Status after authoritative Windows validation: `CLOSED/PASS/WINDOWS-VALIDATED`. Closure requires live API/UI browser acceptance `7/7`, focal `8/8`, bounded current `61/61`, bounded historical `25/25`, deterministic gates and Historical Regression Guard PASS, with `full_regression_runs=0`. The Windows operator must preserve source unchanged by Code Workbench drafts and promote repo409 only by Git fast-forward after all evidence is sealed.

## Windows BLOCK-02 corrective incorporated at closure

The first live-browser attempt exposed a synchronization defect in the acceptance runner, not in Code Workbench behavior: the runner waited for a textarea that exists before the asynchronous source/preimage load completes. Bundle v1.0.3 synchronizes on the server-loaded source state and exact preimage, fails fast on UI BLOCK/ERROR, isolates evidence by `browser_prep_id`, captures diagnostic network/UI events and restores the controlled fixture in `finally`. The corrected runner is incorporated into repo409 in the normal closure commit. The 45-path Test Impact domain is unchanged because this runner already belonged to the 09-B delta. No Full Regression is consumed.


## Windows BLOCK-03 corrective incorporated at closure

The v1.0.3 live attempt proved the first draft save (HTTP 200), the path-escape negative (HTTP 403) and source restoration, then blocked while preparing the external-edit case because the runner reopened the same source after a prior draft existed. `openSource()` intentionally resets the UI-local draft pointer, while the runtime `SourceDraftBuffer` remains persisted; the backend correctly returned HTTP 409 `GSDLC09B_DRAFT_REVISION_CONFLICT` instead of accepting an unbound overwrite.

Bundle v1.0.4 treats each browser case as an independent draft lifecycle: the source-unchanged draft is discarded before path-escape/external-conflict, the conflict case creates its own fresh draft, and after conflict the controlled external edit is restored, rechecked and the runtime draft is discarded before role-negative validation. `browser-prep` remains the authoritative attempt reset and recreates both browser workspace and transient auth state. No functional 09-B source behavior changes and no Full Regression is consumed.

The v1.0.4 runner also validates the authenticated session roles immediately before the role-negative UI check, so a stale owner/developer session cannot create a false PASS for disabled authoring.

## Windows BLOCK-04 corrective incorporated at closure

The v1.0.4 live attempt reached 6/7 PASS and restored the source, then timed out only in the role-negative UI case. The runner had demoted the sole `local-owner` to `architect`, causing `owner_exists()` to become false and `/auth/bootstrap/status` to correctly enter First Run. v1.0.5 preserves the owner, provisions a separate synthetic architect in the transient auth store using the established synthetic-identity pattern, authenticates it through the real LoginView in a fresh BrowserContext, verifies architect-only session authority and disabled draft authoring, captures `05_role_negative_read_only.png`, and removes the synthetic identity before completion. No functional Code Workbench behavior changes and no Full Regression is consumed.

