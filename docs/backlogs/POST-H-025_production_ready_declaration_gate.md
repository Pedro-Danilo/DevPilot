---

doc_id: "POST-H-025-BACKLOG"
id: "POST-H-025"
title: "POST-H-025 — DevPilot Local production-ready declaration gate"
status: "draft"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-23"
approval: "pending_owner_review"
phase: "POST-FASE-H"
priority: "P0"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-025 — DevPilot Local production-ready declaration gate

## 1. Objetivo

Implementar un **gate final de declaración production-ready-local** para DevPilot Local. El gate debe consolidar evidencias de todos los hitos post-H relevantes y producir una de dos decisiones:

```text
production-ready-local: aprobado con evidencia
BLOCK: no aprobado, con gaps y acciones pendientes
```

Este backlog no declara DevPilot enterprise-ready, remote-ready, compliance-certified ni SaaS-ready. Su alcance es únicamente `production-ready-local`.

## 2. Contexto y justificación

El roadmap 1.1.0 incorporó explícitamente la necesidad de que la declaración productiva local no sea una afirmación documental, sino un gate basado en evidencia. Antes de este hito deben existir madurez, test contracts v2, Policy/MIASI semantic validator, architecture map executable, CLI registry, ApplicationService hardening, runtime lifecycle, documentation governance, observability retention, RAG groundedness, Approval/RBAC hardening, UI/API shell, operator dashboard, release reproducibility y onboarding bootstrap.

POST-H-025 es el cierre de ruta: no agrega features sensibles; evalúa si el conjunto alcanza o no la madurez local productiva.

## 3. Alcance

Incluye:

```text
- Production-ready-local criteria schema.
- Evidence aggregator local read-only.
- Declaration gate CLI.
- Reporte de decisión PASS/BLOCK.
- Matriz de gaps residuales.
- No-go gates consolidados.
- Checklist de release local productivo.
- Actualización de manifest/changelog/runbook.
```

No incluye:

```text
- Declarar enterprise-ready.
- Declarar compliance-certified.
- Habilitar remote execution.
- Habilitar connector write.
- Habilitar plugin execution.
- Habilitar APIs externas por defecto.
- Publicar paquetes o desplegar servicios reales.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
outputs/reports/maturity_dashboard*.json
.devpilot/testing/test_contract_registry.json
.devpilot/testing/test_contract_registry_v2.json
.devpilot/policy/miasi_semantic_report.json
.devpilot/architecture/architecture_map.json
.devpilot/runtime/runtime_state_policy.json
.devpilot/docs/documentation_source_registry.json
.devpilot/observability/observability_retention_policy.json
.devpilot/rag/rag_groundedness_report.json
.devpilot/approval/sensitive_action_catalog.json
outputs/reports/ui_api_contract_report.json
outputs/reports/operator_dashboard_snapshot.json
outputs/reports/release_reproducibility_pack.json
outputs/reports/onboarding_bootstrap_report.json
docs/05_operations/runbook.md
docs/release/CHANGELOG.md
```

## 5. Entregables

```text
docs/schemas/production_ready_local_criteria.schema.json
docs/schemas/production_ready_local_report.schema.json
.devpilot/production/production_ready_local_criteria.json
src/devpilot_core/industrial/production_ready.py
src/devpilot_core/industrial/production_ready_reports.py
tests/test_post_h_025_production_ready_criteria.py
tests/test_post_h_025_production_ready_gate.py
docs/audits/devpilot_local_production_ready_declaration.md
outputs/reports/production_ready_local_report.json
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/cli.py o command registry
src/devpilot_core/application/services.py
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
docs/release/CHANGELOG.md
docs/05_operations/runbook.md
```

## 6. Modelo de datos mínimo

### 6.1 Production-ready-local criteria

```json
{
  "schema_version": "1.0",
  "scope": "production-ready-local",
  "required_hitos": [
    "POST-H-002", "POST-H-003", "POST-H-004", "POST-H-005",
    "POST-H-006", "POST-H-007", "POST-H-008", "POST-H-009",
    "POST-H-010", "POST-H-011", "POST-H-012", "POST-H-013",
    "POST-H-014", "POST-H-015", "POST-H-016", "POST-H-017",
    "POST-H-024"
  ],
  "optional_design_hitos": ["POST-H-018", "POST-H-019", "POST-H-020", "POST-H-021", "POST-H-022", "POST-H-023"],
  "minimum_score": 90,
  "blocking_gaps_allowed": 0,
  "no_go_gates": {
    "remote_execution_enabled": false,
    "connector_write_enabled": false,
    "plugin_execution_enabled": false,
    "external_apis_required": false,
    "compliance_certification_claim": false,
    "enterprise_ready_claim": false
  }
}
```

### 6.2 Production-ready-local report

```json
{
  "schema_version": "1.0",
  "decision": "BLOCK",
  "score": 87.5,
  "scope": "production-ready-local",
  "blocking_gaps_total": 2,
  "passed_hitos_total": 15,
  "required_hitos_total": 17,
  "no_go_gates_passed": true,
  "claims": {
    "production_ready_local": false,
    "enterprise_ready": false,
    "remote_ready": false,
    "compliance_certified": false
  }
}
```

