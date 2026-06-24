---
title: "Policy/MIASI Semantic Validation"
doc_id: "DEVPL-SEC-POST-H-004"
status: "approved"
version: "0.4.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
sprint: "POST-H-004-D"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# Policy/MIASI Semantic Validation

## 1. Propósito

Definir la base de seguridad para el validador semántico ampliado de `POST-H-004`, encargado de verificar coherencia transversal entre agentes, herramientas, reglas de política, efectos laterales, aprobaciones, RBAC, security guards, observabilidad, evaluaciones y contratos de prueba.

## 2. Estado

`POST-H-004-D` agrega cruces de observability/evals/test contracts sobre la base agent/tool/policy y approval/RBAC/security guards de `POST-H-004-B/C`. El hito todavía no integra `miasi semantic-validate` como subgate de quality-gate; eso queda para `POST-H-004-E`.

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

Esta primera versión no reemplaza `miasi validate`, no modifica `PolicyEngine`, no ejecuta agentes, no ejecuta tools, no habilita conectores, no habilita plugins y no habilita ejecución remota. Las reglas semánticas se implementan progresivamente en `POST-H-004-B`, `POST-H-004-C`, `POST-H-004-D` y se integrarán al gate en `POST-H-004-E`.

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

La decisión de dejar ciertos `controlled_write` high-risk como `warning` y no como `block` en esta etapa es deliberada: el bundle vigente contiene capacidades `implemented-initial` locales/sandboxed que deben seguir visibles como deuda semántica sin bloquear el avance de `POST-H-004-B`. `POST-H-004-C` agregó cruces de approval/RBAC/security guards; `POST-H-004-D` conserva la deuda como warning y la cruza con observability/evals/test contracts.

## 9. Verificación semántica agent/tool/policy

```powershell
python -m devpilot_core miasi semantic-validate --json
python -m pytest tests/test_miasi_semantic_validator.py tests/test_miasi_semantic_validator_fixtures.py -q
```

## 10. Límites de POST-H-004-B

`POST-H-004-B` no ejecuta agentes, tools, PolicyEngine, pytest, subprocesses, conectores, plugins, red ni APIs externas. No reemplaza el gate estructural `miasi validate`; lo complementa con una lectura semántica preliminar que será endurecida en `POST-H-004-C/D/E`.

## 11. Reglas approval/RBAC/security guards implementadas en POST-H-004-C

La segunda capa semántica valida:

```text
- Tools con requires_approval=true deben estar respaldadas por policy rules/gates de aprobación concretos.
- Approval genérico para tool/action/subject sensible → BLOCK.
- Identity Registry debe existir, negar actores desconocidos y exigir RBAC para acciones sensibles.
- Active actor local debe existir, estar activo y usar roles conocidos.
- Roles RBAC deben incluir permisos de aprobación/acciones críticas para operaciones sensibles.
- Tools controlled_execution/network_cost con approval deben estar ligadas a approval/RBAC/actor gates.
- Tools network_cost requieren approval + CostGuard/NoExternalAPI/NoNetwork/LocalhostOnly.
- Tools write-capable requieren PathGuard/PolicyEngine/sandbox/local/rollback/registry u otros guards locales.
- Remote/plugin/connector write o execute deben permanecer deny/block o metadata/dry-run/sandbox futuro, nunca allow prematuro.
```

El reporte mantiene `dry_run=true`, `tests_executed=false`, `network_used=false`, `external_api_used=false`, `mutations_performed=false` y `source_mutations_performed=false`.

## 12. Verificación semántica approval/RBAC/security guards

```powershell
python -m devpilot_core miasi semantic-validate --json
python -m pytest tests/test_miasi_semantic_validator.py tests/test_miasi_semantic_validator_fixtures.py -q
```

## 13. Reglas observability/evals/test contracts implementadas en POST-H-004-D

La tercera capa semántica valida:

```text
- Agentes A3+/high-risk deben declarar observability_required=true y eval_required=true.
- Capacidades multiagent/workflow deben declarar handoff traces.
- Tools high-risk/sensibles deben mapear a policy rules con observability_required=true.
- Policy rules deny/block/approval/no-go deben declarar observability_required=true.
- Deben existir fixtures/evals locales para red-team, advanced-agentic, plugin-ecosystem, identity-rbac y remote-enterprise.
- Fixtures/evals deben seguir sin red, sin APIs externas y sin LLM judge.
- La cobertura TCR v1/v2 se revisa y se reporta warning si falta contrato formal del semantic validator.
```

## 14. Límites de POST-H-004-D

`POST-H-004-D` no ejecuta agentes, tools, PolicyEngine, pytest desde JSON, evals reales, subprocesses, conectores, plugins, red ni APIs externas. No integra todavía el subgate de `quality-gate`; eso queda para `POST-H-004-E`. La ausencia del contrato formal del semantic validator en TCR se mantiene como warning controlado hasta el cierre del hito.
