# POST-H-007-B — Operation catalog y schema

Estado: `implemented-initial`

## Veredicto

`POST-H-007-B` implementa el catálogo declarativo de operaciones de aplicación exigido por el backlog `POST-H-007_application_service_boundary.md`. El catálogo se genera localmente, en modo read-only, desde la evidencia de `POST-H-007-A` y valida contra `ApplicationOperationCatalog`.

## Métricas

```text
operations_total = 35
domains_total = 18
required_initial_domains_covered_total = 10/10
cli_bound_total = 17
api_bound_total = 27
ui_bound_total = 12
policy_required_total = 7
writes_files_total = 4
high_or_critical_total = 7
operations_with_test_contracts_total = 35
operations_without_test_contracts_total = 0
direct_core_bypass_total = 105
```

## Artefactos

```text
src/devpilot_core/application/operation_catalog.py
src/devpilot_core/application/capability_registry.py
docs/schemas/application_operation_catalog.schema.json
docs/schemas/schema_catalog.json
tests/test_application_operation_catalog_schema.py
docs/post_h_007_b_manifest.json
```

## Seguridad

```text
read_only = true
dry_run = true
network_used = false
external_api_used = false
mutations_performed = false
source_mutations_performed = false
remote_execution_enabled = false
connector_write_enabled = false
plugin_execution_enabled = false
runtime_routes_added = false
runtime_behavior_changed = false
```

## Limitaciones

- No corrige bypasses CLI heredados.
- No normaliza aún operaciones prioritarias vía `ApplicationRequest`/`ApplicationResponse`; eso corresponde a `POST-H-007-C`.
- No aplica políticas por cliente de interfaz; eso corresponde a `POST-H-007-D`.
- No vincula aún `CommandDescriptor` con `ApplicationOperationDescriptor`; eso corresponde a `POST-H-007-E`.
