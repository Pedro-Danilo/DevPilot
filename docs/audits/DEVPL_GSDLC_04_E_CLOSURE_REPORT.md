---
doc_id: "DEVPL-GSDLC-04-E-CLOSURE-REPORT"
title: "DEVPL-GSDLC-04-E — Implementation closure report"
status: "implemented/recovery-014-terminal-ready-for-windows"
version: "1.0.14"
owner: "Ordóñez"
updated: "2026-08-24"
approval: "pending_windows_execution"
---

# DEVPL-GSDLC-04-E — Implementation closure report

## Estado

`IMPLEMENTED / RECOVERY-014-TERMINAL-READY-FOR-WINDOWS`. No es `CLOSED/PASS` todavía.

## Implementado

- detecta external `modified`, exact `renamed` y `deleted` sobre reviews APPROVED/FROZEN;
- drift real invalida approval y mueve lifecycle a `REVALIDATION_REQUIRED`;
- conserva source provenance, branch/head/status y Git diff para UI/auditoría;
- `ArtifactReconciliationUX` muestra drift fail-closed sin auto-revert ni hidden merge;
- MANUAL/PASTE/UPLOAD/IMPORT y review/apply/freeze anteriores permanecen integrados;
- branch switch queda registrado como contexto, sin checkout/switch automático;
- browser closure Windows definido sobre 18 escenarios;
- marker durable y harness para una única full regression después de browser PASS;
- si la full falla, la full no se repite y solo se habilita recuperación compuesta selectiva.

## Seguridad

No arbitrary shell, no network, no external API, no pilot workspace, no auto-revert, no hidden merge. Reconciliation no escribe source. UOC-005 continúa como único writer gobernado.

## PASS/BLOCK

PASS-CANDIDATE Windows exige browser 18/18, parity state/file/Git, S0/S1=0 y full regression PASS o composite recovery PASS usando la única corrida full. BLOCK ante FROZEN que permanezca aprobado tras drift, UI que oculte drift, rerun de full, source write del operador durante browser o contract drift previo a full.

## Recovery-001 — runtime fixture contract parity

La primera ejecución Windows bloqueó antes de levantar API porque `devpl_gsdlc_04_e_runtime_console.py` conservaba el requisito histórico `docs/baseline.json` del fixture 04-D, mientras `prepare-browser` 04-E crea y sella exactamente `.gitignore`, `.devpilot/project.yaml`, `docs/manual_authoring.md`, `docs/manual_authoring.json` y `docs/baseline.md`. Recovery-001 elimina esa precondición heredada, alinea el runtime con `BASELINE_TRACKED` 04-E y añade una prueba AST de paridad para impedir que ambos contratos vuelvan a divergir. Runtime y harness usan versión 1.0.1 de forma coherente para que `runtime-status` y el restart B16 no bloqueen por un handshake de versión obsoleto. No hubo API/UI runtime, source write browser ni consumo de full regression antes del BLOCK; los gates PASS anteriores se reutilizan.

## Recovery-002 — FINDINGS transport/render/navigation parity

La ejecución Windows llegó con PASS hasta Browser B07. En B08 el backend validó el DRAFT inválido, creó un review `FINDINGS` y devolvió deliberadamente HTTP 403 porque BLOCK nunca se representa como HTTP 200. El cliente genérico convirtió ese 403 en `DevPilotApiError`; `ArtifactReviewFlow` descartaba `error.payload.data.review`, por lo que la UI mostraba el texto del finding pero no renderizaba el review ni el botón `Ir al hallazgo`. El análisis hacia adelante detectó además que el evento de navegación existente solo tenía consumidor en el editor MANUAL; un DRAFT IMPORT no escrito en source no podía posicionarse allí. Recovery-002 conserva la semántica HTTP fail-closed, recupera únicamente payloads 403 que contienen un review `FINDINGS` estructuralmente válido y añade navegación segura del finding al preview read-only del import DRAFT, ligada a `source_ref/import_id` y `relative_path`. No se relaja RBAC, no se convierte BLOCK en PASS/200, no se crea plan/approval y no se escribe source. La evidencia B08 previa se conserva como forensic y se repite únicamente B08 después del corrective.

## Recovery-003 — wrong-role runtime identity/auth-store parity

