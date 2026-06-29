# POST-H-016-C — Portfolio status hardening

## Estado

`implemented-initial`.

POST-H-016-C endurece `portfolio status` para consolidar el portfolio local únicamente desde `Workspace Registry v2` y `WorkspaceIsolationValidator`.

## Cambios técnicos

- `PortfolioStatusBuilder` deja de depender directamente del registry v1 para la consolidación operacional.
- La consolidación se bloquea si falla `MultiworkspaceRegistryV2` o `WorkspaceIsolationValidator`.
- La salida reporta solo workspaces registrados y declara `unregistered_workspace_policy=denied`.
- Cada workspace incluye resumen de `readiness`, `state`, `reports`, `traces`, `risks`, `isolation` y `no_go`.
- Las fuentes operacionales ausentes se reportan como `unknown`.
- Se preservan campos históricos de compatibilidad: `portfolio_status_read_only`, `state_files_read`, `secrets_read`, `mutations_performed`.

## No-go gates

```text
read_only=true
state_files_read=false
secrets_read=false
network_used=false
external_api_used=false
remote_execution_used=false
connector_write_used=false
plugin_execution_used=false
source_mutations_performed=false
cross_workspace_writes=false
```

## Pruebas focales

```powershell
python -m pytest -p no:ddtrace tests/test_post_h_016_portfolio_status_hardening.py tests/test_post_h_016_workspace_isolation.py tests/test_post_h_016_workspace_registry_v2.py tests/test_multiworkspace.py tests/test_project_global_state.py -q
python -m devpilot_core portfolio status --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
```

## Límites

POST-H-016-C no implementa API dedicada, UI específica ni quality gate final. Es una capa de hardening semántico sobre el comando/local builder existente. POST-H-016-D/E deben completar integración segura y gate operacional.
