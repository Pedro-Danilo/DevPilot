---
doc_id: "POST-H-034-TOPLEVEL"
title: "POST-H-034 — ADRs de capacidades sensibles"
original_doc_id: "DEVPL-BACKLOG-POST-H-034-SENSITIVE-CAPABILITIES-ADRS-V1"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
roadmap_wave: "Ola 9"
roadmap_source: "devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md"
implementation_status: "active/post-h-034-c-implemented-initial"
current_micro_sprint: "POST-H-034-C"
next_micro_sprint: "POST-H-034-D"
repo_baseline: "repo_DevPilot_Local_307_POST_H_033_F.zip"
created_for: "DevPilot Local"
scope: "architecture decisions / no-go gates / sensitive capability enablement prerequisites"
preliminary: true
---

# POST-H-034 — ADRs de capacidades sensibles

## 1. Proposito del backlog

POST-H-034 convierte la Ola 9 del roadmap post POST-H-025 en un backlog ejecutable para formalizar decisiones arquitectonicas antes de habilitar capacidades sensibles: connector write, plugin execution, remote execution, multiusuario/auth productivo, enterprise y SaaS.

Este backlog no implementa esas capacidades. Su objetivo industrial es crear ADRs, threat models, go/no-go checklists, criterios de habilitacion, criterios de bloqueo, evidence requirements y quality gates que impidan que capacidades design-only, metadata-only o read-only sean confundidas con autorizacion productiva.

El estado actual de DevPilot es `production-ready-local` acotado. POST-H-034 debe preservar:

- `remote_execution_enabled=false`;
- `connector_write_enabled=false`;
- `plugin_execution_enabled=false`;
- `enterprise_ready=false`;
- `saas_ready=false`;
- `compliance_certified=false`;
- `production_multiuser=false`.

## 2. Fuentes consultadas

Se consultaron como fuentes de verdad para formular este backlog:

- `devpilot_post_h_025_roadmap_detallado_v3_agentes_validadores.md`.
- `devpilot_onboarding_report_final_compilado.md`.
- `repo_DevPilot_Local_262_POST_H_025_E.zip`, descomprimido en entorno local de trabajo.

Evidencia tecnica relevante observada:

- El roadmap define la Ola 9 como `POST-H-034: ADRs de capacidades sensibles`.
- El objetivo declarado es formalizar decisiones antes de habilitar remote, connector write, plugin execution, multiusuario, enterprise o SaaS.
- El roadmap fija cinco micro-sprints: `POST-H-034-A` a `POST-H-034-E`.
- El informe final declara restricciones activas: local-first, no remote execution, no connector write, no plugin execution, no SaaS, no enterprise-ready y no compliance-certified.
- El repo ya contiene backlogs y artefactos previos para conectores, plugins, remote, secure transport, compliance y enterprise threat model: POST-H-018, POST-H-019, POST-H-020, POST-H-021, POST-H-022 y POST-H-023.
- El repo contiene `docs/adr/ADR-POSTH-004-remote-runner-adr2.md` y `docs/adr/ADR-POSTH-005-secure-transport-design-only.md`, ambos de naturaleza design-only.
- El repo contiene dominios relevantes: `connectors`, `plugins`, `remote`, `identity`, `approval`, `policy`, `enterprise`, `compliance`, `interfaces/api/security.py`.
- El repo ya tiene tests de bloqueo y diseno: `test_post_h_018_*`, `test_post_h_019_*`, `test_post_h_021_*`, `test_post_h_022_*`, `test_post_h_023_*`, `test_identity_rbac.py`, `test_rbac_exposure.py`, `test_approval_binding.py`, `test_policy_engine_approval_rbac_enforcement.py`, `test_api_security.py`, `test_enterprise_reporting.py` y `test_post_h_020_compliance_no_certification.py`.

## 3. Estado base y problema a resolver

DevPilot ya contiene componentes preparatorios para capacidades sensibles:

- conectores con sandbox, replay, policy binding y deny-write;
- plugins con metadata, permission model, static validator y no execution;
- remote runner con registry/readiness design-only y execution disabled;
- secure transport design-only;
- identity/RBAC local inicial;
- approval binding;
- API local token/CORS/policy;
- enterprise threat model design-only;
- compliance mapping no certificante.

El problema industrial es que la existencia de esos componentes puede ser interpretada erroneamente como autorizacion de uso productivo. POST-H-034 debe crear la capa de decision que separa claramente:

- `exists as design/metadata/readiness` de `enabled as production capability`;
- `read-only/dry-run/replay` de `write/execute`;
- `local token` de `multiuser auth`;
- `enterprise threat model` de `enterprise-ready`;
- `compliance mapping` de `compliance certification`;
- `secure transport design` de `remote-ready`.

## 4. Objetivos industriales

POST-H-034 debe lograr:

- Crear ADRs formales para cada capacidad sensible.
- Definir prerrequisitos de habilitacion futura.
- Mantener no-go gates actuales como default.
- Crear go/no-go checklists por capacidad.
- Definir evidence requirements por capacidad.
- Definir tests y quality gates que bloqueen activacion accidental.
- Definir ownership y decision authority.
- Alinear README, runbook, project_state, source registry y TCR.
- Evitar claims prematuros.
- Establecer criterios para backlog futuro de implementacion, si alguna decision se aprueba.

## 5. No objetivos

Este backlog no debe:

- Habilitar connector write.
- Habilitar plugin execution.
- Habilitar remote execution.
- Habilitar multiusuario productivo.
- Habilitar SaaS/control plane.
- Declarar enterprise-ready.
- Declarar compliance-certified.
- Crear credenciales reales.
- Crear tenants reales.
- Abrir APIs a red externa.
- Permitir OAuth/OIDC productivo.
- Ejecutar plugins, conectores write o comandos remotos.
- Reducir no-go gates vigentes.
- Modificar `production-ready-local` hacia claims mas amplios.

## 6. Principios de diseno

### 6.1 ADR antes de enablement

Ninguna capacidad sensible puede pasar de design-only/read-only a execute/write/network-enabled sin ADR aprobada, backlog especifico, threat model, tests, quality gate y evidencia.

### 6.2 No-go gates por defecto

El estado por defecto sigue siendo bloqueado:

```text
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
external_api_required=false
enterprise_ready_claim=false
saas_ready_claim=false
compliance_certification_claim=false
```

### 6.3 Decision separada de implementacion

Una ADR aceptada puede decidir `continue-blocked`, `pilot-gated`, `design-only` o `approved-for-future-implementation`. Ninguna ADR de POST-H-034 debe activar por si sola runtime productivo.

### 6.4 Evidencia antes de claims

Todo claim nuevo debe tener evidencia regenerable, tests, audit report y decision formal. Sin evidencia, el claim queda prohibido.

### 6.5 Human approval y rollback como prerrequisito

Las capacidades con side effects requieren approval/RBAC, audit trail, rollback o compensacion, kill-switch y observabilidad.

## 7. Artefactos globales previstos

### 7.1 Nuevos ADRs

- `docs/adr/ADR-POSTH-034-A-connector-write-enable-or-continue-blocked.md`
- `docs/adr/ADR-POSTH-034-B-plugin-execution-enable-or-continue-blocked.md`
- `docs/adr/ADR-POSTH-034-C-remote-execution-adr3.md`
- `docs/adr/ADR-POSTH-034-D-multiuser-auth-boundary.md`
- `docs/adr/ADR-POSTH-034-E-enterprise-saas-boundary.md`

### 7.2 Nuevos schemas

