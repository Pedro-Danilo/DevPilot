# POST-H-007-C — DTO normalization report

Estado: `implemented-initial`.

## Propósito

Normalizar operaciones prioritarias para que puedan ejecutarse mediante `ApplicationRequest` y retornar `ApplicationResponse`, manteniendo `CommandResult` como contrato core y preservando hallazgos, códigos de salida y metadata.

## Operaciones cubiertas

```text
workspace.status
validation.docs
validation.contracts
reports.list
reports.read
approvals.list
settings.status
repo.inventory
review.code
refactor.plan
observability.traces
```

## Implementación

```text
src/devpilot_core/application/dto_normalization.py
src/devpilot_core/application/services.py
src/devpilot_core/application/__init__.py
tests/test_application_dto_normalization.py
```

## Evidencia técnica

- `validation.docs` y `validation.contracts` son aliases DTO explícitos sobre `ValidationGateway`.
- `settings.status` agrega de forma read-only `settings.workspace`, `settings.providers` y `settings.policy`.
- `observability.traces` ofrece una operación prioritaria estable hacia `trace_report`.
- `ApplicationResponse.from_command_result` preserva `exit_code`, `data`, `findings`, `report_paths` y metadata crítica.

## Seguridad

```text
read_only = true
dry_run = true
network_used = false
external_api_used = false
remote_execution_enabled = false
connector_write_enabled = false
plugin_execution_enabled = false
public_cli_commands_added = false
runtime_routes_added = false
```

## Limitaciones

`POST-H-007-C` no implementa policy enforcement por interfaz ni corrige todos los bypasses CLI. Es una primera normalización de operaciones prioritarias para preparar `POST-H-007-D/E`.
