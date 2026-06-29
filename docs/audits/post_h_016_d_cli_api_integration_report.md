# POST-H-016-D — CLI/API integration segura

Estado: `implemented-initial`

## Alcance

POST-H-016-D integra el portfolio local endurecido con ApplicationService y la API local protegida sin abrir mutaciones de workspace desde API.

## Implementación

- `PortfolioApplicationService` expone `portfolio.status` como operación read-only.
- `ApplicationService` despacha `portfolio.status` y lo publica en capabilities/routes.
- `python -m devpilot_core portfolio status --json` invoca ApplicationService.
- `GET /api/v1/portfolio/status` devuelve `ApplicationResponse` por `dispatch_application_request`.
- `ApiRouteContractRegistry` registra `api.portfolio.status`.
- `API_ROUTE_POLICIES` protege la ruta con token y PolicyEngine.

## Seguridad

```text
local_first=true
read_only=true
dry_run=true
network_used=false
external_api_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
api_workspace_selection_enabled=false
cross_workspace_writes=false
```

## Corrección heredada

El ZIP 213 contenía `docs/POST-H-016_workspace_portfolio_hardening.md` truncado. En POST-H-016-D se reconstruyó desde `docs/backlogs/POST-H-016_workspace_portfolio_hardening.md` completo, preservando las secciones `POST-H-016-D`, `POST-H-016-E`, criterios BLOCK, riesgos y Definition of Done.

## Verificación prevista

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace tests/test_post_h_016_cli_api_integration.py tests/test_post_h_016_portfolio_status_hardening.py tests/test_post_h_016_workspace_isolation.py tests/test_post_h_014_api_route_contracts.py tests/test_post_h_015_operator_dashboard_application_api.py -q
python -m devpilot_core portfolio status --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
```

## Límites

Esta entrega no implementa UI específica de portfolio ni el subgate final `workspace-portfolio-hardening`. Ese cierre corresponde a `POST-H-016-E`.
