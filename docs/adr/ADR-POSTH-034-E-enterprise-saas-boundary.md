---
doc_id: "ADR-POSTH-034-E"
title: "ADR POST-H-034-E — Enterprise/SaaS boundary"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-12"
approval: "approved_by_owner"
phase: "POST-FASE-H"
created_by: "POST-H-034-E"
capability_id: "enterprise.saas"
decision_state: "continue-blocked"
decision_status: "continue-blocked"
enterprise_ready_claimed: false
enterprise_ready_enabled: false
enterprise_runtime_enabled: false
saas_ready_claimed: false
saas_runtime_enabled: false
control_plane_enabled: false
cloud_deployment_enabled: false
tenancy_enabled: false
tenant_isolation_implemented: false
public_api_enabled: false
compliance_certified: false
compliance_certification_claim: false
external_audit_claimed: false
legal_advice_claimed: false
network_allowed: false
external_api_allowed: false
credentials_required: false
production_ready_local_scope_preserved: true
enterprise_threat_model_design_only: true
compliance_mapping_non_certifying: true
requires_future_enablement_adr: true
requires_future_backlog: true
preliminary: true
---

# ADR POST-H-034-E — Enterprise/SaaS boundary

## Estado

Aprobada como `implemented-initial / continue-blocked`.

## Contexto

DevPilot Local contiene artefactos preparatorios para enterprise y compliance: threat model enterprise design-only, control matrix, compliance mappings no certificantes, declaration gate `production-ready-local`, API local hardened y RBAC/approval inicial. Ninguno de esos artefactos equivale a SaaS, enterprise-ready, certificacion compliance, control plane, tenancy, API publica o despliegue cloud.

## Decisión

`enterprise.saas` permanece `continue-blocked`.

POST-H-034-E no habilita runtime, producto, despliegue ni claim enterprise/SaaS. La decision formal es preservar `production-ready-local` como alcance vigente y bloquear cualquier interpretacion expansiva hasta que exista backlog futuro, threat model actualizado, arquitectura enterprise/SaaS, pruebas, approvals, legal/compliance scope y evidencia regenerable.

## Reglas de interpretación obligatorias

```text
enterprise threat model exists != enterprise-ready
enterprise control matrix exists != production enterprise authorization
compliance mapping exists != compliance-certified
production-ready-local exists != SaaS-ready
local API hardening exists != public API or cloud control plane
POST-H-034-E ADR exists != runtime enablement
```

## No habilitado

```text
enterprise_ready_claimed=false
enterprise_ready_enabled=false
enterprise_runtime_enabled=false
saas_ready_claimed=false
saas_runtime_enabled=false
control_plane_enabled=false
cloud_deployment_enabled=false
tenancy_enabled=false
tenant_isolation_implemented=false
public_api_enabled=false
compliance_certified=false
compliance_certification_claim=false
external_audit_claimed=false
legal_advice_claimed=false
network_allowed=false
external_api_allowed=false
credentials_required=false
```

## Alternativas evaluadas

### `continue-blocked` — aceptada

Es la unica decision compatible con el estado actual: DevPilot es local-first y `production-ready-local`, pero no enterprise-ready, no SaaS-ready y no compliance-certified.

### `design-only` — aceptable como descripcion secundaria

Los artefactos enterprise y compliance existentes siguen siendo design-only/no-certifying evidence, pero el estado de capacidad sensible se expresa como `continue-blocked` para evitar claims.

### `pilot-gated-future` — pospuesta

Un piloto futuro exige backlog separado y controles previos: arquitectura cloud/control plane, tenancy, multiuser auth productivo, data privacy, backup/restore, observability backend, incident response, support/SLA, legal/compliance scope y security tests.

### `enable-now` — rechazada

Habilitar enterprise/SaaS ahora violaria los no-go gates y confundiria evidencia local con producto enterprise/cloud.

## Prerrequisitos para un backlog futuro

- Arquitectura enterprise/SaaS y deployment model.
- Control plane seguro y no habilitado por defecto.
- Multiuser auth productivo y session management.
- Tenant isolation y data segregation.
- Data retention/privacy policy.
- Backup/restore y disaster recovery.
- Observability backend con privacidad y retencion.
- Incident response y support/SLO/SLA model.
- Legal/compliance scope.
- External audit plan si se pretende certificacion.
- Security tests, threat model actualizado y migration plan desde local-first.

## Consecuencias

- DevPilot conserva alcance `production-ready-local`.
- Compliance mapping sigue siendo evidencia interna de ingenieria, no auditoria externa ni certificacion.
- Enterprise threat model sigue design-only.
- Los claims enterprise/SaaS/compliance quedan bloqueados por checklist, schema, project_state, matrix, validator y tests.

## Criterios de salida

Esta ADR puede revisarse solo mediante un nuevo backlog de implementacion sensible. Ese backlog debe preservar dry-run por defecto, aprobacion humana, RBAC, observabilidad, rollback, no-go gates y pruebas negativas de overclaim.