La ejecución Windows completó Recovery-002 y Browser B08 con FINDINGS navegables. En B11, `viewer04e.local` no pudo autenticarse y `/api/v1/auth/login` devolvió HTTP 401, por lo que el escenario no demostró RBAC wrong-role. El RCA estableció que `devpl_gsdlc_04_e_fixture_identity.py` provisionaba la identidad sintética en `fixture/.devpilot/auth/auth.db`, mientras la API real se inicia desde `D:\Projects\DevPilot_Local` y `AuthApplicationService` usa `repo/.devpilot/auth/auth.db`. El harness declaraba PASS por existencia del registro/credential handoff, pero no hacía un round-trip contra el mismo auth store ni contra la API viva. Recovery-003 provisiona/rota únicamente la identidad sintética exacta en el runtime auth store del API, prueba login+role viewer sin exponer el password, prueba adicionalmente un login HTTP real contra `127.0.0.1:8787`, ejecuta con esa sesión un POST sintético de decisión de approval que debe ser denegado por RBAC con HTTP 403 antes del handler, revoca la sesión de verificación y añade cleanup obligatorio después de B11. La identidad viewer legacy del fixture se elimina si coincide exactamente con el actor sintético. No se modifica la identidad owner, no se adjuntan credenciales/auth.db y full regression permanece en 0. La captura B11 de credenciales inválidas se conserva como forensic y se repite únicamente B11.

## Pendiente

Reanudar Windows desde Browser B11 con Recovery-003, demostrar viewer autenticado + RBAC deny, limpiar la identidad sintética, continuar B13/B09 en adelante, completar browser acceptance, exactly-once full regression, commit/candidate repo369 y owner adjudication final del backlog 04.

## Recovery-004 — cumulative corrective manifest parity

Recovery-003 bootstrap terminó PASS pero su preflight bloqueó prematuramente porque trató `ui/web/src/components/ArtifactImportWorkbench.ts` como dirty path desconocido. Ese path no era una mutación ajena: fue introducido legítimamente por Recovery-002 para habilitar la navegación de findings sobre el preview IMPORT y su hash coincide exactamente con el postimage sellado por Recovery-002. El error fue de ingeniería de evidencia: Recovery-002 amplió de hecho la superficie acumulada 04-E de 42 a 43 paths, pero el successor `SOURCE_DELTA_MANIFEST` se mantuvo erróneamente en 42. Recovery-004 corrige la autoridad acumulativa a 43 paths, exige que `ArtifactImportWorkbench.ts` coincida exactamente con el postimage Recovery-002, conserva bloqueo para cualquier otro dirty path y vuelve a entregar el corrective de identidad B11 sin repetir gates ni browser B00-B08. Full regression permanece en 0.


## Recovery-005 — canonical wrong-role identity for browser RBAC proof

Recovery-004 correctly repaired the auth-store binding and proved `viewer04e.local` could authenticate against the live API. The next browser attempt nevertheless rendered `Autenticación no disponible`. Runtime evidence showed the API remained healthy: browser login returned HTTP 200, but the subsequent `GET /api/v1/auth/session` returned HTTP 403. The synthetic `viewer` role was intentionally non-canonical, so server RBAC denied even the safe session-inspection route required by the UI bootstrap. As a result B11 could not reach an authenticated Project Shell and the test mixed two concerns: unknown-role fail-closed and wrong-role approval denial.

Recovery-005 does **not** widen RBAC. It changes only the synthetic test identity to `developer04e.local` with the already-canonical `developer` role. `developer` is allowed to inspect its authenticated safe session but is not in the approval-decision allowlist. The recovery requires three live proofs before browser B11: login HTTP 200, `GET /auth/session` HTTP 200 with role `developer`, and approval-decision POST HTTP 403 with exact finding `RBAC_ROLE_DENY`. The previous synthetic viewer identity/session and plaintext handoff are removed safely. Browser B11 is then repeated once; B00-B08 remain valid and full regression remains 0. The cumulative source authority remains 43 paths.


## Recovery-006 — B15 applied-state / rollback evidence continuity

La ejecución Windows completó B00–B14. En B15 el plan, approval y apply sobre `docs/baseline.md` sí terminaron HTTP 200 y generaron una ejecución UOC-005 persistente. Inmediatamente después, `ArtifactManualEditor` mostró `GSDLC04B_SOURCE_PREIMAGE_CONFLICT_BLOCK`: esto es un fail-closed esperado porque el runtime DRAFT activo conserva el preimage anterior mientras el source ya fue modificado por el apply gobernado. La guía anterior no distinguía ese conflicto del draft respecto de la autoridad de rollback y el operador se detuvo antes de solicitar rollback; el API log confirma que no hubo `rollback-approval-request` ni `rollback`. Recovery-006 no relaja optimistic concurrency ni altera el write engine. Añade dos gates machine-readable al harness: `rollback-preflight` demuestra el apply 200, execution ID recuperable, marker temporal aplicado y dirty scope exacto; `rollback-verify` exige approval separado + rollback 200, restored SHA igual al Git preimage, ausencia del marker, cero partial writes y dirty scope final limitado al artefacto de external drift B14. Browser evidence validation queda ligado a ese JSON PASS. B00–B14 se reutilizan y full regression permanece en 0.

