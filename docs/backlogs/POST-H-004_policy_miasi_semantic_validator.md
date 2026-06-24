---
doc_id: "POST-H-004-BACKLOG"
id: "POST-H-004"
title: "POST-H-004 — Policy/MIASI semantic validator ampliado"
status: "approved"
version: "0.5.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
priority: "P0"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
implementation_status: "in-progress"
approval: "internal"
---

# POST-H-004 — Policy/MIASI semantic validator ampliado

## 1. Objetivo

Implementar un validador semántico ampliado que verifique coherencia transversal entre:

```text
agent → tool → policy_rule → side_effect → approval → RBAC → security guards → observability → evals → test contracts
```

La validación estructural actual de MIASI es necesaria, pero insuficiente para garantizar que agentes, herramientas y políticas sensibles estén correctamente gobernadas antes de escalar capacidades agentic.

## 2. Contexto

DevPilot cuenta con:

```text
.devpilot/miasi/agent_registry.json
.devpilot/miasi/tool_registry.json
.devpilot/miasi/policy_matrix.json
src/devpilot_core/miasi/registry.py
src/devpilot_core/policy/engine.py
src/devpilot_core/approval/
src/devpilot_core/identity/
src/devpilot_core/security/
src/devpilot_core/observability/
src/devpilot_core/evals/
```

El assessment post-H identificó riesgos como remote execution prematura, connector write accidental, plugin execution insegura, actor spoofing, secret leakage, runtime artifacts y RAG sin groundedness. Este hito convierte esos riesgos en reglas semánticas ejecutables.

## 3. Alcance

Incluye:

```text
- Semantic validator para MIASI/Policy.
- Reglas por risk_level y side_effect.
- Validación de approvals y RBAC para herramientas sensibles.
- Validación de observability requerida.
- Validación de eval/test contract asociados para capacidades agentic críticas.
- CLI read-only.
- Integración con quality-gate como subgate o señal P0.
```

No incluye:

```text
- Activar nuevas herramientas.
- Ejecutar tools del registry.
- Habilitar connector write.
- Habilitar plugin execution.
- Habilitar remote execution.
- Cambiar semántica de PolicyEngine sin tests explícitos.
```

## 4. Entregables

```text
src/devpilot_core/miasi/semantic.py
src/devpilot_core/miasi/semantic_rules.py
src/devpilot_core/miasi/semantic_models.py
docs/schemas/miasi_semantic_report.schema.json
docs/03_security/policy_miasi_semantic_validation.md
tests/test_miasi_semantic_validator.py
tests/test_miasi_semantic_validator_fixtures.py
```

Fixtures recomendados:

```text
tests/fixtures/miasi/valid_semantic_bundle.json
tests/fixtures/miasi/missing_approval_for_high_risk_tool.json
tests/fixtures/miasi/remote_enabled_invalid.json
tests/fixtures/miasi/plugin_execution_without_sandbox.json
tests/fixtures/miasi/connector_write_without_adr.json
```

## 5. Reglas semánticas mínimas

### 5.1. Agentes

```text
- Todo agente debe tener allowed_tools existentes.
- Todo agente A3+ debe declarar observability y eval strategy.
- Todo agente high risk debe tener test contract asociado.
- Todo agente con tool high-risk debe requerir approval o default_effect block/deny.
- Agentes future/planned no deben ser ejecutables por AgentRuntime.
```

### 5.2. Tools

```text
- Tool high-risk + controlled_write requiere approval_required=true.
- Tool high-risk + controlled_execution requiere approval, RBAC y observability.
- Tool network_cost requiere CostGuard y external_api_allowed=false por defecto.
- Tool connector.write debe permanecer blocked salvo ADR y sandbox futuros.
- Tool plugin.execute debe permanecer blocked hasta plugin sandbox.
- Tool remote.execute debe permanecer blocked.
```

### 5.3. Policy Matrix

```text
- Toda tool debe referenciar reglas existentes.
- Toda regla deny/block debe tener observability_required=true.
- Toda regla allow sobre side_effect sensible debe tener guard explícito.
- No puede existir contradicción allow vs block para la misma agent/tool/action sin precedencia explícita.
- Reglas de remote/plugin/connector write deben mantenerse block/deny.
```

### 5.4. Approval/RBAC

```text
- Acciones sensibles requieren approval_scope claro.
- Acciones sensibles requieren RBAC role mínimo.
- Actor local debe estar declarado o tratado como unknown con restricciones.
- Approval no puede ser genérico para tool/action/subject sensibles.
```

### 5.5. Observability/Evals/Test Contracts

```text
- High-risk tools requieren observability.
- Agentic workflows requieren handoff traces.
- Capacidades P0/P1 deben mapearse a test contracts.
- Casos de red-team deben existir para injection/secret/remote/plugin/connector.
```

