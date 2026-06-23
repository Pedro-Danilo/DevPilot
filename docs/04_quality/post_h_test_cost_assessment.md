---
id: POST-H-EVAL-001-E
title: Evaluación de testing, costos y contratos
status: implemented
micro_sprint: POST-H-EVAL-001-E
phase: POST-FASE-H
source_micro_sprints:
  - POST-H-EVAL-001-A
  - POST-H-EVAL-001-B
  - POST-H-EVAL-001-C
  - POST-H-EVAL-001-D
local_first: true
dry_run: true
no_runtime_features_added: true
no_remote_execution_enabled: true
no_write_connectors_enabled: true
external_api_used: false
---

# Evaluación de testing y costos post-H

## 1. Resumen ejecutivo

DevPilot tiene una base de pruebas amplia y útil para preservar la historia funcional del proyecto, pero el análisis post-H muestra que **cantidad de tests no equivale automáticamente a cobertura industrial**. El repositorio contiene **187 archivos `test_*.py`**, aproximadamente **17801 líneas de tests** y **893 casos recolectables por pytest** en el snapshot analizado. Además, el Test Contract Registry v1 declara **84 contratos**, de los cuales **78** son contratos históricos/documentales.

La conclusión principal es que DevPilot necesita evolucionar hacia un **Test Contract Registry 2.0** que clasifique pruebas por dominio, criticidad, riesgo, costo, trigger de ejecución e impacto. El registry actual es suficiente como baseline `implemented-initial`, pero todavía no es suficiente como mecanismo industrial de selección de regresión por impacto.

Este micro-sprint no agrega funcionalidades runtime. Su propósito es crear una evaluación técnica accionable para que `POST-H-002` y los sprints posteriores puedan tomar decisiones de madurez sin sobredeclarar cobertura.

## 2. Inventario de tests

| Métrica | Valor |
|---|---:|
| Archivos `tests/test_*.py` | 187 |
| Líneas aproximadas de tests | 17801 |
| Archivos recolectados por `pytest --collect-only` | 188 |
| Casos recolectables por pytest | 893 |
| Tests históricos/documentales `test_sprint_*_documentation.py` | 79 |
| Tests POST-H-EVAL-001 | 4 |
| Contratos registrados en v1 | 84 |
| Tests únicos referenciados por contratos v1 | 84 |
| Tests no mapeados explícitamente por contratos v1 | 103 |

### Lectura técnica

La suite ya es suficientemente grande para exigir control de costo de regresión. A partir de este tamaño, ejecutar todo en cada cambio puede ser correcto como validación de cierre, pero no es eficiente como estrategia única diaria. El sistema necesita distinguir:

- pruebas que deben correr siempre;
- pruebas por impacto;
- pruebas de release;
- pruebas históricas/documentales;
- pruebas futuras de integración/e2e.

## 3. Test Contract Registry actual

El registry actual está en:

```text
.devpilot/testing/test_contract_registry.json
```

Distribución por scope:

| Scope | Contratos |
|---|---:|
| `feature` | 1 |
| `global-state` | 1 |
| `historical-sprint` | 78 |
| `integration` | 1 |
| `quality-gate` | 2 |
| `ui-smoke` | 1 |

Fortalezas:

1. Centraliza contratos críticos después de `POST-H-001`.
2. Se valida por schema y por `python -m devpilot_core test-contracts validate --json`.
3. Integra el estado global mutable, quality gates, schema registry, UI smoke e histórico de sprints.
4. Sirve como primera fuente para el `test-impact analyzer`.

Limitaciones:

1. Está dominado por contratos históricos: **78 de 84**.
2. No codifica todavía prioridad P0/P1/P2/P3.
3. No expresa costo esperado de ejecución.
4. No expresa dominio funcional fino.
5. No mapea suficientes rutas internas de `src/devpilot_core`.
6. No distingue seguridad crítica de pruebas documentales.
7. No contiene campos como `risk_level`, `execution_tier`, `release_blocking` o `required_for_remote_enablement`.

## 4. Tests históricos vs tests funcionales

Los tests históricos/documentales son valiosos para preservar trazabilidad acumulativa. Sin embargo, no deben confundirse con cobertura industrial de seguridad o runtime.

### Tests históricos/documentales

Incluyen principalmente:

```text
tests/test_sprint_*_documentation.py
```