- `docs/schemas/sensitive_capability_adr.schema.json`
- `docs/schemas/sensitive_capability_enablement_checklist.schema.json`
- `docs/schemas/sensitive_capability_decision_report.schema.json`
- `docs/schemas/connector_write_decision.schema.json`
- `docs/schemas/plugin_execution_decision.schema.json`
- `docs/schemas/remote_execution_adr3_decision.schema.json`
- `docs/schemas/multiuser_auth_decision.schema.json`
- `docs/schemas/enterprise_saas_boundary_decision.schema.json`

### 7.3 Nuevos artefactos `.devpilot`

- `.devpilot/sensitive_capabilities/capability_decision_matrix.json`
- `.devpilot/sensitive_capabilities/connector_write_enablement_checklist.json`
- `.devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json`
- `.devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json`
- `.devpilot/sensitive_capabilities/multiuser_auth_checklist.json`
- `.devpilot/sensitive_capabilities/enterprise_saas_boundary_checklist.json`

### 7.4 Nuevos modulos previstos

- `src/devpilot_core/sensitive_capabilities/models.py`
- `src/devpilot_core/sensitive_capabilities/decision_matrix.py`
- `src/devpilot_core/sensitive_capabilities/validator.py`
- `src/devpilot_core/sensitive_capabilities/quality_gate.py`

### 7.5 Reportes y manifests

- `docs/audits/post_h_034_a_connector_write_adr_report.md`
- `docs/audits/post_h_034_b_plugin_execution_adr_report.md`
- `docs/audits/post_h_034_c_remote_execution_adr3_report.md`
- `docs/audits/post_h_034_d_multiuser_auth_adr_report.md`
- `docs/audits/post_h_034_e_enterprise_saas_boundary_adr_report.md`
- `docs/post_h_034_a_manifest.json`
- `docs/post_h_034_b_manifest.json`
- `docs/post_h_034_c_manifest.json`
- `docs/post_h_034_d_manifest.json`
- `docs/post_h_034_e_manifest.json`

### 7.6 Tests previstos

- `tests/test_post_h_034_connector_write_adr.py`
- `tests/test_post_h_034_plugin_execution_adr.py`
- `tests/test_post_h_034_remote_execution_adr3.py`
- `tests/test_post_h_034_multiuser_auth_adr.py`
- `tests/test_post_h_034_enterprise_saas_boundary_adr.py`
- `tests/test_post_h_034_sensitive_capability_decision_gate.py`

## 8. Micro-sprints

## POST-H-034-A - Connector write ADR

### Objetivo

Crear ADR para decidir si `connector write` permanece bloqueado o si puede avanzar a un piloto futuro gated, sin habilitar escritura en este sprint.

### Contexto

POST-H-018 cerro connector sandbox con deny-write, replay fixtures, redaction, policy binding y quality gate. Ese cierre no habilita escritura. La ADR debe formalizar que se requiere para evaluar escritura real.

### Entregables

- ADR `ADR-POSTH-034-A-connector-write-enable-or-continue-blocked.md`.
- Schema `ConnectorWriteDecision`.
- Checklist `.devpilot/sensitive_capabilities/connector_write_enablement_checklist.json`.
- Reporte de decision POST-H-034-A.
- Tests de no-go connector write.
- Actualizacion de runbook connector sandbox.
- Manifest POST-H-034-A.

### Decision options permitidas

- `continue-blocked`: mantener connector write bloqueado.
- `pilot-gated-future`: permitir backlog futuro para fake/write sandbox no productivo.
- `approved-for-future-implementation`: solo si existen todos los prerrequisitos, no esperado en estado actual.
- `rejected`: rechazar connector write para el ciclo actual.

### Prerrequisitos minimos para cualquier piloto futuro

- ADR aprobada.
- Threat model por conector write.
- Connector sandbox con rollback/compensacion.
- Fake connector write tests.
- Replay fixtures negativos.
- Approval/RBAC por actor, connector_id, operation_id y subject.
- Secret handling no versionado.
- Observability y audit trail.
- Data classification.
- Rate limits y idempotency.
- Kill-switch.
- Quality gate `connector-write-disabled-or-approved`.

