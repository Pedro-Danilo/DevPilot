---

doc_id: "POST-H-018-IMPLEMENTATION"
id: "POST-H-018"
title: "POST-H-018 — Connector sandbox avanzado"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-30"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P2"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "active"
current_micro_sprint: "POST-H-018-B"
next_micro_sprint: "POST-H-018-C"
---

# POST-H-018 — Connector sandbox avanzado


## 0. Estado de implementación

Estado del backlog: `approved / active`.

Micro-sprint actual: `POST-H-018-B — Sandbox runner read-only/dry-run`.

Resultado POST-H-018-A: `implemented-initial`. Se aprueba el backlog para implementación y se agregan schemas/policy de sandbox de conectores con deny-write por defecto.

Resultado POST-H-018-B: `implemented-initial`. Se agrega `ConnectorSandboxRunner` y CLI `connector sandbox run` para validar/dry-run/replay local simulado, invocando PolicyEngine antes de cualquier operación simulada y generando `ConnectorSandboxReport` schema-compatible.

Pendiente: replay real con fixtures/redacción, binding Policy/Approval/RBAC fuerte y quality gate final quedan para POST-H-018-C/D/E.

Límites explícitos: no se habilita `connector write`, no se realizan llamadas de red, no se llaman APIs externas, no se almacenan tokens, no se mutan sistemas externos, no se ejecutan plugins y no se ejecutan conectores reales.

## 1. Objetivo

Diseñar e implementar una capa de **sandbox avanzado para conectores** que permita validar, simular, reproducir y auditar llamadas a conectores locales/read-only antes de considerar cualquier evolución futura hacia conectores con efectos laterales.

El objetivo no es habilitar `connector write`. El objetivo es elevar la madurez del ecosistema de conectores desde `implemented-initial/read-only` hacia una base industrial local en la que cada conector tenga contrato, permisos, fixtures de replay, policy binding, trazabilidad, clasificación de riesgo y gates explícitos.

## 2. Contexto y justificación

El diagnóstico post-H clasificó conectores/MCP como capacidad existente pero inicial. El riesgo identificado es que un registry o adapter pueda interpretarse erróneamente como autorización para mutar sistemas externos. El roadmap mantiene `connector write` bloqueado por defecto y lo condiciona a ADR, sandbox, replay tests, approvals, RBAC, observabilidad y no-go gates.

Actualmente DevPilot dispone de una base en:

```text
src/devpilot_core/connectors/
.devpilot/connectors/
docs/schemas/connector_registry.schema.json
src/devpilot_core/policy/
src/devpilot_core/approval/
src/devpilot_core/identity/
src/devpilot_core/observability/
evals/fixtures/
```

Esta base permite validar y modelar conectores, pero falta una capa más explícita de sandbox/replay que impida confundir conectores read-only con conectores ejecutables de escritura.

## 3. Alcance

Incluye:

```text
- Connector sandbox policy local.
- Connector capability registry enriquecido.
- Clasificación de conectores por side_effect, risk_level, permissions y data_sensitivity.
- Replay fixtures para llamadas read-only.
- Simulación determinística de llamadas sin red.
- Reportes de sandbox por conector.
- Integración con PolicyEngine, Approval y RBAC.
- Test contracts para conectores críticos.
- Quality gate que bloquee connector write no autorizado.
- Runbook de operación segura de conectores.
```

No incluye:

```text
- Connector write real.
- Llamadas a APIs externas reales.
- OAuth real.
- Persistencia de tokens reales.
- Mutación de sistemas externos.
- Webhooks entrantes productivos.
- Sincronización bidireccional.
- Background workers remotos.
- Remote execution.
- Plugins ejecutables.
```

## 4. Fuentes de entrada obligatorias

```text
docs/backlogs/post_h_prioritized_roadmap.md
docs/03_security/post_h_security_risk_register.md
docs/02_architecture/post_h_current_architecture_map.md
docs/05_operations/runbook.md
.devpilot/connectors/connector_registry.json
docs/schemas/connector_registry.schema.json
src/devpilot_core/connectors/
src/devpilot_core/policy/
src/devpilot_core/approval/
src/devpilot_core/identity/
src/devpilot_core/observability/
.devpilot/testing/test_contract_registry.json
evals/fixtures/
```

## 5. Entregables

