---
title: "POST-H-004-D — Observability, evals y test contracts"
doc_id: "POST-H-004-D-AUDIT"
status: "approved"
approval: "internal"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
local_first: true
dry_run: true
---

# POST-H-004-D — Observability, evals y test contracts

## Propósito

Agregar al validador semántico MIASI una tercera capa de gobierno declarativo para observabilidad, fixtures/evals locales y cobertura preliminar de Test Contract Registry.

## Estado

`implemented-initial`. No declara producción local completa ni integra todavía el subgate de `quality-gate`.

## Alcance implementado

```text
- SEM-OBSERVABILITY-001.
- SEM-EVAL-COVERAGE-001.
- SEM-TEST-CONTRACT-COVERAGE-001.
- Fixture inseguro para agente high-risk sin observabilidad.
- Sin ejecución de agentes, tools, evals, pytest desde JSON, subprocesses, red o APIs externas.
```

## Funcionamiento

`MiasiSemanticValidator` carga el bundle MIASI vigente, valida las reglas heredadas de `POST-H-004-B/C` y añade cruces contra:

```text
- Agent observability/eval flags.
- Tool/policy observability requirements.
- Handoff trace declarations para multiagent/workflows.
- Fixtures/evals locales: red-team, advanced-agentic, plugin, RBAC y remote.
- TCR v1/v2 como evidencia de cobertura declarativa.
```

## Criterios PASS

```text
PASS si el bundle vigente produce blocking_findings_total=0.
PASS si fixtures/evals existen, son locales y cubren riesgos mínimos.
PASS si TCR v1/v2 existe y no permite red/API externa para contratos P0/P1 sensibles.
PASS si el reporte sigue validando contra MiasiSemanticReport.
```

## Criterios BLOCK

```text
BLOCK si un agente A3+/high-risk carece de observability/eval.
BLOCK si multiagent/workflow carece de handoff traces.
BLOCK si un fixture/eval declara red/API externa/LLM judge.
BLOCK si un contrato P0/P1 de seguridad/MIASI permite red/API externa.
```

## Riesgos y limitaciones

```text
- El contrato formal del validador semántico en TCR queda pendiente para POST-H-004-E.
- Los controlled_write high-risk implementado-initial siguen como warnings hasta hardening futuro.
- La validación es declarativa y no sustituye decisiones runtime del PolicyEngine.
```

## Comandos de validación

```powershell
python -m pytest tests/test_miasi_semantic_validator.py tests/test_miasi_semantic_validator_fixtures.py tests/test_miasi_semantic_report_model.py tests/test_miasi_registry.py tests/test_schema_registry.py -q
python -m devpilot_core miasi semantic-validate --json
python -m devpilot_core validate docs --json
python -m devpilot_core quality-gate run --profile hardening --json
```
