---

doc_id: "POST-H-012-BACKLOG"
id: "POST-H-012"
title: "POST-H-012 — Approval/RBAC hardening"
status: "approved"
version: "0.4.0"
owner: "Ordóñez"
updated: "2026-06-27"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "active"
current_micro_sprint: "POST-H-012-C"
next_micro_sprint: "POST-H-012-D"
---

# POST-H-012 — Approval/RBAC hardening

## 1. Objetivo

Endurecer el modelo local de **aprobaciones humanas y RBAC** para que DevPilot pueda controlar acciones sensibles de forma homogénea en CLI, API local, Web UI, agentes, multiagentes, refactor, release, conectores y futuros plugins/remotes sin habilitar capacidades peligrosas.

El objetivo no es crear un sistema IAM enterprise ni autenticación cloud. El objetivo es establecer un baseline local fuerte: actor, rol, scope, acción, herramienta, sujeto, expiración, binding, auditoría y enforcement consistente.

## 2. Contexto y justificación

DevPilot ya tiene módulos iniciales:

```text
src/devpilot_core/approval/models.py
src/devpilot_core/approval/service.py
src/devpilot_core/approval/store.py
src/devpilot_core/approval/policy.py
src/devpilot_core/identity/models.py
src/devpilot_core/identity/registry.py
src/devpilot_core/identity/rbac.py
src/devpilot_core/policy/engine.py
.devpilot/identity/identity_registry.json
```

El diagnóstico post-H identificó riesgos como actor spoofing local, acciones approval-gated no suficientemente vinculadas a tool calls, API/UI sin auth robusta, connector/plugin/remote future risks y necesidad de endurecer aprobaciones antes de permitir cualquier acción con efectos reales.

Problemas actuales a resolver:

```text
- Approval workflow inicial pero no industrial.
- RBAC inicial con scopes todavía limitados.
- Binding approval → tool/action/subject debe reforzarse.
- Falta de tool_call_id / command_id binding obligatorio para acciones críticas.
- Falta de matriz uniforme de permisos por interfaz.
- Falta de reporte de exposición de acciones sensibles.
- Falta de tests negativos suficientes para spoofing, expiration y scope mismatch.
```

## 3. Alcance

Incluye:

```text
- Schema v2 para approval records y identity registry si aplica.
- Catálogo de sensitive actions.
- Binding fuerte approval_id → actor → role → tool_id → action → subject → command_id/tool_call_id.
- Expiración y revocación estricta.
- Reglas RBAC por dominio e interfaz.
- Reporte de coverage de approval/RBAC.
- Integración con PolicyEngine y quality-gate.
- Tests negativos de spoofing, stale approvals y scope mismatch.
```

No incluye:

```text
- OAuth/OIDC.
- Multiusuario remoto.
- SSO.
- Control plane cloud.
- Remote execution.
- Connector write.
- Plugin execution.
- Aprobaciones para acciones fuera del workspace.
```

## 4. Fuentes de entrada obligatorias

```text
src/devpilot_core/approval/
src/devpilot_core/identity/
src/devpilot_core/policy/engine.py
src/devpilot_core/policy/decisions.py
src/devpilot_core/agents/models.py
src/devpilot_core/agents/runtime.py
src/devpilot_core/multiagent/
src/devpilot_core/interfaces/api/
src/devpilot_core/review/
src/devpilot_core/refactor/
src/devpilot_core/release/
.devpilot/miasi/policy_matrix.json
.devpilot/miasi/tool_registry.json
.devpilot/identity/identity_registry.json
docs/03_security/post_h_security_risk_register.md
docs/06_miasi/human_approval_card.md
docs/backlogs/post_h_prioritized_roadmap.md
```

## 5. Entregables

```text
docs/schemas/approval_record_v2.schema.json
docs/schemas/sensitive_action_catalog.schema.json
docs/schemas/rbac_exposure_report.schema.json
.devpilot/approval/sensitive_action_catalog.json
src/devpilot_core/approval/binding.py
src/devpilot_core/approval/hardening.py
src/devpilot_core/identity/exposure.py
src/devpilot_core/policy/sensitive_actions.py
tests/test_post_h_012_approval_rbac_hardening.py
tests/test_approval_binding.py
tests/test_rbac_exposure.py
docs/03_security/approval_rbac_hardening.md
outputs/reports/approval_rbac_exposure.json       # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/policy/engine.py
src/devpilot_core/approval/policy.py
src/devpilot_core/identity/rbac.py
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
docs/05_operations/runbook.md
```

## 6. Modelo de datos mínimo

### 6.1 Sensitive action catalog

