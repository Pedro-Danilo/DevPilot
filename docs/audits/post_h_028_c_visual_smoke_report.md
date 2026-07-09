---
doc_id: POST-H-028-C-VISUAL-SMOKE-REPORT
title: "POST-H-028-C — Visual smoke tests"
version: "1.0.0"
updated: "2026-07-08"
owner: Ordóñez
status: approved
source_of_truth: true
created_by: POST-H-028-C
---

# POST-H-028-C — Visual smoke tests

## Decisión

`implemented-initial / PASS` para el alcance local-first de POST-H-028-C.

POST-H-028-C agrega un reporte schema-backed y dependency-light para validar que las vistas críticas de la consola local UI/API sean renderizables, tengan marcadores visuales mínimos, expongan estados operacionales clave y preserven la frontera API-only.

## Alcance implementado

- `UiVisualSmokeReport` como contrato JSON validable.
- `UiVisualSmokeReporter` como runner local y read-only.
- CLI `python -m devpilot_core api visual-smoke-report --json --write-report`.
- Verificación de seis superficies críticas: Dashboard, Report Viewer, Trace Viewer, Approval Center, Settings y Operator Dashboard embebido.
- Verificación de estados visuales: loading, empty, error, BLOCK, unauthorized/forbidden 401/403 y API local down.
- Script Node dependency-light `npm --prefix ui/web run test:visual`.
- Scaffold opcional de Playwright: `ui/web/playwright.config.ts` y `ui/web/tests/visual-smoke.spec.ts`.
- Higiene de screenshots: `outputs/ui-smoke/`, `ui/web/test-results/` y `ui/web/playwright-report/` permanecen no versionables.
- Corrección heredada: `local-api-security-hardening` queda efectivamente agregado a `quality-gate` hardening/industrial junto con `ui-visual-smoke`.

## Límites explícitos

- No se instala Playwright ni se agrega `@playwright/test` como dependencia obligatoria.
- El core pytest no depende de Node, navegador ni screenshots.
- El modo browser queda como scaffold opcional/advisory para evolución posterior.
- No hay pixel-perfect assertions ni cobertura cross-browser industrial.
- No se habilita red externa, SaaS, remote execution, connector write ni plugin execution.

## Comandos de verificación

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_028_visual_smoke_contract.py `
  tests/test_web_ui_mvp.py `
  tests/test_web_ui_report_trace_viewer.py `
  tests/test_web_ui_approval_center.py `
  tests/test_web_ui_settings.py `
  tests/test_post_h_015_operator_dashboard_ui.py `
  -q

python -m devpilot_core api visual-smoke-report --json --write-report
python -m devpilot_core schema validate --schema-id UiVisualSmokeReport --instance outputs/reports/ui_visual_smoke_report.json --json
npm --prefix ui/web test
npm --prefix ui/web run test:visual
```

## PASS/BLOCK

PASS requiere que las seis superficies críticas tengan marcadores visuales, estados visuales mínimos visibles, screenshot hygiene no versionable, UI API-only y browser tooling no requerido para core pytest.

BLOCK si la UI queda en blanco, falta una vista crítica, faltan estados 401/403/BLOCK/API-down/empty, se versionan screenshots, la UI lee filesystem/importa core Python o referencia rutas API no contractadas.
