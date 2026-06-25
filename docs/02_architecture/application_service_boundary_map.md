# ApplicationService boundary map — POST-H-007-A

Estado: `implemented-initial`.

## Modelo mental

```text
[CLI]        \n  |          \n[API local]  --> [ApplicationService facade] --> [Domain application services] --> [Core domains]
  |          \n[Web UI]     /
```

## Boundary actual

- API local: mayoritariamente bound a `ApplicationService` mediante `dispatch_application_request`.
- Web UI: consume rutas `/api/v1/*` y no debe acoplarse al filesystem ni a motores core.
- CLI: conserva compatibilidad histórica; muchos comandos siguen en `cli.py` sin mapping explícito a operaciones de aplicación.

## POST-H-007-A

Se agrega un reporte estático:

```text
ApplicationServiceBoundaryReportBuilder
outputs/reports/application_service_boundary_report.json
outputs/reports/application_service_boundary_report.md
```

El mapa no activa runtime routing nuevo, no cambia rutas API, no cambia comandos CLI existentes y no habilita remote execution.

## Interfaces cubiertas

El mapa cubre `CLI/API/UI` como superficies de entrada al boundary.


## POST-H-007-B — ApplicationOperationCatalog

`POST-H-007-B` agrega un catálogo declarativo validable (`ApplicationOperationCatalog`) para describir operaciones de aplicación con contratos `ApplicationRequest`/`ApplicationResponse`, mappings CLI/API/UI explícitos, riesgo, writes, `policy_required`, `dry_run_default` y cobertura de pruebas. Esta versión es `implemented-initial`: no cambia rutas runtime, no ejecuta operaciones y no impone enforcement por interfaz.

Artefactos:

```text
src/devpilot_core/application/operation_catalog.py
src/devpilot_core/application/capability_registry.py
docs/schemas/application_operation_catalog.schema.json
outputs/reports/application_operation_catalog.json  # generado, no versionar
```
