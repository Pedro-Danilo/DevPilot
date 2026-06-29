---
doc_id: "POST-H-014-E-QUALITY-GATE-REPORT"
title: "POST-H-014-E — Quality gate UI/API industrial shell"
status: "approved"
owner: "Ordóñez"
phase: "POST-FASE-H"
created_by: "POST-H-014-E"
preliminary: true
---

# POST-H-014-E — Quality gate UI/API industrial shell

Estado: `implemented-initial`.

POST-H-014-E integra la shell local UI/API al quality gate mediante el subgate `ui-api-industrial-shell`. La implementación consolida los controles acumulados de POST-H-014-A/B/C/D: contratos de rutas API, contratos de rutas UI, response mapping homogéneo, security posture local, smoke test Web UI y documentación operacional.

## Artefactos ejecutables

- `src/devpilot_core/interfaces/api/shell_gate.py`: `UiApiIndustrialShellGate` y generación opcional de `outputs/reports/ui_api_shell_report.json`.
- `docs/schemas/ui_api_shell_report.schema.json`: contrato JSON del reporte final UI/API.
- `src/devpilot_core/quality/gate.py`: integración del subgate en perfiles `hardening` e `industrial`.
- `src/devpilot_core/cli.py`: comando `python -m devpilot_core api shell-gate --json --write-report`.
- `tests/test_post_h_014_ui_api_shell_gate.py`: suite focal del cierre.

## Criterio de cierre

El micro-sprint pasa si:

1. `quality-gate run --profile hardening` incluye `ui-api-industrial-shell`.
2. `ApiRouteContractRegistry` y `UiRouteContractRegistry` validan sin drift.
3. `npm --prefix ui/web test` emite `DEVPL WEB UI SMOKE TEST: PASS`.
4. `outputs/reports/ui_api_shell_report.json` valida contra `UiApiShellReport`.
5. No se habilitan `remote_execution`, `connector_write`, `plugin_execution` ni APIs externas.

## Límites

Esta versión no declara DevPilot como producto SaaS listo para producción. Es una base local industrial `implemented-initial`: no hay OIDC, multiusuario, despliegue cloud, ejecución remota, conectores write ni plugins ejecutables.
