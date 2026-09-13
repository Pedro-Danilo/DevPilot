---
doc_id: "PROMPT-DEVPL-GSDLC-12-B"
title: "DEVPL-GSDLC-12-B — Branch/external edit reconciliation and conflict UX"
status: "approved"
version: "1.0.1"
owner: "Ordóñez"
updated: "2026-09-12"
approval: "approved_by_owner"
precondition: "GSDLC-12-A CLOSED/PASS/WINDOWS-VALIDATED"
execution_source_policy: "immediate Windows-validated successor of GSDLC-12-A"
full_regression_budget: "0 in 12-B by routine; GSDLC-12 budget remains 0/1 unless owner-approved hard trigger consumes it"
browser_policy: "required for conflict/reconciliation UX introduced by 12-B"

source_repo: "repo_DevPilot_Local_426_DEVPL_GSDLC_12_A_PERSISTENT_RESUMABILITY_RECOVERY_LOCKS_WINDOWS_VALIDATED_CANDIDATE.zip"
source_commit: "f79f5d32c928247039feeecb9c773b75343b6a2e"
source_repo_sha256: "b366fd4587bc057e8330fa419c7972fcdec6a8daaf66acd00b587da88f89bf66"
rebound_policy: "immediate-windows-validated-successor-of-12-A; FRX-v2.4 current-active"
---

# Objetivo

Detectar y reconciliar branch switch, HEAD divergence/rewind y ediciones externas sin pérdida de datos ni Git destructivo, haciendo los conflictos visibles y recuperables desde la UI.

# Implementación requerida

1. Resolver el execution source únicamente desde el successor Windows-validado de 12-A; no codificar número de repo futuro en lógica.
2. Definir `WorkspaceDriftSnapshot`/equivalente con branch, HEAD, tree/preimage hashes, rename/delete/add/modify classification y engineering-state binding.
3. Detectar: branch switch, detached HEAD, fast-forward externo, rewind, divergent commit, dirty tracked, untracked relevante, rename, delete y cambio de archivo ligado a plan/draft/evidence.
4. Clasificar drift por efecto: `NO_CONFLICT`, `REVALIDATE`, `REPLAN_REQUIRED`, `MANUAL_RECONCILIATION_REQUIRED`, `READ_ONLY_BLOCK`.
5. Implementar `ConflictResolutionView` con diff/resumen, causa, riesgo, evidencia y planes seguros. Prohibir `reset --hard`, rebase automático, checkout destructivo o overwrite silencioso.
6. Toda adopción/reconciliación mutante debe ser typed operation, dry-run, PathGuard, Git authority, RBAC/approval cuando aplique, verify/evidence.
7. Invalidar approval/preimage/plan cuando el drift afecte su authority binding.
8. Mantener drafts recuperables cuando sea seguro; ofrecer export/copy antes de cualquier decisión que descarte estado UX.
9. Actualizar Project Status con conflicto explícito y next action determinística; no ocultar conflicto detrás de un estado genérico.
10. Reconciliar contratos históricos/current-active y registries derivados antes del cierre.

# Pruebas mínimas

- branch switch benigno y conflictivo;
- HEAD fast-forward, rewind y divergence;
- dirty worktree, rename/delete/add;
- external edit sobre archivo con pending plan/preimage;
- stale approval invalidation;
- no-destructive-Git negative suite;
- no data loss en drafts;
- duplicate/multi-session conflict interaction con locks de 12-A;
- Test Impact + focal/acumulativa. `Full Regression = 0`.

# Browser acceptance obligatorio

Una ejecución real-browser debe demostrar al menos dos conflictos distintos, uno recuperable por revalidation y otro que requiera manual reconciliation, mostrando diff/resumen y sin ejecutar Git destructivo. Capturas + `conflict_matrix.json`/verifier.

# Evidencia mínima

- `conflict_matrix.json`;
- reconciliation report con Git identity pre/post;
- screenshots/verifier;
- no-destructive-operation evidence;
- source delta/Test Impact/HCA/Contract Reconciliation;
- S0/S1.

# PASS/BLOCK

**PASS:** todo drift relevante produce estado explícito; no hay overwrite silencioso; approvals/preimages stale se invalidan; usuario puede recuperar de forma segura; S0/S1=0.

**BLOCK:** pérdida de datos, reset/rebase/checkout destructivo automático, ejecución con authority stale, conflicto oculto o branch/HEAD incorrectamente reconciliado.

# Salida

Autoriza GSDLC-12-C solo después de PASS Windows.

## Reglas transversales obligatorias

- Ingeniería acumulativa: partir únicamente del successor Windows-validado inmediato; nunca retroceder a repo425 ni a otro histórico después de que exista un successor válido.
- `dry-run` por defecto; toda mutación sensible sigue `plan → dry-run → policy/RBAC → approval cuando aplique → execute → verify → evidence`.
- Prohibidos `reset --hard`, `git clean`, force push, rebase destructivo, borrados implícitos, publish o deploy remoto.
- No arbitrary shell desde el usuario. Jobs y mutaciones son operaciones tipadas/allowlisted.
- Runtime stores, secretos, `.git`, `.venv`, `outputs/`, `.pytest_cache/`, `__pycache__/`, `node_modules/`, `auth.db*`, `devpilot.db*` y equivalentes quedan fuera de fixtures/packages finales.
- Operadores Windows: Python preferido; pequeños, reentrantes, idempotentes por evidencia/commit/contenido y state-aware. No asumir cwd, `git common-dir`, remotes, branches ni procesos previos.
- LF/CRLF no puede provocar BLOCK: usar contenido Git o comparación semántica UTF-8/LF.
- Drifts documentales no críticos y acotados se corrigen dentro del micro-sprint activo o del siguiente natural; no crear sprint/operator/repo aislado solo por drift.
- HCA + Contract Reconciliation proporcional antes del cierre de cada micro-sprint; no reescribir hechos históricos para hacer pasar contratos current-active.
- Evidencia PASS hash-bound se reutiliza cuando el corrective no toca esa superficie; no repetir browser ni pruebas costosas por rutina.
- Cada guía Windows resultante será una sola `.md`, pasos consecutivos, orientada a personal beginner-medio, bundle desde `C:\Users\Pedro\Downloads`, y cada comando PowerShell físicamente en una sola línea.
- API/UI solo cuando corresponda, siempre foreground; para browser usar tres consolas separadas: operador, API `8787`, UI `5173`.
- Cada cierre registra explícitamente `network_used`, `external_api_used`, `secrets_exposed`, `mutations_performed`, identidad Git pre/post, S0/S1 y hashes de artefactos.
- A→D: no Full por rutina. E: única logical Full del backlog salvo hard trigger previo owner-approved que ya haya consumido el budget. FAIL funcional = preservar y NO RERUN; recovery composite selectivo obligatorio.


## Rebound repo426 — ejecución 2026-09-12

Este prompt queda materializado contra el successor Windows-validado inmediato de 12-A: `repo_DevPilot_Local_426_DEVPL_GSDLC_12_A_PERSISTENT_RESUMABILITY_RECOVERY_LOCKS_WINDOWS_VALIDATED_CANDIDATE.zip`, commit `f79f5d32c928247039feeecb9c773b75343b6a2e`, SHA-256 `b366fd4587bc057e8330fa419c7972fcdec6a8daaf66acd00b587da88f89bf66`. La cadencia FRX v2.4 permanece: Test Impact + focal/acumulativa en 12-B, Full Regression = 0, budget GSDLC-12 = 0/1 reservado para 12-E.
