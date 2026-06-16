---
title: "Auditoría FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-69"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-69"
updated: "2026-06-15"
approval: "approved_by_implementation_validation"
---

# Auditoría FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI

## 0. Estado

Veredicto: `PASS`.

Estado: `implemented-initial`.

## 1. Propósito

Construir la primera Web UI local de DevPilot como dashboard MVP para workspace, readiness, standards y MIASI, consumiendo únicamente la API local segura `/api/v1`.

## 2. Alcance implementado

- Estructura `ui/web`.
- Cliente API local con token `X-DevPilot-Token`.
- Dashboard read-only con tarjetas PASS/WARN/BLOCK/PENDING.
- Smoke contract Python reproducible sin Node/npm obligatorio, más `npm test` solo bajo ejecución manual o variable explícita `DEVPILOT_RUN_WEB_UI_NPM_TEST=1`.
- Pruebas Python para contrato UI/API-only.
- Documentación de operación y límites.

## 3. Funcionamiento técnico

```text
Browser local
  → ui/web
  → http://127.0.0.1:8787/api/v1
  → API local segura Sprint 68
  → ApplicationService
```

La UI guarda el token únicamente en `sessionStorage` del navegador local y no lo incluye en código fuente ni reportes.

## 4. Archivos creados

- `ui/web/package.json`
- `ui/web/index.html`
- `ui/web/vite.config.ts`
- `ui/web/src/main.ts`
- `ui/web/src/api/client.ts`
- `ui/web/src/api/types.ts`
- `ui/web/src/pages/Dashboard.ts`
- `ui/web/src/components/StatusCard.ts`
- `ui/web/src/components/FindingList.ts`
- `ui/web/src/styles.css`
- `ui/web/scripts/smoke-test.mjs`
- `ui/web/README.md`
- `tests/test_web_ui_mvp.py`
- `tests/test_sprint_69_documentation.py`
- `docs/functional_sprint_69_manifest.json`

## 5. Archivos modificados

- `README.md`
- `pyproject.toml`
- `docs/05_operations/runbook.md`
- `docs/devpilot_backlog_fase_F_producto_visual.md`
- `docs/functional_backlog_after_precode.md`
- `docs/02_architecture/c4_container.md`
- `docs/07_interfaces/internal_application_contract.md`
- `docs/07_interfaces/api_contract_v1.md`
- `docs/07_interfaces/api_service_mapping.md`
- `docs/07_interfaces/openapi_v1.json`
- `src/devpilot_core/application/services.py`
- tests documentales históricos para reflejar el hito vigente.

## 6. Criterios PASS

- El smoke contract Python de `tests/test_web_ui_mvp.py` pasa aunque Node/npm no estén instalados.
- `npm test` pasa cuando se ejecuta manualmente o cuando `DEVPILOT_RUN_WEB_UI_NPM_TEST=1` está activo en un entorno con Node.js/npm correctamente instalado.
- La UI consume `/api/v1`.
- La UI no importa Python/core.
- La UI no usa filesystem.
- La UI no invoca acciones destructivas.
- `python -m pytest tests/test_web_ui_mvp.py tests/test_sprint_69_documentation.py -q` pasa.

## 7. Criterios BLOCK

- Frontend importa `devpilot_core`.
- Frontend lee `outputs/`, `.devpilot/` o filesystem.
- Frontend requiere API externa.
- Frontend hardcodea token.
- Frontend invoca rutas write/execute.

## 8. Riesgos y limitaciones

- Requiere Node.js 20+ para desarrollo visual y ejecución manual de `npm test`.
- La suite Python no debe fallar por ausencia de Node/npm ni por wrappers `npm` no invocables en Windows; por defecto valida el mismo smoke contract desde Python.
- `npm test` es smoke test contractual, no prueba visual end-to-end.
- Token en `sessionStorage` es aceptable para MVP local, no para Web real multiusuario.
- Report Viewer y Trace Viewer no están implementados todavía.

## 9. Nota sobre dependencia `httpx2`

Sprint 69 ajusta `pyproject.toml` para que el extra `dev` use `httpx2>=2.4,<3`, alineado con Starlette 1.2+ TestClient. Este ajuste busca eliminar `StarletteDeprecationWarning` por uso de `httpx` plano en entornos actualizados.

## 10. Comandos de verificación

```powershell
python -m pytest tests/test_web_ui_mvp.py tests/test_sprint_69_documentation.py -q

# Opcional cuando Node.js/npm estén instalados
$env:DEVPILOT_RUN_WEB_UI_NPM_TEST = "1"
python -m pytest tests/test_web_ui_mvp.py -q
Remove-Item Env:DEVPILOT_RUN_WEB_UI_NPM_TEST

cd ui/web
npm test
cd ../..
python -m devpilot_core validate all --json
```

## 11. Conclusión

`FUNC-SPRINT-69` queda implementado como Web UI MVP local, API-only, read-only y preparado para extenderse con Report Viewer/Trace Viewer en Sprint 70.
