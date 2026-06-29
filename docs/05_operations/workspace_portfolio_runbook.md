---
doc_id: "POST-H-016-WORKSPACE-PORTFOLIO-RUNBOOK"
title: "Workspace Portfolio Hardening Runbook"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-29"
phase: "POST-FASE-H"
---

# Workspace Portfolio Hardening Runbook

## Estado

Runbook `implemented-initial` para POST-H-016-A/B. Cubre validación de Workspace Registry v1, migración read-only v2 y workspace isolation check. El hardening de portfolio status, integración API y subgate final se documentarán en POST-H-016-C/D/E.

## Validar registry v1 vigente

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core workspace registry-validate --json
```

PASS si:

```text
- schema_valid=true
- deny_unregistered_workspaces=true
- cross_workspace_state_reads=false
- secret_sharing_allowed=false
- mutations_performed=false
```

## Validar registry v2 migrado

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core workspace registry-validate --registry-version v2 --json
```

PASS si:

```text
- v1_registry_valid=true
- v2_schema_valid=true
- migration_mode=read-only
- cross_workspace_writes=false
- secret_sharing_allowed=false
- connector_write_used=false
- plugin_execution_used=false
- mutations_performed=false
```

## Límites operacionales

POST-H-016-A no escribe `.devpilot/workspaces/workspace_registry.json` durante la migración v2. La v2 es una vista en memoria para endurecer contratos sin romper compatibilidad con los comandos históricos `workspace list/register/select/registry-validate`.

## Validar aislamiento de workspaces

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core workspace isolation-check --json --write-report
python -m devpilot_core schema validate --schema-id WorkspaceIsolationReport --instance outputs/reports/workspace_isolation_report.json --json
```

PASS si:

```text
- registered_workspaces_only=true
- path_guard_aligned=true
- state_paths_inside_workspace=true
- outputs_inside_workspace=true
- traces_inside_workspace=true
- secrets_read=false
- state_files_read=false
- source_mutations_performed=false
```

El reporte `outputs/reports/workspace_isolation_report.json` es evidencia runtime regenerable y no debe incluirse en ZIPs limpios.

BLOCK si:

```text
- secret_sharing_allowed=true
- cross_workspace_writes=true
- remote_execution_used=true
- connector_write_used=true
- plugin_execution_used=true
- active_workspace_id no referencia un workspace registrado
```