### Criterios PASS

- ADR deja claro que POST-H-034-A no habilita connector write.
- Checklist valida contra schema.
- No-go gate actual sigue bloqueando write.
- Cualquier connector write sin approval queda BLOCK.
- Runbook mantiene instrucciones de deny-write.
- Claims no cambian.

### Criterios BLOCK

- ADR habilita escritura inmediata.
- Se agregan credenciales reales o tokens.
- Se permite API externa real.
- Se interpreta sandbox/replay como write.
- Falta rollback, approval o audit trail en prerrequisitos.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_connector_write_adr.py `
  tests/test_post_h_018_connector_sandbox_policy.py `
  tests/test_post_h_018_connector_sandbox_runner.py `
  tests/test_post_h_018_connector_replay.py `
  tests/test_post_h_018_connector_policy_binding.py `
  tests/test_post_h_018_connector_sandbox_gate.py `
  tests/test_connector_registry.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  -q
```

## POST-H-034-B - Plugin execution ADR

### Objetivo

Crear ADR para decidir si `plugin execution` permanece bloqueado o si puede avanzar a un piloto futuro gated, sin ejecutar plugins en este sprint.

### Contexto

POST-H-019 dejo plugins como metadata, static validation, permission model y no-execution policy. La ADR debe separar plugin registry/manifest de plugin execution.

### Entregables

- ADR `ADR-POSTH-034-B-plugin-execution-enable-or-continue-blocked.md`.
- Schema `PluginExecutionDecision`.
- Checklist `.devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json`.
- Reporte de decision POST-H-034-B.
- Tests de no-go plugin execution.
- Actualizacion de plugin metadata runbook.
- Manifest POST-H-034-B.

### Prerrequisitos minimos para cualquier piloto futuro

- ADR aprobada.
- Threat model plugin execution.
- Plugin signing/verification.
- Permission model enforceable.
- Sandbox real de ejecucion.
- Filesystem allowlist.
- Network disabled by default.
- Resource limits.
- Audit trail.
- Approval/RBAC para plugin install/execute.
- Supply-chain policy.
- Kill-switch.
- Static + dynamic tests con plugin fake malicioso.

### Criterios PASS

- ADR deja claro que plugin execution sigue blocked.
- Plugin manifests no equivalen a codigo ejecutable autorizado.
- Permission model no permite bypass.
- Quality gate bloquea execution.
- No se ejecuta codigo de plugin en tests.

### Criterios BLOCK

- Plugin execution habilitado inmediato.
- Plugin puede ejecutar shell/subprocess.
- Plugin puede leer secretos.
- Plugin puede escribir fuera de sandbox.
- Falta firma, permission model o audit trail.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_plugin_execution_adr.py `
  tests/test_post_h_019_plugin_sandbox_design.py `
  tests/test_post_h_019_plugin_permission_model.py `
  tests/test_post_h_019_plugin_static_validator.py `
  tests/test_post_h_019_plugin_execution_blocked.py `
  tests/test_post_h_019_plugin_quality_gate.py `
  tests/test_plugin_registry.py `
  tests/test_secret_guard_hardening.py `
  -q
```

## POST-H-034-C - Remote execution ADR-3

### Objetivo

Crear ADR-3 para remote execution, posterior a ADR-2 y secure transport design, definiendo si remote execution sigue bloqueado o si puede avanzar a un backlog futuro de piloto gated.

### Contexto

ADR-POSTH-004 Remote Runner ADR-2 mantiene remote execution disabled/design-only. POST-H-023 agrego secure transport design, no transporte activo. La ADR-3 debe decidir si existen condiciones para avanzar hacia enablement futuro, sin habilitar ejecucion remota.

### Entregables

