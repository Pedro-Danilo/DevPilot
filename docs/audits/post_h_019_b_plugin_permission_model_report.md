---
doc_id: "POST-H-019-B-PLUGIN-PERMISSION-MODEL-REPORT"
id: "POST-H-019-B"
title: "POST-H-019-B — Permission model y manifest hardening report"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-019-B — Permission model y manifest hardening report

## Resultado

Estado: `implemented-initial`.

POST-H-019-B agrega un modelo explícito de permisos para plugins metadata-only y lo enlaza al `PluginRegistry`. La validación de manifests deja de comprobar solo estructura/policy bindings y ahora bloquea permisos no reconocidos, permisos denegados solicitados por manifests y capacidades críticas que requieren ADR futura.

## Artefactos principales

```text
docs/schemas/plugin_permission_model.schema.json
.devpilot/plugins/plugin_permission_model.json
src/devpilot_core/plugins/permission_model.py
tests/test_post_h_019_plugin_permission_model.py
```

## Invariantes implementadas

```text
plugin.code.execute effect=deny
plugin.code.execute risk_level=critical
plugin.code.execute requires_approval=true
plugin.code.execute blocked_until=future-adr
dynamic_import_allowed=false
subprocess_allowed=false
network_allowed=false
external_api_allowed=false
filesystem_write_allowed=false
shell_allowed=false
remote_execution_allowed=false
pip_install_allowed=false
marketplace_enabled=false
unknown_permissions_effect=deny
```

## PASS/BLOCK

PASS si `plugin validate` pasa con `permission_model_valid=true` y `blocked_findings_total=0`, y si el schema `PluginPermissionModel` valida `.devpilot/plugins/plugin_permission_model.json`.

BLOCK si un manifest declara un permiso desconocido, solicita `plugin.code.execute`, activa `dynamic_import_allowed`, `subprocess_allowed`, `network_allowed`, `filesystem_write_allowed`, `pip_install_allowed` o interpreta un manifest como permiso de ejecución.

## Límites

Este micro-sprint no implementa install dry-run, exposure report, quality gate ni ejecución real. Cualquier ejecución de plugins sigue siendo NO-GO hasta una ADR futura con sandbox técnico, Approval/RBAC, tests, observabilidad y rollback.
