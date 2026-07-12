---
doc_id: "ADR-POSTH-034-B"
title: "ADR-POSTH-034-B — Plugin execution enablement decision"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
decision_state: "accepted"
decision_status: "continue-blocked"
micro_sprint: "POST-H-034-B"
phase: "POST-FASE-H"
local_first: true
plugin_execution_enabled: false
runtime_execution_enabled: false
plugin_code_loading_enabled: false
dynamic_import_allowed: false
subprocess_allowed: false
shell_allowed: false
filesystem_write_allowed: false
network_allowed: false
external_api_allowed: false
credentials_required: false
requires_future_enablement_adr: true
requires_future_backlog: true
---

# ADR-POSTH-034-B — Plugin Execution Enablement Decision

## 1. Contexto

DevPilot ya contiene plugin registry, plugin permission model, static validation, metadata runbook y tests de no-execution derivados de POST-H-019. Esa base **no autoriza plugin execution**. POST-H-034-B formaliza la frontera entre plugins como metadata/manifest y cualquier carga o ejecución real de código de plugin.

Estado actual obligatorio:

```text
plugin_execution_enabled=false
runtime_execution_enabled=false
plugin_code_loading_enabled=false
dynamic_import_allowed=false
subprocess_allowed=false
shell_allowed=false
filesystem_write_allowed=false
network_allowed=false
external_api_allowed=false
credentials_required=false
connector_write_enabled=false
remote_execution_enabled=false
```

## 2. Decisión

La decisión aprobada es **`continue-blocked`**.

```text
plugin registry exists != plugin execution enabled
plugin manifest exists != executable code authorization
permission model exists != sandboxed runtime execution
POST-H-034-B ADR exists != runtime enablement
```

POST-H-034-B no carga plugins, no importa código dinámicamente, no ejecuta subprocess/shell, no crea credenciales, no permite red ni APIs externas y no amplía el claim `production-ready-local`.

## 3. Alternativas evaluadas

| Alternativa | Decisión | Motivo |
|---|---|---|
| `continue-blocked` | Aceptada | Es el único estado coherente con la falta de sandbox real de ejecución, firma/verificación, límites de recursos, allowlist de filesystem, audit trail y tests dinámicos con plugin fake malicioso. |
| `pilot-gated-future` | Pospuesta | Puede evaluarse en backlog futuro solo con sandbox no productivo, signing, permission enforcement runtime y kill-switch. |
| `approved-for-future-implementation` | Rechazada para el estado actual | Los prerrequisitos industriales mínimos no están completos. |
| Habilitación inmediata | Prohibida | Violaría los no-go gates actuales y la política de no-execution. |

## 4. Prerrequisitos antes de cualquier piloto futuro

```text
ADR aprobada
Threat model plugin execution
Plugin signing/verification
Permission model enforceable en runtime
Sandbox real de ejecución
Filesystem allowlist
Network disabled by default
Resource limits
Audit trail
Approval/RBAC para plugin install/execute
Supply-chain policy
Kill-switch
Static + dynamic tests con plugin fake malicioso
```

## 5. Criterios PASS

- `plugin_execution_enabled=false` permanece en project_state, matriz y checklist.
- El plugin registry conserva `loading_mode=metadata-only`, `execution_enabled=false` y entrypoints `disabled://`.
- El permission model conserva deny-by-default y niega ejecución, dynamic import, subprocess, network, shell, filesystem write y marketplace.
- El quality gate `sensitive-capability-adr-gate` valida connector write y plugin execution sin ejecutar código.
- No se versionan credenciales ni secretos.

## 6. Criterios BLOCK

- ``plugin_execution_enabled` true` o ``runtime_execution_enabled` true`.
- Cualquier plugin con `execution_enabled=true` o entrypoint ejecutable.
- ``dynamic_import_allowed` true`, ``subprocess_allowed` true`, `shell_allowed=true`, `filesystem_write_allowed=true` o `network_allowed=true`.
- Permission model que permita `plugin.code.execute` o permisos críticos equivalentes.
- Claims que presenten plugin metadata como runtime productivo.

## 7. Consecuencias

- DevPilot mantiene plugins como metadata-only.
- La arquitectura queda preparada para discutir un piloto futuro, pero sin activarlo.
- POST-H-034-C puede continuar con remote execution ADR-3 preservando no-go gates.

## 8. Estado de implementación

`implemented-initial`: la decisión, schema, checklist, manifest, validador y pruebas son suficientes para bloquear activación accidental. No sustituyen un sandbox productivo de plugins, firma de artefactos ni un permission enforcement runtime; esos elementos quedan para backlog futuro.