- ADR `ADR-POSTH-034-C-remote-execution-adr3.md`.
- Schema `RemoteExecutionAdr3Decision`.
- Checklist `.devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json`.
- Reporte de decision POST-H-034-C.
- Tests de remote disabled invariants.
- Actualizacion de remote runner y secure transport runbooks.
- Manifest POST-H-034-C.

### Prerrequisitos minimos para cualquier piloto futuro

- ADR-3 aprobada.
- Secure transport implementado, no solo design-only.
- Identity/RBAC robusto.
- Approval binding por command_id, actor, target, workspace y risk.
- Remote sandbox.
- Filesystem isolation.
- Command allowlist.
- Secrets handling.
- Observability end-to-end.
- Kill-switch.
- Rollback/cleanup.
- Network security tests.
- Fake remote runner tests.
- No cloud control plane sin ADR separada.

### Criterios PASS

- ADR-3 no habilita ejecucion remota por si misma.
- Remote runner sigue disabled.
- Secure transport design no se interpreta como remote-ready.
- Tests remote disabled siguen pasando.
- No se agregan credenciales reales.
- Claims `remote-ready` siguen prohibidos.

### Criterios BLOCK

- `remote_execution_enabled=true`.
- Shell remoto permitido.
- Red requerida para tests.
- Credenciales remotas versionadas.
- Falta sandbox, RBAC, approval o kill-switch.
- Se declara remote-ready.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_remote_execution_adr3.py `
  tests/test_post_h_021_remote_adr2.py `
  tests/test_post_h_021_remote_readiness_report.py `
  tests/test_post_h_021_remote_quality_gate.py `
  tests/test_post_h_021_remote_disabled_invariants.py `
  tests/test_post_h_023_secure_transport_design.py `
  tests/test_post_h_023_secure_transport_validator.py `
  tests/test_post_h_023_secure_transport_closure.py `
  -q
```

## POST-H-034-D - Multiuser/auth ADR

### Objetivo

Crear ADR para definir frontera entre auth local actual y un eventual modelo multiusuario productivo, sin habilitar multiusuario en este sprint.

### Contexto

DevPilot tiene API local con token/CORS/policy, identity/RBAC inicial y approvals. Eso no equivale a IAM enterprise, login multiusuario, tenancy ni sesiones productivas.

### Entregables

- ADR `ADR-POSTH-034-D-multiuser-auth-boundary.md`.
- Schema `MultiuserAuthDecision`.
- Checklist `.devpilot/sensitive_capabilities/multiuser_auth_checklist.json`.
- Reporte de decision POST-H-034-D.
- Tests de boundary local auth vs multiuser.
- Actualizacion de API security/runbook.
- Manifest POST-H-034-D.

### Decisiones que debe cubrir la ADR

- Mantener API local token como control local, no IAM enterprise.
- Definir si multiuser es `rejected`, `future`, `pilot-gated` o `out-of-scope`.
- Separar actor local, RBAC local y usuario real.
- Definir session model futuro.
- Definir passwordless/OIDC/local accounts solo como opciones evaluadas.
- Definir tenant/data isolation requirements.
- Definir audit and approval binding por usuario real.
- Definir threat model de auth.

### Prerrequisitos minimos para cualquier piloto futuro

- ADR aprobada.
- Threat model auth.
- Identity registry productivo o adapter.
- Session management.
- CSRF/CORS/token hardening.
- RBAC enforcement por endpoint y action.
- Approval actor binding no spoofable.
- Audit trail.
- Data isolation.
- Secret handling.
- Tests de bypass.
- UI auth flow si aplica.

### Criterios PASS

- ADR no declara multiuser productivo.
- API local token sigue descrito como local control.
- UI no se presenta como enterprise console.
- RBAC/approval local se mantiene como implemented-initial.
- Tests de API security siguen pasando.

### Criterios BLOCK

- Se declara production multiuser.
- Se expone API como public/enterprise-ready.
- Se relaja CORS/token.
- Approval actor binding se vuelve spoofable.
- Falta threat model auth.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_multiuser_auth_adr.py `
  tests/test_api_security.py `
  tests/test_identity_rbac.py `
  tests/test_rbac_exposure.py `
  tests/test_approval_binding.py `
  tests/test_approval_policy_binding.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  tests/test_application_boundary_policy.py `
  -q
```

