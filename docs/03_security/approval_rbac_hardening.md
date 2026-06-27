---
doc_id: "POST-H-012-APPROVAL-RBAC-HARDENING"
title: "Approval/RBAC hardening — DevPilot Local"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved_by_owner"
phase: "POST-FASE-H"
source_backlog: "docs/backlogs/POST-H-012_approval_rbac_hardening.md"
local_first: true
dry_run: true
---

# Approval/RBAC hardening — DevPilot Local

## 1. Propósito

Este documento consolida el hardening local de aprobaciones humanas y RBAC implementado en `POST-H-012-A..E`.

DevPilot usa este baseline para bloquear acciones sensibles mediante una cadena determinística:

```text
SensitiveActionCatalog
  -> StrongApprovalBindingValidator
  -> Identity Registry / RBAC
  -> PolicyEngine
  -> quality-gate approval-rbac-hardening
```

El objetivo es gobernar acciones sensibles sin habilitar ejecución remota, connector write, plugin execution, APIs externas ni mutaciones destructivas.

## 2. Alcance operativo

Incluye:

```text
- Catálogo local de acciones sensibles.
- Binding fuerte de approval_id a actor, role_at_decision, tool_id, action, subject, command_id y tool_call_id.
- RBAC local por actor, rol, acción e interfaz.
- PolicyEngine con findings normalizados: APPROVAL_REQUIRED, RBAC_DENIED y APPROVAL_SCOPE_MISMATCH.
- Subgate approval-rbac-hardening dentro de quality-gate hardening/industrial.
- Runbook de ciclo request/approve/deny/revoke con ejemplos seguros.
```

No incluye:

```text
- OAuth/OIDC.
- IAM enterprise.
- Multiusuario remoto.
- Remote execution.
- Connector write.
- Plugin execution.
- Bypass de PathGuard, SecretGuard, CostGuard, PromptInjectionGuard o ToolInjectionGuard.
```

## 3. Contrato de acción sensible

Toda acción sensible debe estar declarada en `.devpilot/approval/sensitive_action_catalog.json` con, como mínimo:

```text
action_id
domain
risk_level
requires_approval
requires_rbac_role
requires_command_binding
requires_tool_call_binding
allowed_interfaces
blocked_interfaces
default_effect
executable
source_mutation_allowed
```

Criterio operativo: una acción crítica no puede quedar `allow` sin approval, rol RBAC y scope exacto. Si la acción aparece como `blocked`, `deny`, `executable=false` o `source_mutation_allowed=false`, permanece bloqueada aunque exista metadata de approval/RBAC.

## 4. Ciclo de aprobación local

### 4.1 Solicitud

```powershell
$approval = python -m devpilot_core approval request `
  --tool patch.sandbox `
  --action apply `
  --subject changes.patch `
  --actor local-owner `
  --reason "Revisión local dry-run de patch" `
  --scope '{"actor_id":"local-owner","role_at_decision":"maintainer","command_id":"cmd-001","tool_call_id":"tool-001"}' `
  --ttl-minutes 60 `
  --json | ConvertFrom-Json

$approvalId = $approval.data.approval.approval_id
```

La solicitud crea un registro `requested`. No autoriza por sí sola la ejecución de la acción.

### 4.2 Consulta

```powershell
python -m devpilot_core approval list --status requested --json
python -m devpilot_core approval show $approvalId --json
```

### 4.3 Aprobación

```powershell
python -m devpilot_core approval approve $approvalId `
  --actor local-owner `
  --reason "Scope revisado; aprobación limitada y temporal" `
  --json
```

La aprobación solo es válida mientras no expire, no sea revocada y coincida exactamente con actor, rol, herramienta, acción, sujeto, `command_id` y `tool_call_id` requeridos.

### 4.4 Denegación

```powershell
python -m devpilot_core approval deny $approvalId `
  --actor local-owner `
  --reason "Riesgo o scope no aceptado" `
  --json
```