Función:

- preservar manifests y auditorías por sprint;
- evitar drift documental;
- garantizar continuidad del backlog histórico;
- comprobar que no se rompen contratos de documentación acumulativa.

Riesgo si se sobreinterpretan:

```text
Un PASS documental puede dar falsa sensación de cobertura runtime si no se complementa con pruebas de PolicyEngine, RBAC, approval, guards, agentes, conectores, RAG y API.
```

### Tests funcionales/industriales

Incluyen seguridad, contratos, agents, RAG, connectors, plugins, observability, API/UI, release y quality gates. Estos deben mapearse explícitamente en el registry 2.0.

## 5. Quality gates existentes

El profile `hardening` actual ejecuta 12 subgates y opera como baseline industrial local-first. En el snapshot D validado, `quality-gate hardening` pasó con 12/12 subgates y 0 blockers.

Subgates relevantes:

- readiness-strict;
- standards-status;
- miasi-validate;
- eval-harness-ready;
- app-contract;
- validation-gateway-all;
- visual-product-smoke;
- ci-workflow-static;
- advanced-evals-safety;
- test-contract-registry;
- project-global-state;
- industrial-readiness.

Lectura:

```text
El quality gate funciona como orquestador de señales, pero no reemplaza una estrategia granular de selección de pruebas por impacto.
```

## 6. Impact analyzer actual

El impact analyzer actual es conservador y útil como baseline, pero todavía insuficiente para gobernanza industrial fina.

Prueba representativa:

```powershell
python -m devpilot_core test-impact analyze --path README.md --json
```

Resultado esperado:

```text
Mapea README.md contra project-global-state y recomienda tests/test_project_global_state.py.
```

Prueba crítica:

```powershell
python -m devpilot_core test-impact analyze --path src/devpilot_core/policy/engine.py --json
```

Resultado observado:

```text
No encuentra contrato específico y recomienda pytest -q completo de forma conservadora.
```

Esto es seguro, pero costoso. El registry 2.0 debe mapear rutas internas críticas como:

```text
src/devpilot_core/policy/
src/devpilot_core/approval/
src/devpilot_core/security/
src/devpilot_core/identity/
src/devpilot_core/remote/
src/devpilot_core/connectors/
src/devpilot_core/plugins/
src/devpilot_core/agents/
src/devpilot_core/multiagent/
src/devpilot_core/rag/
src/devpilot_core/interfaces/api/
```

## 7. Costos de regresión

### Niveles propuestos

| Nivel | Uso | Frecuencia recomendada | Costo esperado |
|---|---|---|---|
| Always-fast | P0/P1 rápido: seguridad, estado global, registry, impact, risk/assessment docs | Cada cambio relevante | Bajo |
| Impact | Tests seleccionados por rutas afectadas y contratos v2 | Cada cambio de dominio | Bajo/medio |
| Release | Históricos, quality gates, UI smoke, audit/compliance/release | Antes de merge/release | Medio/alto |
| Full regression | `pytest -q` completo | Cierre de sprint, tag, release candidate | Alto |
| Manual/nightly futuro | E2E, datasets grandes, UI/API real, integración externa controlada | Nocturno o manual | Alto |

### Política recomendada

```text
No ejecutar todo siempre por defecto en el flujo diario.
Sí ejecutar todo al cerrar hitos, generar tags estables o tocar dominios P0 sin mapeo de impacto suficiente.
```

## 8. Brechas de cobertura por dominio

Tests funcionales relevantes no mapeados explícitamente en el registry v1:

- `tests/test_agent_runtime.py`
- `tests/test_agent_runtime_v2.py`
- `tests/test_agent_session.py`
- `tests/test_agentops_gate.py`
- `tests/test_agentops_instrumentation.py`
- `tests/test_api_approvals_actions.py`
- `tests/test_api_security.py`
- `tests/test_approval_cli.py`
- `tests/test_approval_policy_binding.py`
- `tests/test_approval_store.py`
- `tests/test_connector_adapter.py`
- `tests/test_connector_registry.py`
- `tests/test_contract_schemas.py`
- `tests/test_identity_rbac.py`
- `tests/test_industrial_readiness.py`
- `tests/test_multiagent_coordinator.py`
- `tests/test_multiagent_workflow.py`
- `tests/test_phase_h_backlog_approval.py`
- `tests/test_plugin_registry.py`
- `tests/test_policy_engine.py`
- `tests/test_provider_config_schema.py`
- `tests/test_rag_local.py`
- `tests/test_refactor_testplanner_agents.py`
- `tests/test_release_agent.py`
- `tests/test_repo_analysis_agent.py`
- `tests/test_repo_quality_gate.py`
- `tests/test_review_agents.py`
- `tests/test_schema_validator.py`
- `tests/test_sdlc_agents.py`
- `tests/test_secret_guard_hardening.py`

