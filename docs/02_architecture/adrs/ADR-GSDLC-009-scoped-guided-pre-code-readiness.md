---
doc_id: "DEVPL-ADR-GSDLC-009"
title: "ADR-GSDLC-009 — Scoped Guided Pre-code readiness profile"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-08-25"
approval: "approved_by_owner_backlog_scope"
program_id: "DEVPL-GSDLC"
backlog_id: "DEVPL-GSDLC-05"
micro_sprint: "DEVPL-GSDLC-05-E"
---

# ADR-GSDLC-009 — Scoped Guided Pre-code readiness profile

## Estado

`approved` dentro del alcance owner-approved de `DEVPL-GSDLC-05-E`.

## Contexto

GSDLC-05-E debe demostrar por navegador el milestone `PRE_CODE_READY` para siete etapas obligatorias: Product Vision, Scope, Requirements, Architecture, Security, Test Strategy y Traceability. DevPilot ya conserva contratos históricos de readiness con alcance más amplio. Reducir esos contratos históricos a siete artefactos sería una regresión documental y violaría la política successor-aware.

## Decisión

Se introduce el perfil successor `guided-pre-code-manual-v1`, acotado al milestone de GSDLC-05-E. Su PASS exige, para cada una de las siete etapas, `FROZEN`, source existente, `actual_sha256 == approved_sha256` y ArtifactProfile válido. El perfil no reemplaza ni relaja el readiness histórico global (`historical_global_readiness_replaced=false`).

La autoridad de promoción continúa siendo `ArtifactReviewApplicationService` + `WorkspaceEditExecutionApplicationService`; el wizard no introduce un writer paralelo. El flujo es `DRAFT → validate/findings → immutable plan/diff → approval → apply → freeze`.

## Consecuencias

- Permite demostrar el milestone manual pre-code sin falsificar el readiness global.
- Conserva snapshots y tests históricos.
- GSDLC-06 y sucesores podrán extender o componer el perfil mediante successors explícitos.
- Esta es una primera versión industrializable del milestone; no declara que todos los readiness futuros se reduzcan a siete documentos.

## Seguridad

- Human Session/RBAC/Approval siguen server-side.
- No LLM, red ni API externa.
- DRAFT no escribe source.
- Source write solo ocurre en apply approval-bound.
- Runtime stores `auth.db*`, `devpilot.db*` y `outputs/` se excluyen de release/evidence source archives.

## PASS / BLOCK

PASS si las siete etapas quedan FROZEN con hashes exactos y ArtifactProfile válido, sin modificar readiness histórico. BLOCK si una etapa puede saltarse, si PRE_CODE_READY se alcanza con artefactos preinyectados o si se relaja un contrato histórico para obtener PASS.

## Verificación

`tests/test_devpl_gsdlc_05_e_pre_code_wizard.py` y los sweeps de GSDLC-05-E son la verificación focal de esta ADR.


## 2026-08-26 — BLOCK-09 addendum: contextual pre-code actions and workspace scope

For the GSDLC-05-E integrated vertical slice, an Advisor action may be handled by the current wizard when the action kind maps directly to a stage-local governed authoring mode. `UPLOAD_IMPORT` for an IMPORT-capable stage therefore opens the local browser file input in `/pre-code`; the generic `/workspace/documents` navigation remains a fallback for surfaces that are not integrated into the current wizard. The Advisor still grants no capability: server policy/RBAC and the stage profile remain authoritative.

For authenticated workspace-scoped API routes that predate explicit `workspace_scope_source=active-server-context`, the API middleware may derive a missing caller workspace from a valid server UI context that is present in the principal's scopes, or from the principal's single unambiguous workspace scope. Explicit conflicting caller workspace ids remain denied and ambiguous multi-scope requests fail closed. This avoids the historical `devpilot-local` default being treated as authority for an externally activated project.


## BLOCK-12 amendment — capability composition and historical snapshot isolation

The single 05-E full regression exposed a compatibility boundary not visible in focal gates. Later Guided-SDLC capabilities MUST NOT become eager constructor prerequisites for the generic `ApplicationService` used by historical/minimal workspaces. Optional capability facades are therefore composed lazily and remain strict when actually invoked.

Likewise, historical regression contracts MUST bind historical assertions to frozen `*_at_close` / `*_snapshot` authorities. Mutable `current` pointers, route registries, counters and active budgets may evolve under explicit successor contracts and MUST NOT be compared for exact equality with old snapshots.

For Project Status, MIASI applicability is a current overlay only when its policy authority exists. Historical/minimal roots that predate MIASI retain their neutral persisted projection; if the policy file exists but is malformed, evaluation remains fail-closed.

This amendment does not weaken GSDLC-05-E readiness, Advisor, RBAC, approval or MIASI enforcement in current authoritative roots.
