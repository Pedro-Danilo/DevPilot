---
doc_id: "DEVPL-GSDLC-04-E-MANUAL-BROWSER-OBSERVATIONS"
title: "DEVPL-GSDLC-04-E — Observaciones browser Windows"
status: "template/ready-for-windows"
version: "1.0.14"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "pending_execution"
---

# DEVPL-GSDLC-04-E — Observaciones browser Windows

No registre tokens, passwords, cookies, `.env`, API keys ni secretos. Edite únicamente identidad, Resultado, Observación, resumen y decisión.

## Identidad de ejecución

- Fecha/hora: PENDIENTE
- Operador: PENDIENTE
- Repo/commit antes del commit 04-E: `D:\Projects\DevPilot_Local @ e1d9d1c722dc3fa389ce4cb7c3e18bc401d081cd`
- ZIP de implementación SHA-256: PENDIENTE_BOOTSTRAP
- Browser/versión: PENDIENTE
- Fixture: `D:\Projects\DevPilot_E2E_Evaluation\worktrees\DEVPL_GSDLC_04_E_BROWSER`

<!-- BEGIN_BROWSER_MATRIX -->
| Caso | Resultado PASS/BLOCK | Evidencia | Observación |
|---|---|---|---|
| Project Home + active project + Artifact Workbench | | `00_project_active_workbench.png` | |
| Direct project route guard without context | | `01_project_context_guard.png` | |
| MANUAL Markdown DRAFT | | `02_manual_markdown_draft.png` | |
| MANUAL autosave/restart recovery | | `03_manual_autosave_recovery.png` | |
| JSON DRAFT validation hints | | `04_json_hints.png` | |
| PASTE provenance | | `05_paste_provenance.png` | |
| UPLOAD/IMPORT supported | | `06_upload_import.png` | |
| Upload traversal/unsupported blocked | | `07_upload_negative.png` | |
| Validate/findings/navigation | | `08_findings_navigation.png` | |
| Immutable plan/diff | | `09_plan_diff.png` | |
| Exact owner approval | | `10_owner_approval.png` | |
| Wrong-role approval denied | | `11_wrong_role_denied.png` + `13_wrong_role_auth_prepare_v1_0_5.json` | |
| Apply + freeze | | `12_apply_freeze.png` | |
| Stale preimage invalidates plan/approval | | `13_stale_preimage.png` | |
| External edit FROZEN → REVALIDATION_REQUIRED | | `14_external_revalidation.png` | |
| Rollback/recovery | | `15_context_recovery_PASS.png` + `15_rollback_recovery.png` + `15_rollback_preflight_v1_0_11.json` + `15_rollback_verify_v1_0_11.json` | |
| API-down/timeout recovery | | `16_api_down_recovery.png` | |
| Keyboard/focus/labels/accessibility | | `17_accessibility.png` | |
<!-- END_BROWSER_MATRIX -->

La evidencia `.json` es machine-readable y no requiere screenshot sustituta. Cada observación sigue siendo obligatoria y debe describir lo realmente verificado.

## Resultado operativo — COMPLETE EXACTAMENTE ESTOS CAMPOS

<!-- BEGIN_BROWSER_SUMMARY -->
- `browser_acceptance`: PENDING
- `S0_open`: 0
- `S1_open`: 0
- `secrets_exposed`: false
- `network_runtime_used`: false
- `external_api_used`: false
- `pilot_workspace_accessed`: false
- `normal_user_powershell_required`: 0
- `external_operator_project_writes`: 0
- `full_regression_runs_before_browser`: 0
<!-- END_BROWSER_SUMMARY -->

## Firma/decisión

- Decisión: PENDING
- Justificación: PENDIENTE


### Recovery-009 B15 note

For B15, the separate rollback approval is adjudicated **inline in Edición documental gobernada** using the rollback approval card (`Aprobar` / `Denegar`). Approval Center is not required for this rollback UX and must not be used as a substitute. The final PASS observation must be supported by both Recovery-009 machine JSON files and the focused screenshot.


> Recovery-009 evidence note: CORS `OPTIONS 200` is transport preflight only and is never accepted as proof of a rollback approval request. B15 requires machine-readable `POST rollback-approval-request 200`, separate human approval, and `POST rollback 200`.


### Recovery-010 B15 runtime note

Fresh API/UI restart during B15 may legitimately occur while `docs/baseline.md` is still the exact postimage of the persisted UOC-005 `applied` execution. Runtime Console v1.0.2 accepts that state only through machine authority (persisted execution + Recovery-009 PASS preflight + immutable Git preimage + exact dirty scope). This is not a generic dirty-file exception. Final B15 PASS remains bound to `15_rollback_preflight_v1_0_11.json`, `15_rollback_verify_v1_0_11.json`, and the focused screenshot after `rolled-back-manual`.


### Recovery-011 project-context recovery note

For B15 recovery after a fresh login, do **not** execute `Open Existing`. Open the exact execution-bound URL with `recover_project_context=server-active`. The UI may rebuild only its UX `sessionStorage` project context after read-only server verification of the active workspace and the persisted execution/document. This recovery path must not create a Project Entry execution approval or call `/project-entry/execute`. A redirect to Project Home is a BLOCK and must be preserved as evidence instead of retrying Project Entry.



### Recovery-014 terminal continuity note

For the final B15 recovery attempt, the operator must first create the machine-readable Recovery-014 browser arm checkpoint. Open only the exact canonical recovery URL from the guide. If Login appears, authenticate once as `owner.local`; do not use Create/Open/Import. PASS requires that Workspace Documents opens and that the Recovery-014 browser verifier proves `GET /settings/workspace 200` plus the exact `GET /workspace/edit-executions/{id} 200` after the arm offset, with zero Project Entry POSTs. If the UI returns to Project Home or shows `recovery=server-context-failed`, stop and preserve evidence. Recovery-014 is terminal; do not improvise another recovery path.
