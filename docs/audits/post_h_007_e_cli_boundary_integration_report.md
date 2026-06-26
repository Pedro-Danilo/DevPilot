# POST-H-007-E — CLI registry y ApplicationService quality gate integration

Estado: `implemented-initial`.

## Propósito

`POST-H-007-E` conecta el trabajo de `POST-H-006` con el endurecimiento de `POST-H-007` mediante una verificación local/read-only que relaciona `CommandDescriptor` con `ApplicationOperationDescriptor` y agrega una señal explícita al perfil `quality-gate hardening`.

La implementación es una primera versión industrial: produce evidencia, agrega warnings no bloqueantes para comandos que todavía requieren mapeo de operación, valida que las operaciones expuestas a API/UI tengan contrato explícito y no habilita routing dinámico del CLI.

## Artefactos implementados

```text
src/devpilot_core/application/cli_integration.py
src/devpilot_core/cli_registry/registry.py
src/devpilot_core/quality/gate.py
tests/test_application_cli_boundary_integration.py
docs/audits/post_h_007_e_cli_boundary_integration_report.md
docs/post_h_007_e_manifest.json
```

## Métricas iniciales

```text
commands_total = 130
registered_commands_total = 23
registered_commands_with_operation_mapping_total = 3
registered_commands_missing_operation_mapping_total = 20
applicable_commands_total = 26
applicable_commands_without_mapping_total = 8
catalog_cli_mappings_total = 17
catalog_operations_total = 39
api_ui_operations_total = 27
api_ui_operations_with_contract_total = 27
api_ui_operations_without_contract_total = 0
stale_metadata_total = 0
warnings_total = 8
blocking_findings_total = 0
quality_gate_hardening_bound = true
```

## Guardrails

```text
- No dynamic handler loading.
- No runtime registry routing.
- No public CLI command new.
- No public HTTP route new.
- No remote execution.
- No connector write.
- No plugin execution.
- No network call.
- No external API call.
```

## Warnings no bloqueantes

La integración reporta warnings para comandos registrados o grupos que requieren `ApplicationService` pero todavía no tienen `operation_id` explícito. Estos warnings son deliberadamente no bloqueantes en esta primera versión para no romper el CLI histórico. El bloqueo queda reservado para:

```text
- operaciones API/UI sin test_contract_ids;
- metadata CLI que apunte a operation_id inexistente;
- futura promoción explícita de warnings a enforcement en un sprint posterior.
```

## Estado industrial

Esta versión complementa la frontera de aplicación sin cerrar toda la deuda histórica del CLI. Deja una base verificable para promover progresivamente comandos legacy a operaciones de aplicación o justificar excepciones explícitas.
