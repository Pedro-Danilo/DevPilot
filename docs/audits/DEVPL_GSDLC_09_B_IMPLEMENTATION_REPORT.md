---
doc_id: "DEVPL-GSDLC-09-B-IMPLEMENTATION-REPORT"
title: "DEVPL-GSDLC-09-B — Bounded Code/File Workspace Viewer-Editor — implementation report"
status: "implemented/local-qualified/windows-pending"
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