## POST-H-034-E - Enterprise/SaaS boundary ADR

### Objetivo

Crear ADR que delimite enterprise y SaaS como capacidades futuras, separadas del producto local `production-ready-local`, y que defina prerrequisitos para cualquier evolucion cloud, enterprise o compliance-certified.

### Contexto

POST-H-022 aporta enterprise threat model design-only. POST-H-020 aporta compliance mapping no certificante. El informe final es explicito: DevPilot no es SaaS, no es enterprise-ready, no es compliance-certified y no tiene tenancy.

### Entregables

- ADR `ADR-POSTH-034-E-enterprise-saas-boundary.md`.
- Schema `EnterpriseSaasBoundaryDecision`.
- Checklist `.devpilot/sensitive_capabilities/enterprise_saas_boundary_checklist.json`.
- Reporte de decision POST-H-034-E.
- Tests de no enterprise/SaaS/compliance overclaim.
- Actualizacion de enterprise/compliance runbooks.
- Manifest POST-H-034-E.

### Decisiones que debe cubrir la ADR

- Enterprise-ready queda prohibido hasta backlog futuro.
- SaaS-ready queda prohibido hasta arquitectura cloud/tenancy.
- Compliance-certified queda prohibido hasta proceso externo.
- Compliance mapping sigue siendo no certificante.
- Enterprise threat model sigue design-only.
- Se requiere arquitectura de deployment, auth, tenancy, data isolation, privacy, logging, SLO/SLA, support model y legal/compliance.

### Prerrequisitos minimos para cualquier backlog futuro

- Enterprise/SaaS architecture.
- Tenant isolation.
- Multiuser auth.
- Data retention/privacy policy.
- Cloud deployment model.
- Backup/restore enterprise.
- Observability backend.
- Incident response.
- Support/SLA model.
- Legal/compliance scope.
- External audit plan si se pretende certificacion.
- Security tests y threat model.
- Migration plan desde local-first.

### Criterios PASS

- ADR mantiene enterprise/SaaS como out-of-scope o future gated.
- Claims prohibidos siguen bloqueados.
- Compliance mapping no se presenta como certificacion.
- Enterprise threat model no se interpreta como enterprise-ready.
- Production-ready-local conserva alcance local.

### Criterios BLOCK

- Se declara enterprise-ready.
- Se declara SaaS-ready.
- Se declara compliance-certified.
- Se habilita tenancy sin auth/data isolation.
- Se presentan reports internos como auditoria externa.

### Validacion focal esperada

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_enterprise_saas_boundary_adr.py `
  tests/test_post_h_022_enterprise_threat_model.py `
  tests/test_post_h_022_enterprise_closure.py `
  tests/test_enterprise_reporting.py `
  tests/test_post_h_020_compliance_no_certification.py `
  tests/test_post_h_020_compliance_runbook_disclaimers.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  tests/test_post_h_025_production_ready_final_declaration.py `
  -q
