---
doc_id: DEVPL-MP-SUCCESSOR-132-CONFIGURATION_AUTHORITY_MATRIX_132
title: "Configuración por scope, persistencia, permisos y UX"
version: "1.1.0"
status: "OWNER_APPROVED_PROGRAM"
baseline_commit: "8db5b44694abcced3231183e05731e732f5b8f24"
owner: "Owner DevPilot"
supersedes_program: "DEVPL_MP_SUCCESSOR_131 v1.0.0"
execution_authority: false
approval_revision: 1
approval_date: "2026-10-13"
approved_by: "Owner Ordóñez (instrucción explícita en conversación)"
approval_scope: "PROGRAMMATIC_PLANNING_ONLY"
owner_decision_ref: "DEVPL-MP-132-OWNER-APPROVAL-133"
---

# Configuración por scope, persistencia, permisos y UX

## Matriz de dominios

| Dominio | Fuente candidata | Alcance | Modificación |
|---|---|---|---|
| Preferencias globales | installation settings versionados | Instalación | Validación typed; no secrets en archivo visible |
| Workspaces/root authorized | workspace registry / policy | Workspace | Owner + boundary check |
| Perfil de proyecto/estándares | `.devpilot/project.yaml` y PESP | Proyecto | Successor con revisión |
| Security/egress/CostGuard | `.devpilot/policy.yaml`, policies canónicas | Deny floor global + scopes | Approval-gated, no project override weaker |
| Providers/config | Provider registry/config con secrets-by-reference | Global/proyecto según policy | Plan / validate / controlled apply |
| Runtime kill/revoke | Runtime operational store | Proceso/referencia | Acción operacional independiente auditada |
| Diagnostics/traces/health | Observability store | Read-only | No mutable settings |
| Guided/Expert | User/session preference | UI | Nunca concede RBAC |

Cada setting: `key,namespace,scope,authority_ref,persisted_location,type/default,effective_value,origin,override_rule,permission,approval,restart_required,effect,rollback,status`. Mostrar origen/effective en Guided y diagnostico en Expert.

## UI objetivo

Settings Home: preparación global, configuración efectiva y accesos. Subsuperficies `General`, `Modelos/Proveedores`, `Seguridad/Políticas`, `Proyecto Activo`; Runtime Control/kill y Diagnostics fuera de la edición persistente, aunque tengan links desde Settings. No una pantalla infinita con acordeones. Cada botón muestra efecto, scope, permiso y feedback in situ.

## Migración y seguridad

Auditar `SettingsView.ts`, `settings_service.py`, endpoints provider y stores en HEAD vivo; no editor YAML write-anything ni sobrescritura de archivos. Preserve MP-0F disclosure parcial. Tests persist/restart, RBAC/CSRF, concurrent changes, rollback, kill switch, no egress, no secrets y UI browser. Fase temprana R0 audit, R1 vertical, R2 local model, R7 agents, R8 external.
