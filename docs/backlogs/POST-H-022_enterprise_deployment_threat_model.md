---

doc_id: "POST-H-022-BACKLOG"
id: "POST-H-022"
title: "POST-H-022 — Enterprise deployment threat model"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P3"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
implementation_status: "active"
current_micro_sprint: "POST-H-022-C"
next_micro_sprint: "POST-H-022-D"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-022 — Enterprise deployment threat model

## 0. Estado de implementación

POST-H-022 queda activo con **POST-H-022-C — Enterprise control matrix** como `implemented-initial / design-only`.

POST-H-022-A entrega:

```text
docs/schemas/enterprise_threat_model.schema.json
.devpilot/enterprise/enterprise_threat_model.json
docs/03_security/enterprise_deployment_threat_model.md
tests/test_post_h_022_enterprise_threat_model.py
docs/audits/post_h_022_a_enterprise_asset_inventory_report.md
docs/post_h_022_a_manifest.json
```

El siguiente micro-sprint es **POST-H-022-D — Validator/report read-only**.

POST-H-022-B entrega un catalogo de amenazas STRIDE/LINDDUN por boundary, controles requeridos y riesgos residuales en `.devpilot/enterprise/enterprise_threat_model.json`, sin habilitar despliegue enterprise, control plane, red, ejecucion remota, secretos productivos ni claims de compliance.

POST-H-022-C entrega una matriz enterprise de controles requerida antes de cualquier despliegue enterprise. La matriz distingue `implemented`, `partial` y `required-not-implemented`; los controles no implementados bloquean readiness y no autorizan claims enterprise-ready.


POST-H-022-A no habilita deployment enterprise real, control plane, multiusuario productivo, secure transport activo, remote execution, SSO/SAML/OIDC, red, APIs externas, secrets management productivo ni claims de compliance. La capacidad es preliminar y debe evolucionar antes de cualquier declaracion enterprise.

## 1. Objetivo

Diseñar un **threat model de despliegue enterprise** para DevPilot sin implementar despliegue enterprise, sin control plane remoto, sin multiusuario productivo y sin secure transport activo.

El hito debe definir activos, actores, trust boundaries, amenazas, controles requeridos, riesgos residuales y criterios de bloqueo antes de cualquier evolución hacia operación enterprise.

## 2. Contexto y justificación

DevPilot tiene capacidades locales fuertes, pero enterprise deployment es un dominio de alto riesgo: multiusuario, red, secretos, aislamiento, control de permisos, trazas, retención, compliance y operación remota. La existencia de reportes enterprise experimentales no autoriza claims enterprise ni despliegue productivo.

Este backlog convierte el concepto enterprise en un modelo de amenazas verificable y explícitamente no ejecutable.

## 3. Alcance

Incluye:

```text
- Asset inventory enterprise.
- Actor model: owner, operator, developer, auditor, malicious actor, remote worker futuro.
- Trust boundaries.
- Data flow diagrams textuales/mermaid.
- Threat catalog usando STRIDE/LINDDUN adaptado.
- Control requirements matrix.
- Residual risk register.
- Enterprise deployment go/no-go checklist.
- Tests documentales y schema validation.
```

No incluye:

