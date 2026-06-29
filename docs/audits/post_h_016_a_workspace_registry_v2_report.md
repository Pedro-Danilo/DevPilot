# POST-H-016-A — Workspace Registry v2 y migración compatible

Estado: `implemented-initial`.

## Alcance

POST-H-016-A agrega un contrato `MultiworkspaceRegistryV2` para endurecer la semántica del portfolio local sin reemplazar el registry v1 vigente. La migración v1 -> v2 se ejecuta en memoria, valida contra `docs/schemas/multiworkspace_registry_v2.schema.json` y conserva `.devpilot/workspaces/workspace_registry.json` como fuente compatible.

## Controles implementados

```text
- deny_unregistered_workspaces=true
- cross_workspace_state_reads=false
- cross_workspace_writes=false
- secret_sharing_allowed=false
- portfolio_status_read_only=true
- network_used=false
- external_api_used=false
- remote_execution_used=false
- connector_write_used=false
- plugin_execution_used=false
- mutations_performed=false
- source_mutations_performed=false
- secrets_read=false
```

## Comando

```powershell
python -m devpilot_core workspace registry-validate --registry-version v2 --json
```

## Riesgos y límites

La implementación no incluye todavía isolation report, hardening de `portfolio status`, integración API ni subgate `workspace-portfolio-hardening`. Es una base contractual para POST-H-016-B/C/D/E.
