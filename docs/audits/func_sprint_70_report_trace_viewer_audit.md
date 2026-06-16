---
title: "Auditoría FUNC-SPRINT-70 — Report Viewer y Trace Viewer"
doc_id: "DEVPL-AUDIT-FUNC-SPRINT-70"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
standard: "MIPSoftware"
extension: "MIASI"
sprint: "FUNC-SPRINT-70"
updated: "2026-06-16"
approval: "approved"
---

# Auditoría FUNC-SPRINT-70 — Report Viewer y Trace Viewer

## 0. Estado

Veredicto: `PASS` focalizado.

## 1. Propósito

Implementar una primera versión visual de Report Viewer y Trace Viewer para consultar reportes, findings, trazas y métricas desde la Web UI local sin que el frontend lea `outputs/`, `.devpilot/` ni módulos Python/core directamente.

## 2. Alcance implementado

- Endpoints API protegidos para listar/leer reportes.
- Endpoints API protegidos para listar/inspeccionar trazas y métricas.
- Vistas Web UI de Report Viewer y Trace Viewer.
- Filtro básico por severidad para reportes.
- Manejo explícito de estados vacíos para trazas/reportes.
- Redacción y límites en `ReportsApplicationService`.

## 3. Funcionamiento técnico

La ruta obligatoria es `ui/web → /api/v1 → ApplicationService → ReportsApplicationService/ObservabilityApplicationService → core`. UI no lee `outputs/` ni `.devpilot/`; la API lee de forma controlada y redacted. La UI no lee filesystem; la API limita el acceso a `outputs/reports` y `.devpilot/devpilot.db` mediante servicios de aplicación y policy binding.

## 4. Archivos creados

- `src/devpilot_core/application/reports_service.py`.
- `src/devpilot_core/interfaces/api/routers/reports.py`.
- `src/devpilot_core/interfaces/api/routers/traces.py`.
- `ui/web/src/pages/ReportTraceView.ts`.
- `ui/web/src/components/FindingTable.ts`.
- `tests/test_api_reports_traces.py`.
- `tests/test_web_ui_report_trace_viewer.py`.
- `docs/functional_sprint_70_manifest.json`.

## 5. Archivos modificados

Se actualizaron `ApplicationService`, API security policy, OpenAPI, contrato API, mapping API, README, runbook, backlog F, backlog funcional, C4, contrato interno y pruebas documentales acumulativas.

## 6. Criterios PASS

- Report Viewer no lee filesystem fuera de API.
- Trace Viewer maneja trazas vacías.
- Findings se filtran sin exponer secretos.
- API protege rutas con token y PolicyEngine.
- `pytest` focalizado y smoke UI pasan.

## 7. Criterios BLOCK

- UI accede directamente a `outputs/`.
- UI accede directamente a `.devpilot/`.
- Se revela un secreto en reporte/API/UI.
- Trazas grandes no tienen límites.
- Se habilita acción write/execute.

## 8. Riesgos y limitaciones

- CORS restringido en errores 401/403: Sprint 70 corrige el comportamiento observado en navegador donde un token incorrecto podía verse como `Failed to fetch`; la API ahora devuelve CORS solo para origins locales permitidos en respuestas tempranas de seguridad.

Primera versión visual: filtros simples, detalle JSON en `pre`, sin virtualización, sin paginación avanzada y sin búsqueda global. Debe evolucionar antes de considerarse un observability portal industrial completo.

## 9. Comandos de verificación

```powershell
python -m pytest tests/test_api_reports_traces.py tests/test_web_ui_report_trace_viewer.py tests/test_sprint_70_documentation.py -q
npm --prefix ui/web test
python -m devpilot_core validate all --json
```

## 10. Conclusión

Sprint 70 deja una primera capacidad visual de consulta de reportes y trazas, manteniendo reglas local-first, API-only, redacción, límites y separación UI/API/core.