## 6. Micro-sprints propuestos

### POST-H-004-A — Modelo semántico y report schema

Tareas:

```text
1. Crear MiasiSemanticReport, SemanticFinding, SemanticRuleResult.
2. Crear schema miasi_semantic_report.schema.json.
3. Registrar schema en schema_catalog.
4. Definir severity mapping: info/warning/error/block.
```

PASS:

```text
PASS si el schema valida reportes válidos.
PASS si findings block son machine-readable.
```

#### Avance POST-H-004-A — implemented-initial

Estado: `implemented-initial` / `schema-only`.

Implementado:

```text
- `MiasiSemanticReport`, `SemanticFinding` y `SemanticRuleResult`.
- `docs/schemas/miasi_semantic_report.schema.json`.
- Registro `SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1` en `schema_catalog`.
- Mapeo de severidad semántica `info/warning/error/block`.
- Fixtures de reporte válido e inválido.
- Pruebas focales de modelo/schema.
```

No implementado todavía:

```text
- Reglas agent/tool/policy.
- Reglas approval/RBAC/security guards.
- Cruce con observability/evals/test contracts.
- Integración con quality-gate.
```

Criterio de alcance: `POST-H-004-A` define contrato y modelo de reporte; la ejecución semántica empieza en `POST-H-004-B`.


### POST-H-004-B — Reglas agent/tool/policy

Tareas:

```text
1. Implementar carga del bundle MIASI actual.
2. Validar allowed_tools, policy_rule_ids y status.
3. Detectar tools sensibles sin approval.
4. Detectar rules contradictorias.
```

Comando propuesto:

```powershell
python -m devpilot_core miasi semantic-validate --json
```


## 6.2. Avance de implementación POST-H-004-B

Estado: `implemented-initial`.

`POST-H-004-B` implementa el comando:

```powershell
python -m devpilot_core miasi semantic-validate --json
```

Alcance implementado:

```text
- Carga del bundle MIASI vigente desde .devpilot/miasi/.
- Validación semántica de allowed_tools contra Tool Registry.
- Validación semántica de policy_rule_ids contra Policy Matrix.
- Validación preliminar de status para evitar ejecutabilidad prematura.
- Detección de tools sensibles sin approval explícito.
- Detección de contradicciones de policy rules para el mismo domain/action.
- Detección de no-go gates remote/plugin/connector execute en allow.
- Reporte MiasiSemanticReport validable por schema.
- Fixtures inseguros que deben fallar con BLOCK.
```

Límites explícitos:

```text
- No integra aún approval/RBAC/security guards; eso corresponde a POST-H-004-C.
- No cruza observability/evals/test contracts; eso corresponde a POST-H-004-D.
- No integra semantic-validate al quality-gate; eso corresponde a POST-H-004-E.
- No ejecuta agentes, tools, pytest, subprocesses, red, APIs externas, conectores, plugins ni remote runners.
```

Nota de madurez: el bundle vigente pasa con warnings por cuatro tools high-risk `controlled_write` sin approval explícito (`patch.sandbox`, `rollback.plan`, `workspace.registry.register`, `auditpack.build`). Se mantienen como warnings porque actualmente son flujos locales/sandboxed/registry/rollback y se endurecerán en POST-H-004-C con reglas approval/RBAC/security guards.

### POST-H-004-C — Reglas de approval/RBAC/security guards

Tareas:

```text
1. Cruzar policy rules con approval metadata.
2. Cruzar tool risk/side_effect con RBAC requirements.
3. Validar que secrets/network/external-api estén bloqueados o gobernados.
4. Generar findings BLOCK para remote/plugin/connector write prematuros.
```

## 6.3. Avance de implementación POST-H-004-C

Estado: `implemented-initial`.

`POST-H-004-C` amplía `miasi semantic-validate` con reglas de approval/RBAC/security guards sin ejecutar agentes, tools, subprocesses, pytest, red ni APIs externas.

Alcance implementado:

```text
- Validación de approval metadata para tools sensibles.
- Bloqueo de approvals genéricos para tool/action/subject sensible.
- Carga y validación semántica básica de Identity Registry local.
- Verificación de deny_unknown_actor y rbac_enforced_for_sensitive_actions.
- Verificación de actor local activo y roles conocidos.
- Verificación de permisos RBAC de aprobación/acciones críticas.
- Validación de CostGuard/NoExternalAPI/NoNetwork/LocalhostOnly para network_cost.
- Validación de guards locales para write-capable tools.
- Bloqueo de remote/plugin/connector write/execute prematuro.
- Fixtures inseguros para RBAC ausente, approval genérico, network cost sin CostGuard y connector write sin ADR/sandbox.
```

Límites explícitos:

```text
- No cruza aún observability/evals/test contracts; eso corresponde a POST-H-004-D.
- No integra aún semantic-validate al quality-gate; eso corresponde a POST-H-004-E.
- No modifica PolicyEngine ni habilita capacidades runtime.
```

Nota de madurez: el bundle vigente sigue pasando con warnings por deuda de aprobación/RBAC en high-risk `controlled_write` implementado-initial. Esas advertencias no autorizan producción; mantienen trazabilidad para hardening posterior.

### POST-H-004-D — Observability, evals y test contracts

Tareas:

```text
1. Validar observability_required para reglas sensibles.
2. Validar existencia de fixtures/evals mínimos para red-team y agentic safety.
3. Cruzar capacidades high-risk con Test Contract Registry v1/v2 si existe.
4. Emitir warnings si TCR v2 aún no está implementado.
```


## 6.4. Avance de implementación POST-H-004-D

Estado: `implemented-initial`.

`POST-H-004-D` amplía el comando:

```powershell
python -m devpilot_core miasi semantic-validate --json
```

Alcance implementado:

```text
- Validación de observability_required para agentes A3+/high-risk.
- Validación de eval_required para agentes A3+/high-risk.
- Validación de handoff traces para capacidades multiagent/workflow.
- Validación de observability_required para tools sensibles y policy rules deny/block/approval/no-go.
- Validación de fixtures/evals locales mínimos: red-team, advanced-agentic, plugin-ecosystem, identity-rbac y remote-enterprise.
- Validación de que fixtures/evals sigan siendo locales, deterministas, sin red, sin API externa y sin LLM judge.
- Cruce preliminar con Test Contract Registry v1/v2.
- Warning explícito si el validador semántico todavía no tiene contrato formal v1/v2.
```

Límites explícitos:

```text
- No integra todavía semantic-validate al quality-gate; eso corresponde a POST-H-004-E.
- No agrega aún el contrato formal de cierre POST-H-004; eso corresponde a POST-H-004-E.
- No ejecuta agentes, tools, evals, pytest desde JSON, subprocesses, red ni APIs externas.
```

Nota de madurez: `POST-H-004-D` conserva warnings no bloqueantes para deuda de aprobación/RBAC en `controlled_write` high-risk implementado-initial y para la ausencia del contrato formal del validador semántico en TCR. Estas warnings no autorizan promoción a producción; definen deuda a cerrar en `POST-H-004-E` y/o hitos posteriores.

### POST-H-004-E — Integración con quality-gate y documentación

Tareas:

```text
1. Integrar miasi semantic-validate como subgate o pre-subgate.
2. Documentar en security docs.
3. Agregar pruebas focales.
4. Agregar contract de POST-H-004.
```

## 7. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_miasi_semantic_validator.py -q
python -m pytest tests/test_miasi_semantic_validator_fixtures.py -q
python -m devpilot_core miasi validate --json
python -m devpilot_core miasi semantic-validate --json
python -m devpilot_core schema validate --schema-id MiasiSemanticReport --instance outputs/reports/miasi_semantic_report.json --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 8. Criterios PASS

```text
PASS si el bundle MIASI vigente pasa validación semántica.
PASS si fixtures inseguros fallan con BLOCK.
PASS si remote execution, connector write y plugin execution siguen bloqueados.
PASS si high-risk tools requieren approval/RBAC/observability.
PASS si el reporte generado es validable por schema.
```

## 9. Criterios BLOCK

```text
BLOCK si alguna regla permite remote.execute.
BLOCK si connector.write está allow sin ADR/sandbox.
BLOCK si plugin.execute está allow sin sandbox.
BLOCK si una tool high-risk controlled_write no requiere approval.
BLOCK si un agente future/planned aparece ejecutable.
BLOCK si se relaja PolicyEngine para pasar tests.
```

## 10. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Falsos positivos por reglas demasiado rígidas | Media | Fixtures válidos e inválidos; severity warning vs block. |
| Falso PASS semántico | Alta | Reglas explícitas para remote/plugin/connector/high-risk. |
| Duplicar PolicyEngine | Alta | Validator detecta coherencia; PolicyEngine sigue ejecutando decisiones. |
| Acoplar demasiado a formato actual MIASI | Media | Modelos internos y schema de reporte estable. |
| Bloquear desarrollo legítimo | Media | Excepciones solo con ADR y test contract. |

## 11. No-go gates

```text
NO-GO si el hito modifica AgentRuntime para permitir más acciones.
NO-GO si se habilita tool execution genérico.
NO-GO si se habilita remote/connectors/plugins.
NO-GO si se declaran capacidades enterprise/compliance certificadas.
```

## 12. Entregable verificable

```text
Comando miasi semantic-validate.
Reporte JSON/Markdown con findings semánticos.
Fixtures inseguros bloqueados.
Quality gate hardening PASS.
```
