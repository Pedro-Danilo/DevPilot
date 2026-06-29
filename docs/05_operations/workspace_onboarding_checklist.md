---
doc_id: "POST-H-016-WORKSPACE-ONBOARDING-CHECKLIST"
title: "Workspace onboarding checklist"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-29"
phase: "POST-H-016-E"
---

# Workspace onboarding checklist

Estado: `implemented-initial`.

Este checklist operacional cubre el onboarding local de un workspace DevPilot registrado. No habilita workspaces remotos, multiusuario enterprise, sincronización cloud, cross-workspace writes ni ejecución remota.

## 1. Preparar workspace

```powershell
$env:PYTHONPATH="src"
python -m devpilot_core workspace status --json
```

PASS si el workspace contiene `.devpilot/project.yaml` y `docs/`.

## 2. Registrar workspace

```powershell
python -m devpilot_core workspace register `
  --path . `
  --workspace-id devpilot-local `
  --name "DevPilot Local" `
  --json
```

PASS si el workspace aparece en `.devpilot/workspaces/workspace_registry.json` y no se registran rutas fuera del workspace root.

## 3. Validar registry

```powershell
python -m devpilot_core workspace registry-validate --json
python -m devpilot_core workspace registry-validate --registry-version v2 --json
```

PASS si `deny_unregistered_workspaces=true`, `cross_workspace_writes=false`, `secret_sharing_allowed=false` y `portfolio_status_read_only=true`.

## 4. Validar aislamiento

```powershell
python -m devpilot_core workspace isolation-check --json --write-report
```

PASS si `path_guard_aligned=true`, `state_paths_inside_workspace=true`, `outputs_inside_workspace=true`, `traces_inside_workspace=true`, `secrets_read=false` y `state_files_read=false`.

## 5. Validar portfolio

```powershell
python -m devpilot_core portfolio status --json
python -m devpilot_core portfolio hardening-gate --json --write-report
```

PASS si `registered_workspaces_only=true`, `unregistered_workspace_policy=denied`, `portfolio_status_read_only=true` y `cross_workspace_writes=false`.

## 6. Criterios BLOCK

```text
BLOCK si active_workspace_id no referencia un workspace registrado.
BLOCK si state_path, outputs/reports o traces quedan fuera del workspace root.
BLOCK si secret_sharing_allowed=true.
BLOCK si cross_workspace_writes=true.
BLOCK si la API de portfolio cambia active_workspace_id.
BLOCK si workspace-portfolio-hardening no está integrado en quality-gate hardening/industrial.
```

## 7. Límites

Esta versión es `implemented-initial`. La operación es local-first y read-only por defecto. No declara madurez multi-tenant, SaaS, enterprise auth, remote runner, connector write ni plugin execution.
