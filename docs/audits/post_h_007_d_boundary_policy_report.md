# POST-H-007-D — Boundary policy y guardrails por interfaz

Estado: `implemented-initial`  
Fecha: 2026-06-25  
Fuente base: `repo_DevPilot_Local_168_POST_H_007_C.zip`  
Fuente actual esperada: `repo_DevPilot_Local_169_POST_H_007_D.zip`

## Veredicto

`POST-H-007-D` implementa una primera capa de boundary policy dentro de `ApplicationService.execute()` para gobernar qué clientes pueden invocar qué operaciones mediante `ApplicationRequest`.

La implementación es local-first, determinística y no habilita remote execution, connector write, plugin execution ni APIs externas.

## Artefactos principales

- `src/devpilot_core/application/policy.py`: reglas de interfaz, `InterfaceClient`, `ApplicationBoundaryPolicy` y reporte estático.
- `src/devpilot_core/application/services.py`: evaluación de boundary policy antes del dispatch de operación.
- `tests/test_application_boundary_policy.py`: pruebas focales para clientes, bloqueo API/UI, dry-run y policy check.

## Métricas

```json
{
  "rules_total": 39,
  "clients_total": 5,
  "sensitive_operations_total": 7,
  "sensitive_without_policy_required_total": 0,
  "api_allowed_total": 27,
  "ui_allowed_total": 12,
  "automation_allowed_total": 32,
  "publicly_unexposed_operations_total": 12,
  "dry_run_default": true,
  "remote_execution_enabled": false,
  "connector_write_enabled": false,
  "plugin_execution_enabled": false,
  "network_used": false,
  "external_api_used": false,
  "mutations_performed": false,
  "source_mutations_performed": false,
  "preliminary": true
}
```

## Reglas aplicadas

- Clientes formales: `cli`, `api`, `ui`, `automation`, `internal`.
- `api` y `ui` son estrictos: solo pueden ejecutar operaciones con exposición explícita en `ApplicationOperationCatalog`.
- `automation` solo recibe operaciones no write-like, no sensibles y de riesgo bajo/medio.
- `cli` e `internal` se mantienen compatibles para operación local y pruebas históricas.
- Clientes locales/desconocidos se normalizan a `internal` por compatibilidad, pero no se consideran clientes públicos.
- Operaciones sensibles invocan `PolicyEngine` antes del handler de dominio.
- Operaciones sensibles llamadas desde `api`, `ui` o `automation` requieren `dry_run=true`.

## Seguridad

```text
remote_execution_enabled: false
connector_write_enabled: false
plugin_execution_enabled: false
network_used: false
external_api_used: false
mutations_performed: false
source_mutations_performed: false
```

## Limitaciones

Esta es una primera versión de guardrails por interfaz. No migra todos los comandos CLI a `ApplicationService`, no crea rutas HTTP nuevas, no cambia la UI y no conecta todavía `CommandDescriptor` con `ApplicationOperationDescriptor`. Esa integración queda para `POST-H-007-E`.
