---
doc_id: "DEVPL-GSDLC-13-B-03-BLOCK-ADJUDICATION"
title: "DEVPL-GSDLC-13-B-03 — Project Status EMPTY/UNKNOWN block adjudication"
status: "reviewed"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-09-22"
approval: "chatgpt-adjudicated"
---

# DEVPL-GSDLC-13-B-03 — Adjudicación del BLOCK

## Propósito

Preservar la causa raíz y el alcance autorizado del corrective para el primer BLOCK de `13-B-03`.

## Estado

`BLOCK / DEVPL_PRODUCT_CONTRACT_GAP / ACTIVE-CORRECTIVE`.

## Veredicto

`13-B-03-00 = BLOCK / DEVPL_PRODUCT_CONTRACT_GAP / ACTIVE-CORRECTIVE`.

El start state fue correcto: repo438 limpio/sincronizado, Project Shell existente y Git clean. La UI resolvió el workspace `inventory-sales-local-greenfield`, pero Project Status devolvió `project=unknown`, `phase=unknown`, `ui_state=EMPTY` y `STATE_AUTHORITY_UNAVAILABLE`.

## Causa raíz

B-02 persistió autoridad target-local (`project.yaml`, bootstrap receipt y workspace registration), pero no materializó el estado operacional que Guided SDLC usa para Project Status:

- registry runtime activo para `GuidedSDLCService`;
- `outputs/workspaces/<workspace_id>/engineering_state.json`.

El launcher B-03 enlazó `DEVPILOT_UI_ACTIVE_WORKSPACE_ROOT`, por lo que `UiWorkspaceContextResolver` sí identificó el workspace. Sin embargo, `GuidedSDLCService.from_platform_root()` siguió usando el registry histórico por ausencia de `DEVPILOT_GUIDED_SDLC_WORKSPACE_REGISTRY_PATH`; aun con el registry correcto, no existía un WorkspaceEngineeringState del greenfield.

El repo ya documentaba esta clase de causa en GSDLC-05-E BLOCK-03. Reinyectar manualmente registry/state desde la Run Card ocultaría un defecto real del lifecycle B-02 → B-03.

## Corrective

1. Persistir active-project runtime registry bajo `outputs/runtime/` al completar un CREATE_NEW GSDLC-13.
2. Inicializar un WorkspaceEngineeringState mínimo, reconstruible, bajo `outputs/workspaces/<id>/`, sin escribirlo dentro del greenfield.
3. Hacer que el launcher estándar `api serve` cargue automáticamente ese contexto persistido.
4. Para el greenfield ya creado, ejecutar un backfill correctivo mediante código DevPilot, comprobando que Git y metadata del proyecto no cambian.
5. Mantener PathGuard/RBAC/approval fail-closed.

## No-go

- no escribir estado de ingeniería manualmente desde PowerShell;
- no modificar `.devpilot/workspaces/workspace_registry.json` histórico;
- no añadir artifacts funcionales al greenfield;
- no ejecutar Full Regression;
- no continuar al restart hasta validar/promover el corrective.
