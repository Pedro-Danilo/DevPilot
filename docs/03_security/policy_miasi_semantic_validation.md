---
title: "Policy/MIASI Semantic Validation"
doc_id: "DEVPL-SEC-POST-H-004"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
sprint: "POST-H-004-B"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# Policy/MIASI Semantic Validation

## 1. Propósito

Definir la base de seguridad para el validador semántico ampliado de `POST-H-004`, encargado de verificar coherencia transversal entre agentes, herramientas, reglas de política, efectos laterales, aprobaciones, RBAC, security guards, observabilidad, evaluaciones y contratos de prueba.

## 2. Estado

`POST-H-004-B` eleva la entrega a una versión inicial con reglas agent/tool/policy (`implemented-initial`). El hito todavía no valida approval/RBAC/security guards, observability/evals/test contracts ni se integra como subgate de quality-gate.

## 3. Contrato de reporte

El schema registrado es:

```text
SCHEMA-DEVPL-MIASI-SEMANTIC-REPORT-V1
Contrato: MiasiSemanticReport
Archivo: docs/schemas/miasi_semantic_report.schema.json
```

El reporte exige que todo análisis sea local, dry-run y no mutante:

```text
dry_run=true
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
```

## 4. Severidad semántica

El mapeo oficial de severidad para `POST-H-004` es:

| Severidad | Uso | Efecto esperado |
|---|---|---|
| `info` | Hallazgo informativo o regla pass | No bloquea |
| `warning` | Riesgo no bloqueante o deuda semántica | No bloquea por sí mismo |
| `error` | Violación semántica fuerte | Bloquea |
| `block` | No-go gate o condición insegura | Bloquea |

## 5. No-go gates

`POST-H-004-A` conserva explícitamente estos no-go gates:

```text
remote.execute debe permanecer bloqueado.
plugin.execute debe permanecer bloqueado hasta sandbox futuro.
connector.write debe permanecer bloqueado salvo ADR/sandbox/test-contract gates futuros.
```

## 6. Límites

Esta primera versión no reemplaza `miasi validate`, no modifica `PolicyEngine`, no ejecuta agentes, no ejecuta tools, no habilita conectores, no habilita plugins y no habilita ejecución remota. Las reglas semánticas se implementan progresivamente en `POST-H-004-B`, `POST-H-004-C` y `POST-H-004-D`.

## 7. Verificación

```powershell
python -m devpilot_core schema validate --schema-id MiasiSemanticReport --instance tests/fixtures/miasi_semantic_report/valid_schema_only_report.json --json
python -m pytest tests/test_miasi_semantic_report_model.py -q
```


## 8. Reglas agent/tool/policy implementadas en POST-H-004-B

La primera capa semántica valida:

```text
- Agentes con allowed_tools inexistentes → BLOCK.
- Agentes o tools con policy_rule_ids inexistentes o vacíos → BLOCK.
- Estados planned/future/disabled referenciados por componentes implementados → WARNING controlado.
- Tools high-risk con controlled_execution o network_cost sin approval explícito → BLOCK.
- Tools high-risk con controlled_write sin approval explícito pero con gates locales/sandbox/rollback/registry → WARNING evolutivo.
- Contradicciones allow/deny/block para el mismo domain/action sin precedencia → BLOCK.
- Reglas no-go de remote/plugin/connector execute en allow → BLOCK.
```

La decisión de dejar ciertos `controlled_write` high-risk como `warning` y no como `block` en esta etapa es deliberada: el bundle vigente contiene capacidades `implemented-initial` locales/sandboxed que deben seguir visibles como deuda semántica sin bloquear el avance de `POST-H-004-B`. `POST-H-004-C` debe endurecerlas con cruces explícitos de approval, RBAC y security guards.

## 9. Verificación semántica agent/tool/policy

```powershell
python -m devpilot_core miasi semantic-validate --json
python -m pytest tests/test_miasi_semantic_validator.py tests/test_miasi_semantic_validator_fixtures.py -q
```

## 10. Límites de POST-H-004-B

`POST-H-004-B` no ejecuta agentes, tools, PolicyEngine, pytest, subprocesses, conectores, plugins, red ni APIs externas. No reemplaza el gate estructural `miasi validate`; lo complementa con una lectura semántica preliminar que será endurecida en `POST-H-004-C/D/E`.
