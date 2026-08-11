---
doc_id: "DEVPL-UOC-006-GOVERNED-GIT-OPERATIONS-REPORT"
title: "UOC-006 — Governed Git Operations Implementation Report"
status: "implemented-initial"
version: "1.0.2"
owner: "Ordóñez"
updated: "2026-08-10"
approval: "pending_windows_browser_closure"
---

# UOC-006 — Governed Git Operations

## Objetivo

Implementar el subset Git gobernado definido por el backlog UOC-006 sin exponer shell, argumentos Git libres ni operaciones remotas/destructivas.

## Arquitectura implementada

`WorkspaceGitOperationsApplicationService` es el boundary de aplicación. El adapter histórico `GitAdapter` continúa estrictamente read-only. Las mutaciones se encapsulan en `GovernedGitMutationAdapter`, que solo expone operaciones tipadas: staging exacto, un commit local exacto y creación de un branch ref local desde HEAD.

Flujo commit:

`status/diff → immutable commit plan → approval de staging → recheck HEAD/hash → exact staging → deterministic pre-commit validation → commit-intent hash → approval independiente de commit → explicit identity commit → post-commit parent/path/index verification → evidence record`.

Flujo branch:

`clean worktree → branch plan ligado a HEAD → approval → create local branch ref → verify ref; no checkout y no push`.

## Seguridad

- documentos seleccionados por opaque `document_id`, nunca por path libre del browser;
- allowlist documental y `SecretGuard` antes del staging y sobre el contenido real del index;
- máximo inicial de 20 archivos / 2 MiB;
- pre-existing staged state bloquea el plan;
- delete/rename bloqueados en esta primera versión;
- approval binding a actor/role/tool/action/plan hash/scope/TTL;
- approval de staging y commit separados;
- commit identity explícita;
- hooks de repositorio no se ejecutan (`--no-verify`) para evitar ejecución arbitraria; las validaciones internas DevPilot se ejecutan antes;
- `reset --hard`, rebase, push/force-push, branch delete, checkout/switch, tag y argumentos libres no están expuestos;
- toda mutación es local-first; external API/network no son requisito.

## UX

La superficie se integra en `/workspace/documents` mediante progressive disclosure. La primera versión opera desde el documento seleccionado en UI; el Application Service admite un conjunto acotado de documentos. Se muestran hashes, approval IDs, stage/commit state, no-go Git y branch creation separada. El botón `Recargar trazabilidad` usa exactamente el styling compartido `validation-action-button`.

## Estado

`implemented-initial / pending Windows browser + Git closure`.

UOC-007 permanece no autorizado hasta PASS del cierre completo de UOC-006.

## Riesgos y limitaciones

- ejecución síncrona inicial; jobs persistentes/heartbeat/cancelación pertenecen a UOC-007/UOC-008;
- no se implementa push ni publicación remota;
- no se implementan renames/deletes en staging gobernado inicial;
- branch create crea el ref y no cambia el branch activo;
- no existe commit signing en esta primera versión; `commit.gpgSign=false` es explícito;
- la UI inicial planifica un documento activo por interacción para reducir complejidad visual.

## PASS/BLOCK

PASS de implementación controlada requiere schemas, contratos service/API/UI, Approval/RBAC/MIASI, route registries, Test Impact, TypeScript/Vite/smokes y negative no-go sin relajación de validators. El cierre definitivo requiere Windows/browser/Git/evidence/repo334.


## Validación controlada previa a Windows

- Test Impact v2: 60 paths, 157 contratos matched, 62 P0, 86 P1, 220 tests recomendados y 0 paths unmatched.
- Suite Python focal/acumulativa: 171 PASS antes del último guard de secreto; después de añadir ese guard se reejecutó `test_workspace_git_operations_service.py` y obtuvo 6/6 PASS. El guard nuevo bloquea contenido tipo `OPENAI_API_KEY` antes de producir un staging plan y confirma index vacío.
- TypeScript `--noEmit`: PASS con TypeScript 5.8.3.
- UI smokes: smoke, visual, operator-flow y route-enforcement, 4/4 PASS.
- MIASI validate PASS; MIASI semantic PASS con warnings de madurez `controlled_write`/RBAC no bloqueantes.
- TCR v1 PASS; TCR v2 PASS con dos `NEEDS_REVIEW` heredados y no bloqueantes; Project State PASS; Documentation Governance PASS.
- Vite build no se declara PASS en el entorno controlado porque el source tree limpio no incluye `node_modules` y el tarball offline de Vite 6.4.3 no estaba cacheado. La compilación Vite es un gate obligatorio en Windows antes de browser acceptance.
- No se ejecutó full regression: Test Impact y el alcance permiten validación impactada; cualquier fallo Windows en contratos históricos/globales bloquea el cierre y exige adjudicación antes de continuar.

## Windows Git staging portability correction (payload 1.0.2)

The initial UOC-006 staging verifier compared the SHA-256 of the raw worktree
bytes captured in the immutable plan with the SHA-256 of the Git index blob.
That is not a valid cross-platform invariant when Git clean filters transform
content while staging (most visibly `core.autocrlf=true`, where CRLF worktree
bytes become LF index bytes). The approval-bound raw worktree SHA-256 remains
part of the optimistic-concurrency recheck before staging, but post-stage
identity is now verified with Git's own canonical object model:

- after exact `git add`, `git diff --quiet --no-ext-diff -- <path>` must prove
  Git-semantic equivalence between the current worktree path and the index;
- this correctly accepts Git-for-Windows CRLF→LF normalization without treating
  different raw bytes as a content drift;
- the SHA-256 of the exact staged bytes remains in the index fingerprint used
  for the independent commit approval and post-approval drift recheck.

The UOC-006 fixture explicitly uses CRLF worktree bytes plus
`core.autocrlf=true`, so Linux CI now reproduces the Git-for-Windows staging
semantics that exposed this defect. This is a portability hardening correction,
not a relaxation of approval, SecretGuard, staged-set or pre-commit controls.

### Validación de portabilidad v1.0.2

La recuperación del fallo Windows R10B se validó en un fixture determinista con
worktree CRLF y `core.autocrlf=true`. Los tres casos que fallaron en Windows
(stage service, commit service y API end-to-end) pasan con el nuevo contrato de
equivalencia Git; la suite dirigida completa queda en 152 PASS / 0 FAIL /
0 ERROR / 0 SKIP, ejecutada en tres grupos equivalentes para evitar timeouts del
entorno de validación. MIASI structural/semantic, TCR v1/v2, Project State y
Documentation Governance permanecen PASS; los warnings semánticos existentes
continúan siendo no bloqueantes y no fueron ocultados.
