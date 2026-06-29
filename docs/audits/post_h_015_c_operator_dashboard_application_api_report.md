# POST-H-015-C — Operator Dashboard Application/API Report

## Estado

`implemented-initial`

## Objetivo

Exponer el snapshot del dashboard local de operador por el boundary `ApplicationService` y por la API local protegida, sin permitir que la API o una UI futura importen directamente el aggregator de portfolio.

## Artefactos

```text
src/devpilot_core/application/operator_dashboard_service.py
src/devpilot_core/interfaces/api/routers/operator.py
tests/test_post_h_015_operator_dashboard_application_api.py
docs/post_h_015_c_manifest.json
docs/audits/post_h_015_c_operator_dashboard_application_api_report.md
```

## Capacidad implementada

```text
ApplicationService operation: operator.dashboard
API route: GET /api/v1/operator/dashboard
Response contract: ApplicationResponse
Route registry id: api.operator.dashboard
```

El router usa `dispatch_application_request()` y no llama directamente a `OperatorDashboardAggregator`. `OperatorDashboardApplicationService` encapsula el aggregator y mantiene `write_report=false` como valor por defecto.

## Seguridad

```text
local_first=true
read_only=true
dry_run=true
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

La ruta queda protegida por token local, CORS local-only y `PolicyEngine` mediante `ApiRoutePolicy("operator.dashboard", "read", "protected-operator-dashboard")`.

## Correccion heredada aplicada

`TestContractRegistryV2` no acepta `operator.dashboard` como `domain`. Los contratos POST-H-015-A y POST-H-015-B se corrigen a `product.ui`, y POST-H-015-C agrega un contrato `application.service` para la nueva exposición ApplicationService/API.

## Limitaciones

POST-H-015-C no implementa la UI visual del dashboard ni el subgate final `operator-dashboard-ready`. Esos alcances permanecen planificados para POST-H-015-D/E.