Ejemplos generales de tests no mapeados:

- `tests/test_advanced_evals.py`
- `tests/test_agent_runtime.py`
- `tests/test_agent_runtime_v2.py`
- `tests/test_agent_session.py`
- `tests/test_agentops_gate.py`
- `tests/test_agentops_instrumentation.py`
- `tests/test_api_approvals_actions.py`
- `tests/test_api_contract.py`
- `tests/test_api_local.py`
- `tests/test_api_reports_traces.py`
- `tests/test_api_security.py`
- `tests/test_api_settings.py`
- `tests/test_application_services.py`
- `tests/test_application_services_v2.py`
- `tests/test_approval_cli.py`
- `tests/test_approval_policy_binding.py`
- `tests/test_approval_store.py`
- `tests/test_architecture_drift.py`
- `tests/test_architecture_drift_repo.py`
- `tests/test_artifact_profile_registry.py`
- `tests/test_artifact_validator.py`
- `tests/test_audit_pack.py`
- `tests/test_backup_upgrade.py`
- `tests/test_bootstrap.py`
- `tests/test_ci_workflow_scaffolding.py`
- `tests/test_cli_core.py`
- `tests/test_compliance_packs.py`
- `tests/test_connector_adapter.py`
- `tests/test_connector_registry.py`
- `tests/test_contract_schemas.py`
- `tests/test_dependency_graph.py`
- `tests/test_enterprise_reporting.py`
- `tests/test_eval_runner.py`
- `tests/test_event_logger.py`
- `tests/test_frontmatter_validator.py`

La brecha no significa que esos tests no existan. Significa que el registry v1 no sabe usarlos todavía para selección inteligente por impacto.

## 9. Propuesta Test Contract Registry 2.0

Propuesta de campos adicionales:

```json
{
  "contract_id": "policy-engine-guards",
  "schema_version": "2.0",
  "domain": "security-policy",
  "priority": "P0",
  "risk_level": "critical",
  "execution_tier": "always",
  "estimated_cost": "low",
  "security_critical": true,
  "release_blocking": true,
  "required_for_remote_enablement": true,
  "test_files": ["tests/test_policy_engine.py"],
  "watched_paths": ["src/devpilot_core/policy/"],
  "change_triggers": ["source", "policy_matrix", "tool_registry"],
  "coverage_intent": "deny-by-default, guard composition, local/no-cost behavior",
  "owner_role": "security-maintainer"
}
```

### Campos requeridos

| Campo | Propósito |
|---|---|
| `domain` | Agrupar por arquitectura/capacidad. |
| `priority` | P0/P1/P2/P3. |
| `risk_level` | critical/high/medium/low. |
| `execution_tier` | always/impact/release/manual_or_nightly. |
| `estimated_cost` | low/medium/high. |
| `security_critical` | Bloquea release si falla. |
| `release_blocking` | Define obligatoriedad antes de tag/release. |
| `required_for_remote_enablement` | Exige cobertura antes de activar capacidades riesgosas. |
| `change_triggers` | source/docs/schema/config/runtime-policy. |
| `coverage_intent` | Qué riesgo cubre realmente. |

## 10. Matriz P0/P1/P2/P3

| Prioridad | Archivos detectados | Definición |
|---|---:|---|
| P0 | 13 | Seguridad, PolicyEngine, Approval, RBAC, guards y remote disabled |
| P1 | 14 | Schemas, manifests, project state, quality gates y test contracts |
| P2 | 63 | Agents, RAG, connectors, plugins, multiworkspace y workflows |
| P3 | 97 | UI smoke, docs, reports, release artifacts y producto visual |

### P0 — Seguridad y permisos

Debe incluir como mínimo:

