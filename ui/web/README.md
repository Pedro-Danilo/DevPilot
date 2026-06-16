---

title: "DevPilot Local Web UI Sprint 71 MVP"
doc_id: "DEVPL-UI-WEB-README-FUNC-SPRINT-71"
status: "approved"
approval: "approved_by_implementation_validation"
version: "0.3.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
phase: "FASE-F-PRODUCTO-VISUAL"
sprint: "FUNC-SPRINT-71"
updated: "2026-06-16"
---

# DevPilot Local Web UI — Sprint 71 MVP

## Propósito

Documentar la ejecución local de la Web UI MVP de DevPilot, su contrato API-only, los límites de seguridad, los viewers operacionales y las acciones dry-run permitidas desde navegador local.

## Estado

`implemented-initial` para `FUNC-SPRINT-71 — Approval Center y acciones dry-run desde UI`.

Esta Web UI local es una primera versión visual industrializable. Consume exclusivamente la API local `/api/v1`, no importa Python/core, no lee `outputs/`, no toca `.devpilot/` directamente y mantiene bloqueadas las acciones críticas/destructivas. Sprint 71 permite únicamente acciones seguras en modo dry-run mediante allowlist.

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

El smoke test es deliberadamente dependency-light y no requiere instalar paquetes. Valida que la UI conserve el contrato API-only, no importe módulos Python/core, mantenga Report/Trace Viewer y exponga Approval Center/Action Launcher sin habilitar acciones críticas.

## Capacidades visuales actuales

- Dashboard workspace/readiness/standards/MIASI.
- Report Viewer y Trace Viewer sobre API local, sin lectura directa del filesystem desde UI.
- Métricas AgentOps resumidas.
- Approval Center para listar, crear y decidir solicitudes de aprobación locales.
- Action Launcher limitado a `readiness`, `code-review` y `refactor-plan` en modo dry-run.

## Límites

- No implementa login/RBAC multiusuario.
- No persiste token fuera de `sessionStorage` del navegador.
- No habilita `patch apply`, `refactor execute`, `rollback execute`, `git push` ni `deploy` desde UI.
- Approval Center es una primera versión local; la correlación avanzada approval↔trace↔report debe evolucionar en sprints posteriores.