```


## Estado de implementación POST-H-034-B

POST-H-034-B queda implementado como `implemented-initial`: se crea la ADR aprobada de `plugin.execution`, el schema `PluginExecutionDecision`, el checklist `.devpilot/sensitive_capabilities/plugin_execution_enablement_checklist.json`, el reporte, el manifest y pruebas focales. La decisión es `continue-blocked`: no se ejecutan plugins, no se carga código, no se habilitan dynamic import/subprocess/shell/filesystem write/network/API externa y no se amplían claims productivos.

El resultado es deliberadamente conservador. Para una versión industrial futura se requiere backlog separado con sandbox real, firma/verificación de plugins, permission enforcement runtime, límites de recursos, audit trail, Approval/RBAC, kill-switch y pruebas dinámicas con plugin fake malicioso.

## 9. Definition of Done del backlog POST-H-034

El backlog completo se puede cerrar solo si:

- Existen cinco ADRs versionadas y aprobadas o propuestas formalmente.
- Cada ADR define decision state, allowed states, rejected alternatives, prerequisites, no-go gates y future backlog triggers.
- La capability decision matrix valida contra schema.
- Los no-go gates actuales siguen activos.
- No se habilita connector write.
- No se habilita plugin execution.
- No se habilita remote execution.
- No se habilita multiusuario productivo.
- No se declara enterprise-ready.
- No se declara SaaS-ready.
- No se declara compliance-certified.
- README, runbook, project_state, source registry, schema catalog y TCR quedan sincronizados.
- Claims validator sigue bloqueando overclaims.
- Quality gate nuevo bloquea activacion accidental.

## 10. Quality gates requeridos

### Gates existentes obligatorios

Deben seguir pasando:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

### Gate nuevo recomendado

Crear subgate:

```text
sensitive-capability-adr-gate
```

El gate debe verificar:

- ADR existe para cada capacidad sensible.
- Decision state es permitido.
- No-go gates siguen en falso.
- Cualquier `pilot-gated-future` tiene prerequisites completos.
- Ningun claim prohibido aparece como permitido.
- Capability decision matrix valida contra schema.
- No hay credenciales reales.
- No hay network/external API requerida.
- No hay runtime enablement accidental.

## 11. Regresion focal acumulada recomendada

Durante POST-H-034 no se recomienda usar `pytest -q` completo como validacion primaria. La validacion focal acumulada debe incluir:

```powershell
$env:PYTHONPATH="src"
python -m pytest -p no:ddtrace --assert=plain `
  tests/test_post_h_034_connector_write_adr.py `
  tests/test_post_h_034_plugin_execution_adr.py `
  tests/test_post_h_034_remote_execution_adr3.py `
  tests/test_post_h_034_multiuser_auth_adr.py `
  tests/test_post_h_034_enterprise_saas_boundary_adr.py `
  tests/test_post_h_034_sensitive_capability_decision_gate.py `
  tests/test_post_h_018_connector_sandbox_gate.py `
  tests/test_post_h_019_plugin_execution_blocked.py `
  tests/test_post_h_021_remote_disabled_invariants.py `
  tests/test_post_h_023_secure_transport_closure.py `
  tests/test_identity_rbac.py `
  tests/test_rbac_exposure.py `
  tests/test_api_security.py `
  tests/test_approval_binding.py `
  tests/test_policy_engine_approval_rbac_enforcement.py `
  tests/test_post_h_022_enterprise_closure.py `
  tests/test_post_h_020_compliance_no_certification.py `
  tests/test_post_h_025_production_ready_claims_validator.py `
  -q
```

Validaciones CLI/documentales:

```powershell
python -m devpilot_core docs-governance validate --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core test-contracts validate-v2 --json
python -m devpilot_core project-state validate --json
python -m devpilot_core schema list --json
python -m devpilot_core cli-registry guard --json
```

## 12. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
| --- | --- | --- |
| ADR interpretada como enablement | Critico | Decision states y no-go gates explicitos |
| Connector write accidental | Critico | Quality gate, deny-write, approval/RBAC prerequisites |
| Plugin execution accidental | Critico | No execution tests, permission model, sandbox prerequisites |
| Remote execution accidental | Critico | Remote disabled invariants y ADR-3 sin enablement |
| Multiuser claim prematuro | Alto | Auth boundary ADR y API local token wording |
| Enterprise/SaaS overclaim | Critico | Claims validator y enterprise/SaaS boundary ADR |
| Compliance mapping tratado como certificacion | Alto/legal | No-certification disclaimers y tests |
| Credenciales versionadas | Critico | SecretGuard, docs governance, no real secrets |