## Recovery-007 — B15 state authority and safe replay

Recovery-006 blocked before convergence because its preflight required finding the literal temporary marker in `docs/baseline.md`. That condition was stronger than the available Windows proof: the API log established apply HTTP 200 and a recoverable UOC-005 execution, but did not prove that the physical file would still contain the marker at the next recovery boundary. Recovery-007 removes that accidental assumption. The harness now reads the persisted UOC-005 execution record and compares `status`, `pre_sha256`, `post_sha256`, the current raw source hash, immutable Git preimage and exact dirty scope. It classifies three explicit states: `ROLLBACK_ONLY`, `REPLAY_B15`, and `ALREADY_ROLLED_BACK`; unknown combinations fail closed. `REPLAY_B15` is allowed only when the old execution is still `applied`, the source is already Git-preimage-equivalent, rollback has not started and the only remaining fixture drift is the declared B14 artifact. This permits repeating only B15 once from a clean preimage while preserving the earlier execution as forensic evidence. The final rollback gate now additionally verifies the persisted execution record reaches `rolled-back-manual` and its recorded restored SHA equals the actual source. B00–B14 remain reusable and the unique full regression remains unconsumed.


## Recovery-008 — fresh-session rollback continuity attempt

Recovery-007 correctly classified B15 as `ROLLBACK_ONLY` and preserved the UOC-005 execution `uedit_20034a2ee02bbb564baa2d7b0914633d` with source equal to the persisted post SHA. The live API had two `POST .../rollback-approval-request` responses HTTP 401 and no successful rollback POST. Recovery-008 correctly proposed a fresh trusted runtime, owner reauthentication and the inline rollback approval card, but its own preflight blocked **before convergence** because its HTTP evidence parser was method-insensitive.

## Recovery-009 — method-aware HTTP evidence parsing + fresh-runtime rollback continuation

Recovery-008 misclassified the CORS transport preflight `OPTIONS .../rollback-approval-request HTTP 200` as if it were a successful `POST`. Recovery-009 requires exact **HTTP method + path + status**. The supplied Windows evidence contains one OPTIONS 200, two POST 401, zero rollback-approval POST 200 and zero rollback POST 200; therefore no rollback approval exists and B15 remains safely recoverable from the same persisted `applied` execution. Recovery-009 preserves the fresh-runtime strategy: stop the trusted historical API/UI processes, start new Consoles 2/3, reauthenticate `owner.local`, recover the exact execution and use the inline rollback approval card in the same tab. B00-B14 remain reusable and the unique full regression remains 0 until browser acceptance is complete. Final B15 proof is bound to `15_rollback_preflight_v1_0_9.json` and `15_rollback_verify_v1_0_9.json`.


## Recovery-010 — state-aware fresh-runtime fixture dirty policy

Recovery-009 completed bootstrap, preflight, converge and validate, then stopped the historical API/UI runtime successfully with both ports free. Starting the fresh API in a new Console 2 blocked before child process creation because `devpl_gsdlc_04_e_runtime_console.py` used a static browser dirty-path allowlist that omitted `docs/baseline.md`. That static rule was correct for normal browser operation but incorrect for the exact B15 rollback recovery checkpoint already proven by Recovery-009: persisted UOC-005 execution `applied`, current `docs/baseline.md` equal to the execution `post_sha256`, immutable Git blob equal to the execution `pre_sha256`, and dirty scope exactly `docs/baseline.md` + the declared B14 drift artifact.

Recovery-010 does not broadly allow `docs/baseline.md`. Runtime Console v1.0.2 authorizes that dirty path only when all of the following agree: Recovery-009 PASS preflight with `ROLLBACK_REAUTH_NEW_RUNTIME`, exact execution ID, persisted UOC-005 record status `applied`, current raw SHA equal to persisted post SHA, immutable Git blob SHA equal to persisted pre SHA, exact two-path dirty scope, no rollback verification already sealed, and no full-regression marker. Any mismatch remains BLOCK. Harness runtime-version authority advances to 1.0.2 and B15 machine evidence uses Recovery-010 filenames. The fresh-runtime strategy remains unchanged: start new API/UI, reauthenticate owner, recover the same execution, use the inline rollback approval card, verify `rolled-back-manual`, then continue B16/B17/parity/browser closure. B00-B14 remain reusable and full regression remains 0.


## Recovery-011 — execution-bound server-active project-context recovery

Recovery-010 successfully started a fresh API/UI runtime and authenticated `owner.local`, but the exact deep link to `/workspace/documents` was redirected to Project Home. Runtime evidence shows authentication itself was healthy (`POST /auth/login 200`, `GET /auth/session 200`). The attempted `Open Existing` recovery then produced `POST /project-entry/dry-run 200`, `POST /project-entry/revalidate 200` and `POST /project-entry/execution-approval-request 200`, but **no** `POST /project-entry/execute`. Consequently the UI-only `ProjectJourneyContext` never returned to `phase=project`, and the project-scoped route guard behaved as designed by redirecting to Project Home.

