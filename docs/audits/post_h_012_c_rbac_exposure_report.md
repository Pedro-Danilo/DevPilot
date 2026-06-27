---
doc_id: "POST-H-012-C-RBAC-EXPOSURE-REPORT"
title: "POST-H-012-C — RBAC exposure report"
status: "approved"
owner: "Ordóñez"
updated: "2026-06-27"
phase: "POST-FASE-H"
source_backlog: "docs/backlogs/POST-H-012_approval_rbac_hardening.md"
---

# POST-H-012-C — RBAC exposure report

## Resultado

Estado: `implemented-initial`.

DevPilot incorpora un reporte local y determinístico de exposición Approval/RBAC que cruza tres fuentes: `.devpilot/identity/identity_registry.json`, `.devpilot/approval/sensitive_action_catalog.json` y `.devpilot/miasi/policy_matrix.json`.

## Controles implementados

```text
- Matriz actor/role/action/interface/effect.
- Detección de acciones críticas sin `requires_rbac_role`.
- Detección de roles requeridos no declarados en Identity Registry.
- Bloqueo de exposición API/UI para acciones críticas.
- Bloqueo de remote/plugin/connector write.
- Escritura opcional de `outputs/reports/approval_rbac_exposure.json` y `.md`.
```

## Seguridad

```text
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## Limitaciones

El reporte no concede permisos y no sustituye el enforcement de `PolicyEngine`. La integración homogénea queda para POST-H-012-D y el subgate final para POST-H-012-E.
