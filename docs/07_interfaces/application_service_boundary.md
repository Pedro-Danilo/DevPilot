# POST-H-007 — ApplicationService boundary

Estado: `implemented-initial` acumulativo hasta `POST-H-007-D`.

## Propósito

Este documento define la frontera objetivo entre interfaces públicas de DevPilot y el core:

```text
CLI/API/UI
  -> ApplicationService
  -> domain application services
  -> core/domain engines
```

`POST-H-007-A` no modifica runtime. Genera un inventario read-only para saber qué ya pasa por la frontera y qué queda como bypass histórico.

## Resultado POST-H-007-A

El reporte generado calcula, entre otras métricas:

```text
operations_total
direct_core_bypass_total
api_routes_total
api_bound_total
cli_bound_total
cli_unbound_total
critical_bypass_total
```

## Reglas actuales

```text
- API local debe usar dispatch_application_request + ApplicationService.
- Web UI debe consumir API local; no debe leer outputs/ directamente.
- CLI histórico puede seguir usando CommandResult, pero los comandos nuevos deben mapearse a ApplicationService cuando aplique.
- Comandos sensibles deben declarar policy_required y no pueden habilitar writes remotos.
```

## Limitación explícita

El estado es preliminar/industrial-initial. `POST-H-007-A` identifica bypasses; no los corrige masivamente. La corrección incremental se divide en:

```text
POST-H-007-B — Operation catalog y schema
POST-H-007-C — Normalización DTO de operaciones prioritarias
POST-H-007-D — Boundary policy y guardrails por interfaz
POST-H-007-E — Integración con CLI registry y quality gate
```


## POST-H-007-B — ApplicationOperationCatalog

`POST-H-007-B` agrega un catálogo declarativo validable (`ApplicationOperationCatalog`) para describir operaciones de aplicación con contratos `ApplicationRequest`/`ApplicationResponse`, mappings CLI/API/UI explícitos, riesgo, writes, `policy_required`, `dry_run_default` y cobertura de pruebas. Esta versión es `implemented-initial`: no cambia rutas runtime, no ejecuta operaciones y no impone enforcement por interfaz.

Artefactos:

```text
src/devpilot_core/application/operation_catalog.py
src/devpilot_core/application/capability_registry.py
docs/schemas/application_operation_catalog.schema.json
outputs/reports/application_operation_catalog.json  # generado, no versionar
```


## POST-H-007-C — DTO normalization priority path

`POST-H-007-C` agrega normalización runtime para 11 operaciones prioritarias usando `ApplicationRequest`/`ApplicationResponse`. El adapter conserva `CommandResult` como contrato core y no cambia rutas públicas.

Nuevas operaciones/aliases DTO:

```text
validation.docs -> ValidationGateway(scope=docs)
validation.contracts -> ValidationGateway(scope=contracts)
settings.status -> agregado read-only workspace/providers/policy
observability.traces -> trace_report estable para API/UI
```

Garantías:

```text
- findings preservados
- exit_code preservado
- data/report_paths/metadata preservados
- sin remote execution
- sin connector write
- sin plugin execution
- sin nuevos comandos CLI públicos
```

Límite actualizado: la decisión de qué cliente puede ejecutar qué operación queda cubierta de forma inicial por `POST-H-007-D`; la integración con CLI registry y quality gate queda para `POST-H-007-E`.


## POST-H-007-D — Boundary policy por interfaz

`POST-H-007-D` agrega `ApplicationBoundaryPolicy` como guardrail previo al dispatch de `ApplicationService.execute()`.

Clientes reconocidos:

```text
cli
api
ui
automation
internal
```

Reglas iniciales:

```text
- api/ui son clientes estrictos y solo pueden invocar operaciones con mapping explícito.
- automation solo recibe operaciones no sensibles, no write-like y de riesgo bajo/medio.
- operaciones sensibles invocan PolicyEngine antes del handler.
- operaciones sensibles llamadas desde api/ui/automation requieren dry_run=true.
- unknown/local testing clients se normalizan a internal para compatibilidad, no a clientes públicos.
```

Esta versión no crea rutas HTTP nuevas, no cambia la UI y no migra comandos CLI históricos. Es un enforcement `implemented-initial` orientado a cerrar la brecha de autorización por interfaz antes de `POST-H-007-E`.