```json
{
  "schema_version": "1.0",
  "catalog_id": "devpilot-sensitive-actions",
  "actions": [
    {
      "action_id": "patch.apply",
      "domain": "patch",
      "risk_level": "critical",
      "requires_approval": true,
      "requires_rbac_role": "maintainer",
      "requires_tool_call_binding": true,
      "requires_command_binding": true,
      "allowed_interfaces": ["cli"],
      "blocked_interfaces": ["api", "ui"],
      "default_effect": "block"
    }
  ],
  "safety": {
    "remote_execution_enabled": false,
    "connector_write_enabled": false,
    "plugin_execution_enabled": false
  }
}
```

### 6.2 Approval binding

Un approval endurecido debe vincular:

```text
approval_id
actor_id
role_at_decision
tool_id
action
subject
subject_hash opcional
command_id opcional
tool_call_id opcional
requested_at
expires_at
decision
reason
policy_rule_ids
revoked_at opcional
```

## 7. Principios de diseño

```text
1. Least privilege por defecto.
2. Approval no sustituye RBAC; ambos se combinan.
3. Scope exacto para acciones críticas.
4. Expiración obligatoria para acciones sensibles.
5. Binding fuerte para tool calls y comandos críticos.
6. Deny-by-default para interfaz no declarada.
7. No remote/write/plugin execution en este hito.
8. Auditoría local de toda decisión.
```

## 8. Micro-sprints propuestos

### POST-H-012-A — Sensitive action catalog y schema

Objetivo: declarar de forma machine-readable qué acciones son sensibles y cómo deben gobernarse.

Tareas:

```text
1. Crear sensitive_action_catalog.schema.json.
2. Crear .devpilot/approval/sensitive_action_catalog.json.
3. Incluir dominios: patch, refactor, release, connector, plugin, remote, filesystem, model, agent, approval, identity.
4. Marcar remote/plugin/connector write como blocked.
5. Crear loader y validator.
6. Registrar schema en schema_catalog.json.
```

Criterios PASS:

```text
PASS si el catálogo valida contra schema.
PASS si acciones críticas requieren approval y RBAC.
PASS si remote/plugin/connector write quedan blocked.
PASS si action catalog se cruza con MIASI policy matrix.
```

Criterios BLOCK:

```text
BLOCK si una acción crítica queda allow sin approval.
BLOCK si remote execution aparece habilitado.
BLOCK si connector write/plugin execution quedan como executable.
```

Validación:

```powershell
python -m pytest tests/test_post_h_012_approval_rbac_hardening.py -q
python -m devpilot_core schema validate --schema-id SensitiveActionCatalog --instance .devpilot/approval/sensitive_action_catalog.json --json
```

### POST-H-012-B — Approval binding fuerte

Objetivo: impedir reutilización indebida de approvals y asegurar scope exacto.

Tareas:

```text
1. Implementar src/devpilot_core/approval/binding.py.
2. Agregar matcher estricto de actor/tool/action/subject/command/tool_call.
3. Agregar subject hash opcional para paths o patches.
4. Añadir expiration enforcement.
5. Crear tests negativos: wrong actor, wrong tool, wrong action, expired, revoked, subject mismatch.
```

Criterios PASS:

```text
PASS si un approval solo sirve para su scope.
PASS si approval expirado bloquea.
PASS si approval revocado bloquea.
PASS si subject mismatch bloquea.
PASS si tool_call_id mismatch bloquea cuando es requerido.
```

Criterios BLOCK:

```text
BLOCK si approval genérico puede autorizar acción crítica.
BLOCK si actor spoofing pasa.
BLOCK si expiration es opcional en critical actions.
```

Validación:

```powershell
python -m pytest tests/test_approval_binding.py -q
```

### POST-H-012-C — RBAC exposure report

Objetivo: identificar qué roles pueden ejecutar qué acciones por interfaz y dominio.

Tareas:

```text
1. Implementar src/devpilot_core/identity/exposure.py.
2. Leer identity registry, sensitive action catalog y policy matrix.
3. Generar matrix actor/role/action/interface/effect.
4. Detectar acciones sin rol requerido.
5. Detectar interfaces expuestas indebidamente.
6. Generar outputs/reports/approval_rbac_exposure.json.
```

Criterios PASS:

```text
PASS si reporta todos los dominios críticos.
PASS si detecta acciones sin role binding.
PASS si API/UI no exponen acciones bloqueadas.
PASS si remote/plugin/connector write aparecen blocked.
```

Criterios BLOCK:

```text
BLOCK si una acción critical aparece expuesta sin role.
BLOCK si API/UI pueden ejecutar patch apply, remote o plugin execution.
BLOCK si el reporte ignora identity registry.
```

Validación:

```powershell
python -m devpilot_core identity exposure --json --write-report
python -m pytest tests/test_rbac_exposure.py -q
```

### POST-H-012-D — PolicyEngine enforcement homogéneo

Objetivo: conectar catálogo y binding con PolicyEngine para rutas CLI/API/UI/agents.

Tareas:

```text
1. Integrar sensitive_action_catalog en PolicyEngine.
2. Validar approvals usando binding fuerte.
3. Validar RBAC por actor/role/interface.
4. Agregar findings normalizados para APPROVAL_REQUIRED, RBAC_DENIED, APPROVAL_SCOPE_MISMATCH.
5. Actualizar tests existentes de policy/approval/identity.
```

Criterios PASS:

```text
PASS si PolicyEngine bloquea acciones críticas sin approval válido.
PASS si PolicyEngine bloquea role insuficiente.
PASS si findings explican la causa.
PASS si comandos read-only existentes no se rompen.
```

Criterios BLOCK:

```text
BLOCK si se relaja PathGuard/SecretGuard/CostGuard.
BLOCK si PolicyEngine deja de ser determinístico.
BLOCK si se habilita algún side effect bloqueado por diseño.
```

Validación:

```powershell
python -m pytest tests/test_policy_engine.py tests/test_approval_binding.py tests/test_rbac_exposure.py -q
```

### POST-H-012-E — Quality gate y runbook de aprobación

Objetivo: convertir hardening en gate operacional y documentación de uso.

Tareas:

```text
1. Agregar subgate approval-rbac-hardening al quality gate.
2. Actualizar test contract registry.
3. Crear docs/03_security/approval_rbac_hardening.md.
4. Actualizar human_approval_card y runbook.
5. Documentar comandos de request/approve/deny/revoke con ejemplos seguros.
```

Criterios PASS:

```text
PASS si quality-gate hardening valida approval/RBAC.
PASS si test-contracts validate pasa.
PASS si runbook explica approval lifecycle.
PASS si ejemplos mantienen dry-run por defecto.
```

Criterios BLOCK:

```text
BLOCK si se recomienda approval permanente para acciones críticas.
BLOCK si se omite revocation.
BLOCK si se omite actor/role/interface.
```

Validación:

```powershell
python -m pytest tests/test_post_h_012_approval_rbac_hardening.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 9. Casos de uso soportados al cierre

```text
- Solicitar approval local con scope exacto.
- Aprobar/denegar/revocar approval.
- Bloquear acción crítica sin approval válido.
- Bloquear acción crítica con role insuficiente.
- Ver matriz de exposición RBAC.
- Auditar por qué una acción fue bloqueada.
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Actor spoofing local | Alta | actor_id, role_at_decision, local identity registry y tests negativos. |
| Approval demasiado amplio | Alta | scope exacto y binding obligatorio. |
| Acciones críticas por UI/API | Alta | allowed_interfaces/blocklist por acción. |
| Complejidad excesiva | Media | catálogo explícito, no IAM enterprise. |
| Romper comandos read-only | Media | paridad y tests de no-regresión. |

## 11. No-go gates

```text
NO approvals globales permanentes para critical actions.
NO remote execution.
NO connector write.
NO plugin execution.
NO approval sin expiración en acciones críticas.
NO acción crítica sin RBAC.
NO bypass de PolicyEngine.
```

## 12. Definition of Done del hito

```text
- Sensitive action catalog creado y validado.
- Approval binding fuerte implementado.
- RBAC exposure report implementado.
- PolicyEngine integrado.
- Tests negativos pasan.
- Quality gate actualizado.
- Runbook y documentación actualizados.
```

## 13. Comandos finales esperados

```powershell
python -m devpilot_core approval request --tool-id patch.apply --action apply --subject changes.patch --actor local-admin --json
python -m devpilot_core identity exposure --json --write-report
python -m devpilot_core policy check --tool-id patch.apply --action apply --subject changes.patch --json
python -m pytest tests/test_post_h_012_approval_rbac_hardening.py tests/test_approval_binding.py tests/test_rbac_exposure.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```

## 14. Avance de implementación — POST-H-012-A

Estado: `implemented-initial`.

Capacidad incorporada:

```text
- Sensitive action catalog machine-readable.
- Schema JSON validable por `SensitiveActionCatalog`.
- Catálogo local `.devpilot/approval/sensitive_action_catalog.json`.
- Loader/validator local en `src/devpilot_core/policy/sensitive_actions.py`.
- Cobertura inicial de dominios: patch, refactor, release, connector, plugin, remote, filesystem, model, agent, approval, identity.
- Remote execution, connector write y plugin execution quedan declarados como blocked y non-executable.
- Acciones críticas requieren approval, RBAC role, command binding y tool_call binding.
- Cruce determinístico contra `.devpilot/miasi/policy_matrix.json` y `.devpilot/miasi/tool_registry.json`.
```