```text
- Despliegue enterprise real.
- Control plane.
- Multiusuario productivo.
- Auth enterprise real.
- SSO/SAML/OIDC activo.
- Remote workers.
- Secure transport activo.
- Compliance certification.
- SaaS.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/03_security/post_h_security_risk_register.md
docs/02_architecture/post_h_current_architecture_map.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-004-remote-runner-adr2.md
src/devpilot_core/enterprise/
src/devpilot_core/identity/
src/devpilot_core/approval/
src/devpilot_core/policy/
src/devpilot_core/interfaces/api/
ui/web/
.devpilot/compliance/
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
docs/03_security/enterprise_deployment_threat_model.md
docs/schemas/enterprise_threat_model.schema.json
docs/schemas/enterprise_control_matrix.schema.json
.devpilot/enterprise/enterprise_control_matrix.json
src/devpilot_core/enterprise/threat_model.py
src/devpilot_core/enterprise/reports.py
tests/test_post_h_022_enterprise_threat_model.py
docs/05_operations/enterprise_design_runbook.md
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Enterprise threat model

```json
{
  "schema_version": "1.0",
  "status": "design-only",
  "enterprise_deployment_enabled": false,
  "assets": ["workspace", "source_code", "local_store", "reports", "traces", "approvals", "secrets"],
  "actors": ["owner", "local_operator", "developer", "auditor", "malicious_local_user", "future_remote_worker"],
  "trust_boundaries": ["local_machine", "workspace_root", "api_localhost", "future_network_boundary"],
  "threat_categories": ["spoofing", "tampering", "repudiation", "information_disclosure", "denial_of_service", "elevation_of_privilege"],
  "no_go_gates": {
    "enterprise_deployment_enabled": false,
    "remote_execution_enabled": false,
    "secure_transport_implemented": false,
    "compliance_certification_claim": false
  }
}
```

### 6.2 Enterprise control matrix

```json
{
  "control_id": "ENT-RBAC-001",
  "title": "Strong actor identity before enterprise deployment",
  "risk": "actor spoofing",
  "required_before": ["enterprise_deployment", "remote_runner"],
  "status": "required-not-implemented",
  "evidence_required": ["identity registry", "approval binding", "audit logs", "test contracts"]
}
```

## 7. Principios de diseño

```text
1. Enterprise report is not enterprise readiness.
2. Threat model before deployment design.
3. Local-first remains default.
4. Enterprise requires identity, RBAC, approvals, audit, retention and transport maturity.
5. No compliance certification claims.
6. No multiuser production mode in POST-H-022.
7. No secrets should be introduced.
8. Every future enterprise boundary must be mapped to controls and tests.
9. The result is a design artifact and a quality gate input.
10. Residual risks must be explicit.
```

## 8. Micro-sprints propuestos

### POST-H-022-A — Asset inventory y trust boundaries

Tareas:

```text
1. Inventariar activos enterprise futuros.
2. Identificar actores internos y externos.
3. Definir trust boundaries actuales y futuros.
4. Crear enterprise_threat_model.schema.json.
5. Crear primera versión del documento threat model.
```

Criterios PASS:

```text
- Activos, actores y boundaries están enumerados.
- enterprise_deployment_enabled=false.
```

Criterios BLOCK:

```text
- Se propone deployment enterprise real.
- Se omiten secretos/trazas/approvals como activos.
```

### POST-H-022-B — Threat catalog STRIDE/LINDDUN adaptado

Tareas:

```text
1. Crear catálogo de amenazas por boundary.
2. Mapear amenazas a controles requeridos.
3. Identificar riesgos residuales.
4. Separar riesgos actuales vs futuros.
```

Criterios PASS:

```text
- Cada trust boundary tiene amenazas asociadas.
- Cada amenaza crítica tiene control requerido.
```

Criterios BLOCK:

```text
- Amenazas de spoofing/elevation/secrets sin mitigación.
```

### POST-H-022-C — Enterprise control matrix

Tareas:

```text
1. Crear enterprise_control_matrix.schema.json.
2. Crear .devpilot/enterprise/enterprise_control_matrix.json.
3. Definir controles requeridos antes de enterprise.
4. Marcar controles no implementados como required-not-implemented.
```

Criterios PASS:

```text
- La matriz distingue implemented, partial, required-not-implemented.
- No hay claim enterprise-ready.
```

### POST-H-022-D — Validator/report read-only

Tareas:

```text
1. Crear src/devpilot_core/enterprise/threat_model.py.
2. Crear report enterprise threat model read-only.
3. Integrar con quality gate como diseño.
4. Añadir test contract.
```

Criterios PASS:

```text
- El validator reporta design-only.
- No se habilita enterprise deployment.
```

### POST-H-022-E — Runbook y cierre

Tareas:

```text
1. Crear enterprise_design_runbook.md.
2. Documentar go/no-go enterprise.
3. Actualizar docs de arquitectura si aplica.
4. Ejecutar validación focal.
```

## 9. Comandos de validación esperados

```powershell
python -m pytest tests/test_post_h_022_enterprise_threat_model.py -q
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate-artifact docs/03_security/enterprise_deployment_threat_model.md --json
```

## 10. No-go gates

```text
- enterprise_deployment_enabled=true
- remote_execution_enabled=true
- secure_transport_implemented=true en este hito
- compliance_certification_claim=true
- secrets introduced
- network dependency introduced
```

## 11. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Sobreclaiming enterprise | Alto | Disclaimers y gate design-only. |
| Amenazas incompletas | Alto | STRIDE/LINDDUN y matriz de controles. |
| Mezclar enterprise con remote execution | Crítico | Remote sigue bloqueado. |
| Compliance implícito | Alto | No certification claim. |

## 12. Definition of Done

```text
[ ] Threat model enterprise documentado.
[ ] Control matrix creada y validada.
[ ] Validator/report read-only implementado.
[ ] Quality gate mantiene enterprise design-only.
[ ] Tests pasan.
[ ] No hay deployment enterprise real.
```