## 13. Dependencias

- POST-H-018 connector sandbox.
- POST-H-019 plugin sandbox design.
- POST-H-020 compliance mapping packs.
- POST-H-021 remote runner ADR-2.
- POST-H-022 enterprise deployment threat model.
- POST-H-023 secure transport design.
- POST-H-025 production-ready local claims/no-go gates.
- POST-H-032 tool/MCP/agents, si alguna ADR referencia tool execution.
- POST-H-033 schema-backed validators, si ya existe al implementar decision matrix.

## 14. Decisiones arquitectonicas

Este backlog es, por definicion, un backlog de decisiones arquitectonicas. Cada micro-sprint debe producir ADR formal.

Estados de decision permitidos:

- `continue-blocked`;
- `design-only`;
- `pilot-gated-future`;
- `approved-for-future-implementation`;
- `rejected`;
- `out-of-scope`.

Estados no permitidos en POST-H-034:

- `enabled-now`;
- `production-enabled`;
- `enterprise-ready`;
- `saas-ready`;
- `remote-ready`;
- `compliance-certified`.

## 15. Ruta recomendada en el repo

Guardar este backlog en:

```text
docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md
```

Opcionalmente, si se mantiene un documento top-level por backlog activo:

```text
docs/POST-H-034_sensitive_capabilities_adrs.md
```

## 16. Commit sugerido para incorporar el backlog

```bash
git add docs/backlogs/POST-H-034_sensitive_capabilities_adrs.md
git commit -m "Add POST-H-034 sensitive capability ADR backlog"
```

## 17. Cierre esperado de POST-H-034

POST-H-034 debe cerrar con una frontera arquitectonica clara para capacidades sensibles. El resultado correcto no es habilitar funcionalidades de alto riesgo, sino impedir activacion accidental y preparar decisiones futuras con criterios verificables. DevPilot debe seguir siendo `production-ready-local`, no enterprise-ready, no SaaS-ready, no remote-ready, no compliance-certified y sin side effects externos no autorizados.

## 18. Estado de implementación acumulado

### POST-H-034-A — Connector write ADR

Estado: `implemented-initial`. El backlog fue elevado a `approved` para iniciar la Ola 9. POST-H-034-A crea una ADR aprobada para mantener `connector write` bloqueado, un schema `ConnectorWriteDecision`, un checklist versionado y un quality gate determinístico. Esta versión no habilita escritura de conectores, no agrega credenciales reales, no requiere red ni APIs externas y conserva el alcance `production-ready-local`.

Evolución pendiente: POST-H-034-B a POST-H-034-E deben completar las ADRs de plugin execution, remote execution, multiuser/auth y enterprise/SaaS. El cierre del backlog solo procede cuando existan las cinco ADRs, decision matrix, quality gates y no-go gates sincronizados.


### POST-H-034-C — Remote execution ADR-3 implementado inicial

Estado: `implemented-initial`.

Artefactos agregados:

- ADR `docs/adr/ADR-POSTH-034-C-remote-execution-adr3.md`.
- Schema `RemoteExecutionAdr3Decision`.
- Checklist `.devpilot/sensitive_capabilities/remote_execution_adr3_checklist.json`.
- Manifest `docs/post_h_034_c_manifest.json`.
- Reporte `docs/audits/post_h_034_c_remote_execution_adr3_report.md`.
- Tests `tests/test_post_h_034_remote_execution_adr3.py`.

La decisión es `continue-blocked`. Este avance no habilita remote execution, remote runner runtime, transporte activo, red, shell, external APIs, credenciales ni workers remotos. Secure transport sigue `design-only` y remote runner sigue disabled. Una evolución posterior requiere backlog separado, threat model, secure transport implementado, sandbox remoto, Approval/RBAC, kill-switch, rollback y quality gate propio.
