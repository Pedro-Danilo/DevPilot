---
doc_id: "POST-H-012-A-SENSITIVE-ACTION-CATALOG-REPORT"
title: "POST-H-012-A — Sensitive action catalog y schema"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-012-A"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-012-A — Sensitive action catalog y schema

## Resultado

`POST-H-012-A` implementa la primera pieza machine-readable del hardening Approval/RBAC: un catálogo local de acciones sensibles y un validador determinístico que cruza el catálogo con MIASI.

## Artefactos implementados

```text
docs/schemas/sensitive_action_catalog.schema.json
.devpilot/approval/sensitive_action_catalog.json
src/devpilot_core/policy/sensitive_actions.py
tests/test_post_h_012_approval_rbac_hardening.py
```

## Criterios PASS

```text
PASS si el catálogo valida contra SensitiveActionCatalog.
PASS si todos los dominios mínimos están cubiertos.
PASS si las acciones críticas requieren approval y RBAC.
PASS si remote execution, connector write y plugin execution aparecen blocked y non-executable.
PASS si cada miasi_policy_rule_id referenciado existe en `.devpilot/miasi/policy_matrix.json`.
```

## Criterios BLOCK

```text
BLOCK si una acción crítica queda allow sin approval.
BLOCK si remote execution aparece habilitado.
BLOCK si connector write/plugin execution quedan executable.
BLOCK si una acción referencia una regla MIASI inexistente.
```

## Seguridad

```text
network_used=false
external_api_used=false
llm_judge_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## Limitación

Esta es una versión `implemented-initial`: declara y valida el catálogo, pero no aplica todavía enforcement homogéneo en `PolicyEngine`. Ese trabajo queda para POST-H-012-B/C/D/E.