Artefactos principales:

```text
docs/schemas/sensitive_action_catalog.schema.json
.devpilot/approval/sensitive_action_catalog.json
src/devpilot_core/policy/sensitive_actions.py
tests/test_post_h_012_approval_rbac_hardening.py
docs/audits/post_h_012_a_sensitive_action_catalog_report.md
docs/post_h_012_a_manifest.json
```

Criterios PASS cubiertos:

```text
PASS si el catálogo valida contra schema.
PASS si acciones críticas requieren approval y RBAC.
PASS si remote/plugin/connector write quedan blocked.
PASS si action catalog se cruza con MIASI policy matrix.
```

Límites explícitos:

```text
POST-H-012-A no cambia todavía PolicyEngine enforcement.
POST-H-012-A no implementa approval binding fuerte.
POST-H-012-A no implementa RBAC exposure report.
POST-H-012-A no habilita ejecución remota, connector write ni plugin execution.
POST-H-012-A no habilita acciones destructivas.
```


## 15. Avance de implementación — POST-H-012-B

Estado: `implemented-initial`.

Capacidad incorporada:

```text
- Binding fuerte de approvals locales mediante `src/devpilot_core/approval/binding.py`.
- Validación exacta approval_id → actor_id → role_at_decision → tool_id → action → subject.
- Validación opcional de `subject_hash` para paths, patches o sujetos materializados.
- Enforcement determinístico de expiración y revocación en el binding.
- Enforcement de `command_id` y `tool_call_id` cuando el SensitiveActionCatalog lo requiere.
- Bloqueo de approvals genéricos/wildcard para acciones sensibles.
- Integración inicial con `ApprovalPolicyChecker` para acciones sensibles declaradas en el catálogo sin activar ejecución real.
```

Artefactos principales:

```text
src/devpilot_core/approval/binding.py
tests/test_approval_binding.py
docs/audits/post_h_012_b_approval_binding_report.md
docs/post_h_012_b_manifest.json
```

Criterios PASS cubiertos:

```text
PASS si un approval solo sirve para su scope.
PASS si approval expirado bloquea.
PASS si approval revocado bloquea.
PASS si subject mismatch bloquea.
PASS si tool_call_id mismatch bloquea cuando es requerido.
```

Límites explícitos:

```text
POST-H-012-B no implementa todavía RBAC exposure report.
POST-H-012-B no implementa enforcement homogéneo completo en PolicyEngine para todas las rutas CLI/API/UI/agents.
POST-H-012-B no agrega quality-gate approval-rbac-hardening.
POST-H-012-B no habilita ejecución remota, connector write, plugin execution ni acciones destructivas.
```


## 16. Avance de implementación — POST-H-012-C

Estado: `implemented-initial`.

Capacidad incorporada:

```text
- Reporte local de exposición Approval/RBAC mediante `src/devpilot_core/identity/exposure.py`.
- CLI `python -m devpilot_core identity exposure --json` y escritura explícita con `--write-report`.
- Schema `docs/schemas/rbac_exposure_report.schema.json` registrado como `RbacExposureReport`.
- Matriz actor/role/action/interface/effect construida desde Identity Registry, SensitiveActionCatalog y MIASI policy matrix.
- Detección de acciones críticas sin rol requerido o con roles no declarados.
- Verificación de que API/UI no exponen acciones críticas catalogadas.
- Verificación de que remote execution, plugin execution y connector write permanecen bloqueados y non-executable.
```

Artefactos principales:

```text
src/devpilot_core/identity/exposure.py
docs/schemas/rbac_exposure_report.schema.json
tests/test_rbac_exposure.py
docs/audits/post_h_012_c_rbac_exposure_report.md
docs/post_h_012_c_manifest.json
outputs/reports/approval_rbac_exposure.json  # generado, no versionable
```

Criterios PASS cubiertos:

```text
PASS si reporta todos los dominios críticos.
PASS si detecta acciones sin role binding.
PASS si API/UI no exponen acciones bloqueadas.
PASS si remote/plugin/connector write aparecen blocked.
```

Límites explícitos:

```text
POST-H-012-C no concede permisos ni ejecuta acciones.
POST-H-012-C no implementa todavía enforcement homogéneo completo en PolicyEngine.
POST-H-012-C no agrega todavía el subgate approval-rbac-hardening.
Los reportes bajo outputs/reports son evidencia runtime regenerable y no fuente versionable.
Remote execution, connector write, plugin execution y acciones destructivas siguen bloqueadas.
```
