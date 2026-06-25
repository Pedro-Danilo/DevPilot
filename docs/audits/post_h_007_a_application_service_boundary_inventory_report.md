# POST-H-007-A — Inventario de operaciones y bypasses

Estado: `implemented-initial`.

## Objetivo

Identificar de forma reproducible qué operaciones pasan por `ApplicationService` y qué superficies siguen acopladas directamente a `cli.py` o motores de dominio.

## Implementación

```text
src/devpilot_core/application/boundary.py
src/devpilot_core/application/report.py
```

El builder usa análisis estático de:

```text
src/devpilot_core/application/services.py
src/devpilot_core/application/*_service.py
src/devpilot_core/interfaces/api/routers/*.py
src/devpilot_core/cli.py
ui/**
CLI registry POST-H-006-E
```

## Seguridad

```text
read_only=true
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
runtime_behavior_changed=false
```

## Resultado esperado

El reporte debe mostrar `direct_core_bypass_total > 0`, porque `POST-H-007-A` inventaría bypasses históricos y no los corrige todavía.

## Evolución

La siguiente etapa debe convertir filas prioritarias en un `ApplicationOperationCatalog` validable por schema y luego normalizar DTOs de operaciones prioritarias.