```text
PolicyEngine
ApprovalPolicyChecker
RBAC / Identity
PathGuard
SecretGuard
PromptInjectionGuard
ToolInjectionGuard
remote disabled
connector write denied
plugin execution denied
```

### P1 — Contratos de consistencia

Debe incluir:

```text
Schemas
Manifests
Project state
Quality gates
Test contract registry
Industrial readiness
Post-H assessment artifacts
```

### P2 — Capacidades funcionales

Debe incluir:

```text
Agents
RAG
Connectors
Plugins
Multiworkspace
Workflows
Observability
API local
```

### P3 — Producto, documentación y release

Debe incluir:

```text
UI smoke
Históricos documentales
Reports
Release artifacts
Audit/compliance packs
```

## 11. Roadmap de testing

### POST-H-003 — Test Contract Registry 2.0

Objetivo:

```text
Evolucionar .devpilot/testing/test_contract_registry.json o crear registry v2 compatible, sin romper POST-H-001.
```

Entregables esperados:

```text
docs/schemas/test_contract_registry_v2.schema.json
.devpilot/testing/test_contract_registry_v2.json
src/devpilot_core/testing/contracts_v2.py
tests/test_test_contract_registry_v2.py
```

### POST-H-004 — Impact analyzer por dominio

Objetivo:

```text
Mapear paths a dominios P0/P1/P2/P3 y recomendar suites por impacto.
```

### POST-H-005 — Regression profiles

Objetivo:

```text
Crear perfiles explícitos: always-fast, impact, release, full.
```

### POST-H-006 — Coverage intent y risk-based testing

Objetivo:

```text
Asociar cada test crítico a un riesgo operativo o de seguridad.
```

## 12. Criterios de cierre

### PASS

```text
PASS si se propone Test Contract Registry 2.0.
PASS si se clasifican pruebas por criticidad.
PASS si se evalúa costo de pytest completo.
PASS si se identifican gaps del impact analyzer.
PASS si se recomienda roadmap de testing.
```

### BLOCK evitados

```text
No se asume que muchos tests equivalen automáticamente a cobertura industrial.
No se mezclan tests históricos con tests críticos.
No se omite costo de ejecución.
No se habilita remote execution.
No se habilitan conectores write.
No se modifica código runtime.
```

## 13. Respuestas a preguntas obligatorias

### ¿Qué pruebas son críticas para no romper seguridad?

PolicyEngine, Approval, RBAC/Identity, PathGuard, SecretGuard, PromptInjectionGuard, ToolInjectionGuard, remote disabled, connector write denied y plugin execution denied.

### ¿Qué pruebas son históricas y documentales?

Las pruebas `tests/test_sprint_*_documentation.py`, pruebas de manifests funcionales y pruebas de auditorías documentales.

### ¿Qué pruebas son de producto?

UI web, API local, visual smoke, report/trace viewer, approval center, settings UI, release dry-run y audit packs exportables.

### ¿Qué pruebas pueden correr siempre?

P0/P1 rápidas: project state, test contract registry, impact analyzer, post-H eval artifact tests, hardening gate, industrial readiness y pruebas de seguridad-deny.

### ¿Qué pruebas deben correr por impacto?

Las mapeadas por paths en Test Contract Registry 2.0, por ejemplo cambios en `src/devpilot_core/policy/` deben disparar pruebas de PolicyEngine, MIASI, approval y guards, no necesariamente todo pytest.

### ¿Qué pruebas deben ejecutarse solo antes de release?

Full pytest, sweep histórico documental, UI smoke, audit/compliance-pack integrity, release dry-run, advanced evals y futuras pruebas e2e.

### ¿Qué dominios no están bien mapeados por impact analyzer?

PolicyEngine internals, approval/RBAC, API security, agent runtime, RAG, connectors, plugins, multiworkspace, observability y release.

## 14. Decisiones del micro-sprint E

```text
DEC-E-001 — No asumir que cantidad alta de tests equivale a cobertura industrial.
DEC-E-002 — Promover Test Contract Registry 2.0 antes de depender del impact analyzer para cambios de dominio crítico.
DEC-E-003 — Separar ejecución always, impact, release y manual/nightly.
DEC-E-004 — P0 debe priorizar seguridad, guards, RBAC, approval, remote disabled y writes denegados.
DEC-E-005 — POST-H-002 debe consumir métricas de testing/costo como parte del dashboard de madurez.
```
