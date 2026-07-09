---
doc_id: "POST-H-028-E-UI-ROUTE-ENFORCEMENT-REPORT"
title: "POST-H-028-E — UI route registry enforcement report"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
created: "2026-07-09"
updated: "2026-07-09"
approval: "approved"
sprint: "POST-H-028-E"
---

# POST-H-028-E — UI route registry enforcement report

## Decision

`PASS` — POST-H-028-E queda implementado como version `implemented-initial/local-first`.

## Alcance implementado

- `UiRouteEnforcementReport` schema-backed.
- `UiRouteEnforcementRunner` y CLI `python -m devpilot_core api ui-route-enforcement --json --write-report`.
- Enforcement bloqueante de `UiRouteContractRegistry` contra `ApiRouteContractRegistry`.
- Validacion de vistas criticas: Dashboard, Reports, Traces, Approval Center, Settings y Operator Dashboard embebido.
- Validacion de estados requeridos: loading, empty, error y BLOCK.
- Validacion de allowlist de acciones UI: no `patch/apply`, no rollback execute, no refactor execute, no tests/run, no git push, no deploy.
- Validacion de frontera UI/API-only: la UI no importa core Python, no lee `.devpilot/` ni `outputs/`, no usa `child_process` ni filesystem desde navegador.
- Subgates `ui-route-enforcement` y `ui-api-local-hardening` integrados a perfiles hardening/industrial.
- Script dependency-light `npm --prefix ui/web run test:route-enforcement`.

## Patch correctivo heredado

El log especifico de POST-H-028-D mostro un fallo Windows en `npm --prefix ui/web run test:operator-flows` por manejo de rutas con `new URL(...).pathname`, generando rutas `D:\D:\...`. POST-H-028-E corrige el script con `fileURLToPath(import.meta.url)`.

## Ajuste de registry

`ReportTraceView` es un componente compartido entre `ui.reports` y `ui.traces`. El enforcement estricto detecto que cada contrato declaraba solo su mitad del API. Se actualizo `.devpilot/interfaces/ui_route_contract_registry.json` para permitir explicitamente la llamada compartida:

- `ui.reports` permite `api.traces.list`.
- `ui.traces` permite `api.reports.list`.

Esto evita falsos negativos y hace explicita la frontera de API usada por el componente compartido.

## No-go gates

No se habilita:

- remote execution;
- connector write;
- plugin execution;
- API externa;
- host remoto;
- CORS wildcard;
- lectura directa de filesystem desde UI;
- escritura o ejecucion de acciones sensibles desde navegador.

## Estado y limitaciones

La capacidad queda `implemented-initial`. No sustituye una suite browser E2E industrial, cross-browser ni pruebas visuales pixel-perfect. Esa evolucion debe abordarse despues de POST-H-029 cuando existan tiers de testing/costo de regresion mas formales.