```text
docs/schemas/connector_sandbox_policy.schema.json
docs/schemas/connector_replay_fixture.schema.json
docs/schemas/connector_sandbox_report.schema.json
.devpilot/connectors/connector_sandbox_policy.json
evals/fixtures/connector_replay_cases.json
src/devpilot_core/connectors/sandbox.py
src/devpilot_core/connectors/replay.py
src/devpilot_core/connectors/sandbox_reports.py
tests/test_post_h_018_connector_sandbox_policy.py
tests/test_post_h_018_connector_replay.py
tests/test_post_h_018_connector_sandbox_gate.py
docs/05_operations/connector_sandbox_runbook.md
docs/03_security/connector_sandbox_threat_model.md
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/connectors/registry.py
src/devpilot_core/policy/engine.py
src/devpilot_core/quality/gate.py
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

### 6.1 Connector sandbox policy

```json
{
  "schema_version": "1.0",
  "default_mode": "deny-write",
  "network_allowed_by_default": false,
  "external_api_allowed_by_default": false,
  "mutation_allowed_by_default": false,
  "replay_required": true,
  "approval_required_for_side_effects": true,
  "connectors": [
    {
      "connector_id": "local.filesystem.readonly",
      "status": "implemented-initial",
      "allowed_modes": ["validate", "dry-run", "replay"],
      "side_effect": "read",
      "risk_level": "medium",
      "data_sensitivity": "workspace-metadata",
      "network_allowed": false,
      "external_api_allowed": false,
      "mutations_allowed": false,
      "approval_required": false,
      "policy_rules": ["connector.readonly.local"]
    }
  ]
}
```

### 6.2 Connector replay fixture

```json
{
  "fixture_id": "connector.local.filesystem.readonly.basic",
  "connector_id": "local.filesystem.readonly",
  "operation": "list_resources",
  "input": {
    "path": "docs"
  },
  "expected": {
    "ok": true,
    "mutations_performed": false,
    "network_used": false,
    "external_api_used": false
  },
  "redaction_required": true
}
```

### 6.3 Connector sandbox report

```json
{
  "schema_version": "1.0",
  "connector_id": "local.filesystem.readonly",
  "mode": "replay",
  "ok": true,
  "policy_passed": true,
  "approval_required": false,
  "network_used": false,
  "external_api_used": false,
  "mutations_performed": false,
  "fixtures_total": 3,
  "fixtures_passed": 3,
  "blocking_findings_total": 0
}
```

## 7. Principios de diseño

```text
1. Deny-write by default.
2. Replay before integration.
3. No real secrets in fixtures.
4. No network unless a future ADR explicitly allows it.
5. No connector write until POST-H-018 is closed and a later write-specific ADR exists.
6. Every connector must declare side_effect and data_sensitivity.
7. Every connector must have policy coverage.
8. Every side-effecting connector must require approval and RBAC even in future design.
9. Reports must distinguish validation, replay, dry-run and real execution.
10. A connector registry entry is not permission to execute.
```

## 8. Micro-sprints propuestos

### POST-H-018-A — Connector sandbox policy y schemas

Objetivo: definir el contrato estructural y la política local de sandbox para conectores.

Tareas:

```text
1. Crear connector_sandbox_policy.schema.json.
2. Crear connector_replay_fixture.schema.json.
3. Crear connector_sandbox_report.schema.json.
4. Registrar los schemas en schema_catalog.json.
5. Crear .devpilot/connectors/connector_sandbox_policy.json.
6. Clasificar conectores actuales por status, side_effect, risk_level y mode.
7. Crear tests de schema y validación estructural.
```

Criterios PASS:

```text
PASS si todos los connectors actuales tienen entrada de sandbox policy.
PASS si network_allowed=false por defecto.
PASS si mutations_allowed=false por defecto.
PASS si connector write queda explícitamente no permitido.
PASS si los schemas se registran correctamente.
```

Criterios BLOCK:

```text
BLOCK si se habilita network/external_api por defecto.
BLOCK si se permite connector write.
BLOCK si una entrada carece de side_effect o risk_level.
```

### POST-H-018-B — Sandbox runner read-only/dry-run

Objetivo: implementar un runner de sandbox que solo ejecute validación, dry-run o replay local.

Tareas:

```text
1. Crear src/devpilot_core/connectors/sandbox.py.
2. Implementar ConnectorSandboxRequest y ConnectorSandboxResult.
3. Integrar PolicyEngine antes de cualquier operación.
4. Bloquear modos distintos de validate/dry-run/replay.
5. Generar ConnectorSandboxReport.
6. Agregar CLI preliminar connector sandbox run --mode replay --json.
7. Crear tests de bloqueo de modos peligrosos.
```

Criterios PASS:

```text
PASS si el runner solo acepta validate/dry-run/replay.
PASS si cualquier intento de write produce BLOCK.
PASS si PolicyEngine se invoca en operaciones de riesgo medio o alto.
PASS si el reporte declara network_used=false y mutations_performed=false.
```

Criterios BLOCK:

```text
BLOCK si se invoca red real.
BLOCK si se muta un recurso externo.
BLOCK si se omite PolicyEngine.
```

### POST-H-018-C — Replay fixtures y redacción

Objetivo: crear fixtures reproducibles y seguros para probar conectores sin red ni secretos.

Tareas:

```text
1. Crear evals/fixtures/connector_replay_cases.json.
2. Implementar ConnectorReplayRunner.
3. Validar que fixtures no contengan tokens, .env, API keys o URLs sensibles.
4. Implementar redaction report.
5. Crear tests de replay determinístico.
6. Integrar replay summary en sandbox report.
```

Criterios PASS:

```text
PASS si todos los fixtures pasan redaction checks.
PASS si replay es determinístico.
PASS si no hay secretos en fixtures.
PASS si los reportes indican fixtures_total/fixtures_passed.
```

Criterios BLOCK:

```text
BLOCK si un fixture contiene secreto o token.
BLOCK si replay intenta red.
BLOCK si replay modifica filesystem fuera de outputs/.devpilot permitidos.
```

### POST-H-018-D — Policy/approval/RBAC binding para conectores

Objetivo: conectar sandbox de conectores con PolicyEngine, Approval y RBAC.

Tareas:

```text
1. Definir reglas mínimas de policy para connector.validate, connector.replay y connector.write_future.
2. Validar que connector.write_future siempre sea deny/block.
3. Integrar ApprovalPolicyChecker para side_effect != read/report/none.
4. Integrar Identity/RBAC para operaciones de riesgo alto.
5. Crear exposure report de conectores.
6. Crear tests de denegación por falta de approval/RBAC.
```

Criterios PASS:

```text
PASS si toda operación side-effecting futura queda bloqueada.
PASS si conectores read-only tienen policy coverage.
PASS si RBAC se evalúa para riesgo alto.
PASS si el exposure report lista conectores por riesgo.
```

Criterios BLOCK:

```text
BLOCK si connector write puede pasar sin approval.
BLOCK si una operación de riesgo alto no evalúa RBAC.
BLOCK si connector policy coverage es incompleta.
```

### POST-H-018-E — Quality gate, runbook y cierre

Objetivo: integrar sandbox de conectores al quality gate y documentar operación segura.

Tareas:

```text
1. Agregar subgate connector-sandbox a quality-gate hardening o perfil específico.
2. Crear docs/05_operations/connector_sandbox_runbook.md.
3. Documentar límites: read-only/replay/dry-run.
4. Agregar test contract post-h-018-connector-sandbox.
5. Ejecutar tests focales.
6. Ejecutar quality-gate correspondiente.
```

Criterios PASS:

```text
PASS si el subgate pasa con network_used=false.
PASS si connector write sigue bloqueado.
PASS si el runbook explica no-go gates.
PASS si test-contracts validate reconoce el nuevo contrato.
```

Criterios BLOCK:

```text
BLOCK si el gate permite external_api_used=true.
BLOCK si se declara que conectores write están listos.
BLOCK si no hay runbook operativo.
```

## 9. Comandos esperados de validación

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_post_h_018_connector_sandbox_policy.py -q
python -m pytest tests/test_post_h_018_connector_replay.py -q
python -m pytest tests/test_post_h_018_connector_sandbox_gate.py -q
python -m devpilot_core schema validate --schema ConnectorSandboxPolicy --instance .devpilot/connectors/connector_sandbox_policy.json --json
python -m devpilot_core connector sandbox run --mode replay --json
python -m devpilot_core quality-gate run --profile hardening --json
python -m devpilot_core test-contracts validate --json
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Confundir registry con ejecución permitida | Alta | Reportes deben separar declared/validated/replayed/executable. |
| Habilitar write accidental | Crítica | Deny-write by default + tests BLOCK. |
| Filtrar secretos en fixtures | Alta | Redaction checks obligatorios. |
| Usar red en replay | Alta | network_allowed=false + monkeypatch/tests. |
| Policy coverage incompleta | Alta | Semantic checks y quality gate. |

## 11. No-go gates

```text
NO-GO si connector write queda habilitado.
NO-GO si una operación usa red real.
NO-GO si se almacenan secretos reales.
NO-GO si se permite external_api_used=true.
NO-GO si se omite PolicyEngine en conectores de riesgo medio/alto.
NO-GO si se declara capacidad productiva de integración externa.
```

## 12. Definition of Done

```text
- Schemas de sandbox/replay/report creados y registrados.
- Connector sandbox policy validable.
- Runner validate/dry-run/replay implementado sin write real.
- Fixtures de replay seguros y determinísticos.
- Policy/approval/RBAC binding probado.
- Quality gate actualizado.
- Runbook operativo aprobado.
- Test contract agregado.
- Ninguna mutación externa, red o API externa usada.
```