The root defect is a recovery-boundary mismatch: after fresh login, `sessionStorage` is intentionally cleared, while the API runtime already has an explicit PathGuard-approved active browser fixture and the persisted UOC-005 execution is still authoritative. Requiring a new Project Entry mutation/approval merely to reconstruct UX navigation expands the state surface and is unrelated to the B15 rollback-only checkpoint.

Recovery-011 introduces a narrowly bounded recovery path. Only `/workspace/documents` with `recover_project_context=server-active`, a syntactically valid `execution` and `document` may attempt it. After authenticated session validation, the UI reads existing `/settings/workspace` and `/workspace/edit-executions/{id}` endpoints. It restores only `sessionStorage` UX context when the server workspace is configured, valid, read-only, network/external-api/mutation free, and the persisted execution ID/document/status exactly match. It does **not** call Project Entry dry-run, approval or execute, does not grant server authorization and does not alter the normal GSDLC-03 Create/Open/Import journey. Any mismatch falls through to the existing Project Home guard.

Recovery-011 also preserves the complete `pathname + query string` through authentication redirects, preventing loss of `execution`, `document`, handoff and recovery parameters after login. The login/first-run loop protection remains fail-closed.

The cumulative 04-E source authority expands from 43 to 45 paths because `ui/web/src/main.ts` and `ui/web/src/api/client.ts` are legitimate product corrections not previously touched by 04-E. No route, schema, server RBAC, approval or write engine is added. The Windows harness advances only its evidence identity to v1.0.11; Runtime Console remains v1.0.2. B00-B14 and the persisted B15 apply evidence remain reusable, and the unique full regression remains unconsumed until browser acceptance passes.



## Recovery-014 — terminal browser-login continuity recovery

Recovery-013 proved that source, B15, runtime binding and focused/build gates remained healthy, but real browser evidence showed a second redirect to Project Home after successful `owner.local` authentication. The fresh API segment contains `POST /auth/login 200` and `GET /auth/session 200` but no subsequent `GET /api/v1/settings/workspace` and no exact `GET /api/v1/workspace/edit-executions/{execution_id}`. Therefore the Recovery-011 server-authority restoration function was not reached; the remaining defect is continuity of the explicit recovery intent across Login → return, not B15, RBAC, UOC-005 or the artifact lifecycle implementation.

Recovery-014 is the terminal recovery. It stores only a short-lived same-tab UX recovery intent (`execution_id`, `document_id`, canonical target, TTL) in `sessionStorage` before redirecting to Login. After authentication it reconstructs the canonical `/workspace/documents?recover_project_context=server-active...` target from that intent instead of trusting a potentially transformed `return` query. Project context is still restored only after the existing read-only server checks on `/settings/workspace` and `/workspace/edit-executions/{id}`; the intent itself grants no authorization and cannot execute Project Entry. A failed explicit recovery is surfaced as a deterministic recovery failure and the intent is cleared.

The Windows operator records an API-log offset before the manual browser action. Browser verification accepts PASS only if, after that offset, the exact read-only workspace/execution GETs occur and there are zero Project Entry POSTs. If this terminal continuity proof fails, no Recovery-015 is authorized: GSDLC-04-E must be reimplemented cleanly from the 04-D authority instead of extending the recovery chain.


## Post-full composite recovery — unique full consumed

The unique GSDLC-04 full regression was executed exactly once after browser acceptance and is permanently consumed. Result: `2557 passed / 33 failed / 0 errors / 5 skipped`. A rerun is prohibited. Root-cause analysis reduced the 33 nodeids to five deterministic classes: successor UI lineage, SecretGuard synthetic credential literals, OpenAPI/ApplicationService/mapping drift, historical tests reading mutable current-active authorities, and the frozen UOC-011 source budget being applied to the later GSDLC UI.

The authorized recovery is the backlog-defined composite path only: exact failed-nodeid retest, bounded impacted retest, Historical Regression Guard, then composite closure. Browser B00-B17, rollback evidence, parity evidence and the unique full artifacts remain immutable and are not rerun. The source authority may grow from 45 to 56 paths only through the 11 explicitly classified current-active successor corrections. Frozen historical snapshots are preserved.

**Composite decision:** `PASS-CANDIDATE / original full consumed once + prior exact retest 25/33 + residual 8/8 PASS + bounded impacted + Historical Regression Guard PASS; full was not rerun.`. Owner adjudication and GSDLC-05 authorization remain blocked until composite evidence is PASS.
