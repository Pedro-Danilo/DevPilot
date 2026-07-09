---
doc_id: POST-H-028-D-OPERATOR-FLOW-SMOKE-REPORT
title: "POST-H-028-D — Operator flows and error states"
version: "1.0.0"
updated: "2026-07-09"
owner: Ordóñez
status: approved
approval: "approved"
source_of_truth: true
created_by: POST-H-028-D
---

# POST-H-028-D — Operator flows and error states

## Decisión

`implemented-initial / PASS` para el alcance local-first de POST-H-028-D.

POST-H-028-D madura la shell UI/API para que el operador vea estados, errores, bloqueos y siguientes acciones sin leer logs crudos ni código. El sprint agrega un smoke report schema-backed que cruza API local in-process con contratos fuente de la Web UI.

## Alcance implementado

- `OperatorFlowSmokeReport` como contrato JSON validable.
- `OperatorFlowSmokeRunner` como runner local de flujos de operador.
- CLI `python -m devpilot_core api operator-flow-smoke --json --write-report`.
- Verificación de API down, token missing, token invalid y 401/403 visibles.
- Verificación de empty states de Report Viewer y Trace Viewer.
- Verificación de settings/providers y security posture con secretos redactados.
- Verificación de Action Launcher con allowlist `readiness`, `code-review`, `refactor-plan`.
- Verificación de acción prohibida `patch-apply` como `BLOCK`, no como éxito.
- Verificación de Approval Center create/list/show/decision dentro de sandbox runtime temporal.
- Verificación de Operator Dashboard con no-go gates y recommended next actions visibles.
- Script Node dependency-light `npm --prefix ui/web run test:operator-flows`.

## Corrección aplicada

El Approval Center usaba `actor: ui-local` para crear/decidir approvals demo, pero el actor gobernado existente para flujo local es `local-owner`. Se corrigió a `local-owner` para que el flujo create/list/decision sea consistente con RBAC local y con `tests/test_api_approvals_actions.py`.

## Límites explícitos

- No es una suite E2E browser industrial completa.
- No implementa login, RBAC multiusuario, OIDC, SSO ni sesiones persistentes.
- No ejecuta acciones críticas ni habilita patch apply/refactor execute/rollback/git push/deploy.
- No arranca servidor, no abre sockets y no usa red externa.
- El flujo de approvals se prueba en sandbox runtime temporal para no mutar la DB operacional real del repo.
- POST-H-028-E queda pendiente para enforcement bloqueante del UI route registry.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_operator_flows_error_states.py `
  tests/test_api_reports_traces.py `
  tests/test_api_approvals_actions.py `
  tests/test_api_settings.py `
  tests/test_post_h_015_operator_dashboard_application_api.py `
  tests/test_post_h_015_operator_dashboard_ui.py `
  tests/test_web_ui_mvp.py `
  -q

python -m devpilot_core api operator-flow-smoke --json --write-report
python -m devpilot_core schema validate --schema-id OperatorFlowSmokeReport --instance outputs/reports/operator_flow_smoke_report.json --json
npm --prefix ui/web run test:operator-flows
```

## PASS/BLOCK

PASS requiere que los diez flujos mínimos estén cubiertos: API down, token missing, token invalid, dashboard ready, reports empty, traces empty, approval lifecycle, dry-run allowed actions, forbidden action BLOCK y settings redacted.

BLOCK si la UI queda en blanco ante API down, oculta BLOCK como éxito, expone acciones no-go como disponibles, muestra tokens/secretos raw o sugiere exponer la API fuera de localhost como remedio.
