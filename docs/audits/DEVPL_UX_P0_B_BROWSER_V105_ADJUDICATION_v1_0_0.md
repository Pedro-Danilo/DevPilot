---
doc_id: DEVPL-UX-P0-B-BROWSER-V105-ADJUDICATION
status: current
version: 1.0.0
updated: 2026-09-15
baseline_repo: repo_DevPilot_Local_432_DEVPL_UX_P0_B_PRODUCT_APP_SHELL_WINDOWS_VALIDATED_CANDIDATE.zip
baseline_commit: 0136c3cac5d10ef8c647f96e38423f4940cadb6c
baseline_sha256: 527fdf14b91af19638c45dc2b578c834cab8a137c686c582bcd5ffdb84330a76
adjudication: BLOCK
---

# DEVPL-UX-P0-B — Browser v1.0.5 adjudication

## Veredicto

El receipt automático/manual `browser_validation=PASS` no es suficiente para cerrar UX-P0-B porque las capturas reales contradicen dos invariantes funcionales del sprint.

## Evidencia visual

Las capturas `browser_v105` muestran:

- Project Status con `PROYECTO=unknown`, `ETAPA=unknown`, `ESTADO=EMPTY`;
- Next Action degradada a `STATE_AUTHORITY_UNAVAILABLE`;
- `Acceso local no autorizado` / HTTP 403 en Project Status;
- Recovery con contexto de proyecto no resuelto;
- logs API con 403 para `/api/v1/recovery` y `/api/v1/reconciliation`.

La navegación agrupada, responsive layout y diferenciación Guided/Expert sí se renderizan, pero el contrato de contexto server-authoritative no queda demostrado.

## Causa raíz

`UiWorkspaceContextResolver._from_active_root()` derivaba el identificador lógico del workspace mediante `root.name`. En Windows el root físico es `DevPilot_Local`, mientras el project authority y el scope RBAC usan `devpilot-local`. Recovery y Reconciliation comparan scopes contra `active_workspace_id`, por lo que la diferencia de representación produce un 403 legítimo.

## Decisión

- UX-P0-B permanece abierto.
- repo432 se preserva como candidate fallido de aceptación browser, no se reescribe.
- el correctivo parte de repo432 y produce un successor nuevo;
- UX-P0-C permanece bloqueado hasta el cierre Windows/browser del correctivo.
- Full Regression sigue prohibida en B.
