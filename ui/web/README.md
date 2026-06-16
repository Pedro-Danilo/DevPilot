---
title: "DevPilot Local Web UI Sprint 69 MVP"
doc_id: "DEVPL-UI-WEB-README-FUNC-SPRINT-69"
status: "approved"
approval: "approved_by_implementation_validation"
version: "0.1.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-69"
updated: "2026-06-15"
---

# DevPilot Local Web UI — Sprint 69 MVP

## Propósito

Documentar la ejecución local de la Web UI MVP de DevPilot, su contrato API-only, los límites read-only y los comandos mínimos de verificación.

## Estado

`implemented-initial` para `FUNC-SPRINT-69 — Web UI MVP: dashboard workspace/readiness/MIASI`.

Esta Web UI local es una primera versión visual. Consume exclusivamente la API local `/api/v1`, no importa Python/core, no lee `outputs/`, no toca `.devpilot/` y no ejecuta acciones destructivas.

## Requisitos

- Node.js 20 o superior para ejecutar la Web UI, `npm run dev`, `npm run build` o `npm test`.
- La suite Python de DevPilot valida el contrato smoke de la UI aunque Node/npm no estén instalados o `npm` no sea invocable desde `PATH`, para que `pytest -q` siga siendo un gate reproducible del core. La ejecución de `npm test` desde pytest es opt-in mediante `DEVPILOT_RUN_WEB_UI_NPM_TEST=1`.
- API local DevPilot ejecutándose en `http://127.0.0.1:8787`.
- Token local generado con `python -m devpilot_core api token --json`.

## Ejecución

Terminal 1:

```powershell
$env:DEVPILOT_API_TOKEN = "<token>"
python -m devpilot_core api serve --host 127.0.0.1 --port 8787 --execute
```

Terminal 2:

```powershell
cd ui/web
npm install
npm run dev
```

Abrir:

```text
http://127.0.0.1:5173
```

## Pruebas

```powershell
cd ui/web
npm test
```

El smoke test es deliberadamente dependency-light y no requiere instalar paquetes. Valida que la UI conserve el contrato API-only/read-only y que no importe módulos Python/core.

## Límites

- No implementa login/RBAC.
- No persiste token fuera de `sessionStorage` del navegador.
- No implementa Report Viewer ni Trace Viewer; quedan para Sprint 70.
- No ejecuta acciones write/execute.