### 4.5 Revocación

```powershell
python -m devpilot_core approval revoke $approvalId `
  --actor local-owner `
  --reason "La condición de aprobación ya no aplica" `
  --json
```

La revocación es obligatoria si cambia el diff, sujeto, actor, herramienta, comando, interfaz o contexto de riesgo.

## 5. Validación con PolicyEngine

Ejemplo seguro de verificación local. Debe bloquear porque una acción sensible sin approval válido no puede pasar:

```powershell
python -m devpilot_core policy check publish_deploy_tag `
  --tool release.manager `
  --subject v1.2.3 `
  --actor local-owner `
  --role-at-decision owner `
  --command-id cmd-demo `
  --tool-call-id tool-call-demo `
  --interface cli `
  --json
```

Findings esperados según escenario:

```text
APPROVAL_REQUIRED
APPROVAL_REQUIRED_MISSING
RBAC_DENIED
APPROVAL_SCOPE_MISMATCH
SENSITIVE_ACTION_INTERFACE_BLOCKED
SENSITIVE_ACTION_NON_EXECUTABLE_BLOCKED
```

## 6. Quality gate

`POST-H-012-E` agrega el subgate `approval-rbac-hardening` a los perfiles `hardening` e `industrial`:

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
```

El subgate valida de forma read-only:

```text
- SensitiveActionCatalog.
- RBAC exposure report sin escribir outputs.
- Escenarios determinísticos de PolicyEngine.
- Scope mismatch con StrongApprovalBindingValidator en memoria.
- Documentación de request/approve/deny/revoke.
- Registro en Test Contract Registry v1/v2.
```

## 7. Criterios PASS

```text
PASS si quality-gate hardening incluye approval-rbac-hardening y este subgate pasa.
PASS si acciones críticas sin approval válido bloquean.
PASS si role insuficiente o rol no declarado bloquea.
PASS si scope mismatch bloquea.
PASS si API/UI/agent/remote/connector/plugin no exponen acciones bloqueadas.
PASS si runbook y Human Approval Card explican request, approve, deny, revoke, actor, role_at_decision e interface.
PASS si test-contracts validate y validate-v2 pasan.
```

## 8. Criterios BLOCK

```text
BLOCK si se recomienda approval permanente para acciones críticas.
BLOCK si se omite revocation.
BLOCK si se omite actor, role_at_decision o interface.
BLOCK si una acción critical aparece allow sin approval/RBAC.
BLOCK si remote execution, connector write o plugin execution quedan habilitados.
BLOCK si PolicyEngine deja de evaluar PathGuard, SecretGuard, CostGuard, PromptInjectionGuard o ToolInjectionGuard.
```

## 9. Riesgos y limitaciones

| Riesgo | Estado | Mitigación |
|---|---|---|
| Approval demasiado amplio | Mitigado inicialmente | Binding exacto y bloqueo de wildcard/generic scope. |
| Actor spoofing local | Mitigado inicialmente | `actor_id`, Identity Registry, RBAC y tests negativos. |
| Role taxonomy incompleta | Visible por diseño | Roles requeridos no declarados bloquean; no se infieren permisos implícitos. |
| Acciones críticas por UI/API | Bloqueado | `blocked_interfaces` y deny-by-default. |
| Uso como IAM enterprise | Fuera de alcance | Baseline local-first, no OAuth/OIDC/SSO. |

## 10. Comandos de verificación

```powershell
python -m pytest -p no:ddtrace tests/test_approval_rbac_hardening_gate.py tests/test_post_h_012_approval_rbac_hardening.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core docs-governance validate --json
```

## 11. Reglas de seguridad permanentes del hito

```text
NO approvals globales permanentes para acciones críticas.
NO remote execution.
NO connector write.
NO plugin execution.
NO approval sin expiración para acciones críticas.
NO acción crítica sin RBAC.
NO bypass de PolicyEngine.
NO side effects por ejecutar este quality gate.
```
