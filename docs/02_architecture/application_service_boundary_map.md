# ApplicationService boundary map — POST-H-007-A/B/C/D/E

Estado: `implemented-initial` acumulativo hasta `POST-H-007-E`.

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


## POST-H-007-C — DTO runtime normalization

El mapa acumula una nueva ruta interna:

```text
ApplicationRequest(priority operation)
  -> ApplicationService.execute()
  -> priority DTO normalization/default payloads
  -> domain application service
  -> CommandResult
  -> ApplicationResponse
```

Esta ruta no reemplaza `CommandResult`; lo envuelve para API/UI/CLI-equivalent paths. Tampoco agrega rutas HTTP ni comandos CLI públicos.


## POST-H-007-D — Runtime boundary policy

El mapa incorpora una compuerta previa al dispatch:

```text
ApplicationRequest
  -> normalize_priority_application_request
  -> ApplicationBoundaryPolicy.evaluate
      -> InterfaceClient allowlist
      -> dry-run guardrail para operaciones sensibles
      -> PolicyEngine para operaciones sensibles
  -> domain operation handler
  -> CommandResult
  -> ApplicationResponse
```

Métricas iniciales:

```text
rules_total = 39
sensitive_operations_total = 7
api_allowed_total = 27
ui_allowed_total = 12
automation_allowed_total = 32
publicly_unexposed_operations_total = 12
```

La política no reemplaza `PolicyEngine`; lo invoca cuando corresponde. Tampoco corrige todos los bypasses CLI históricos. La conexión inicial con `CLI Command Registry` y quality gate queda cubierta por `POST-H-007-E`.


## POST-H-007-E — CLI registry and quality gate coupling

El mapa incorpora una ruta de gobernanza, no de routing runtime:

```text
CLI Command Registry
  -> CommandDescriptor.metadata.application_operation_id
  -> ApplicationOperationCatalog.operation_id
  -> CliApplicationBoundaryIntegrationReportBuilder
  -> QualityGate hardening subgate
```

Esta ruta permite detectar comandos registrados o grupos que requieren `ApplicationService` pero aún no tienen operación de aplicación explícita. Los gaps se reportan como warning no bloqueante salvo cuando una operación API/UI carece de contrato explícito o una metadata CLI apunta a una operación inexistente.

No se habilita `dynamic_handler_loading`, no se activa runtime registry routing, no se agregan rutas HTTP y no se agregan comandos públicos.