## 7. Principios de diseño

```text
1. Evidence before declaration.
2. BLOCK is an acceptable result.
3. production-ready-local is not enterprise-ready.
4. production-ready-local is not compliance-certified.
5. production-ready-local does not enable remote execution.
6. No critical no-go gate may be bypassed.
7. Every required hito must provide machine-readable evidence.
8. Reports must distinguish missing, partial, failed and passed evidence.
9. Declaration must be reproducible locally.
10. The result must be auditable and versioned.
```

## 8. Micro-sprints propuestos

### POST-H-025-A — Criteria schema y evidence map

Objetivo: definir los criterios formales de declaración.

Tareas:

```text
1. Crear production_ready_local_criteria.schema.json.
2. Crear production_ready_local_report.schema.json.
3. Crear criteria JSON bajo .devpilot/production/.
4. Mapear cada hito requerido a evidencia esperada.
5. Clasificar evidencia: required, optional, blocker, advisory.
```

Criterios PASS:

```text
- Criteria valida contra schema.
- Cada hito requerido tiene evidencia mapeada.
- No-go gates están presentes.
```

Criterios BLOCK:

```text
- Se omiten remote/plugin/connector no-go gates.
- Se permite claim enterprise/compliance.
```

### POST-H-025-B — Evidence aggregator read-only

Objetivo: implementar agregador local de evidencias.

Tareas:

```text
1. Crear src/devpilot_core/industrial/production_ready.py.
2. Leer artefactos de madurez, testing, policy, architecture, docs, observability, RAG, approvals, UI/API, release y onboarding.
3. Clasificar faltantes y gaps.
4. No mutar archivos.
5. Producir modelo intermedio de evidencia.
```

Criterios PASS:

```text
- El agregador funciona con fuentes faltantes marcadas como gaps.
- No modifica archivos.
- No requiere red.
```

### POST-H-025-C — Declaration gate CLI/API

Objetivo: exponer el gate de declaración.

Tareas:

```text
1. Crear comando industrial-readiness production-ready-local o production-ready check.
2. Integrar con ApplicationService.
3. Generar report JSON/Markdown.
4. Devolver exit_code BLOCK si hay gaps críticos.
```

Criterios PASS:

```text
- El gate produce PASS o BLOCK determinístico.
- BLOCK incluye acciones concretas.
- PASS solo ocurre si no hay blockers.
```

### POST-H-025-D — No-go gates y claims validator

Objetivo: impedir declaraciones indebidas.

Tareas:

```text
1. Validar claims en README, runbook, changelog y report.
2. Bloquear enterprise-ready/compliance-certified/remote-ready no sustentados.
3. Validar que remote/connector-write/plugin-execution siguen deshabilitados.
4. Integrar con quality-gate hardening.
```

Criterios BLOCK:

```text
- Algún documento declara enterprise-ready.
- Algún documento declara compliance-certified.
- Remote execution aparece habilitado.
```

### POST-H-025-E — Declaración final o BLOCK report

Objetivo: emitir el artefacto final de cierre.

Tareas:

```text
1. Crear docs/audits/devpilot_local_production_ready_declaration.md.
2. Incluir decisión, evidencia y límites.
3. Generar production_ready_local_report.json.
4. Actualizar changelog/runbook si procede.
5. Ejecutar regresión focal y quality gate.
```

Criterios PASS:

```text
- La declaración es reproducible.
- Si PASS, el alcance dice production-ready-local solamente.
- Si BLOCK, el reporte lista gaps y próximos pasos.
```

## 9. Comandos de validación esperados

```powershell
python -m pytest tests/test_post_h_025_production_ready_criteria.py tests/test_post_h_025_production_ready_gate.py -q
python -m devpilot_core industrial-readiness check --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core validate-artifact docs/audits/devpilot_local_production_ready_declaration.md --json
```

## 10. No-go gates

```text
- blocking_gaps_total > 0 para PASS
- remote_execution_enabled=true
- connector_write_enabled=true
- plugin_execution_enabled=true
- external_apis_required=true
- compliance_certification_claim=true
- enterprise_ready_claim=true
- missing evidence for required hito
- stale or failed quality gate
```

## 11. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Declaración prematura | Crítico | Gate con BLOCK por defecto si falta evidencia. |
| Confundir local production-ready con enterprise | Alto | Claims validator. |
| Omisión de evidencias | Alto | Evidence map obligatorio. |
| Quality gate desactualizado | Alto | Validar freshness/timestamps. |
| Sobreconfianza en documentación | Medio-alto | Requerir machine-readable evidence. |

## 12. Definition of Done

```text
[ ] Criteria y report schemas creados.
[ ] Criteria JSON creado.
[ ] Evidence aggregator implementado.
[ ] Gate CLI/API implementado.
[ ] Claims validator implementado.
[ ] Report PASS/BLOCK generado.
[ ] Tests focales pasan.
[ ] No se declaran enterprise/compliance/remote capabilities.
[ ] production-ready-local solo se declara si no hay blockers.
```
