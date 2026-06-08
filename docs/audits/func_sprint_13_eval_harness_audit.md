---
title: "FUNC-SPRINT-13 — Evaluation Harness para validadores y agentes"
doc_id: "DEVPL-AUDIT-FUNC-013"
status: approved
version: 1.0.0
owner: "Ordóñez"
updated: 2026-06-08
approval: approved_by_owner_direction
---

# FUNC-SPRINT-13 — Evaluation Harness para validadores y agentes

## 1. Propósito

Implementar un Evaluation Harness offline para validar de forma reproducible el comportamiento de validadores documentales y agentes documentales MVP. El objetivo es detectar regresiones funcionales, falsos positivos y falsos negativos antes de avanzar hacia Git read-only, patch review y agentes más autónomos.

## 2. Alcance implementado

Sprint 13 implementa:

- fixtures sintéticos versionados en `evals/fixtures/documentation_eval_cases.json`;
- modelos de evaluación en `src/devpilot_core/evals/models.py`;
- `EvalRunner` en `src/devpilot_core/evals/runner.py`;
- comando CLI `python -m devpilot_core eval run`;
- reportes opcionales JSON/Markdown mediante `ReportEngine`;
- eventos JSONL mediante `EventLogger`;
- persistencia SQLite best-effort mediante `LocalStore`;
- pruebas automatizadas en `tests/test_eval_runner.py`;
- actualización de README, runbook, Eval Card, Test Strategy y backlog.

## 3. Funcionamiento técnico

`EvalRunner` carga la suite `documentation`, crea archivos temporales bajo `outputs/evals/workdir/`, ejecuta el componente declarado en cada caso y compara el resultado con la expectativa.

Componentes evaluados:

- `validate_frontmatter`;
- `validate_artifact`;
- `agent.documentation_audit`;
- `agent.precode_documentation`.

Cada caso declara:

```text
id
component
description
input
expected.ok
expected.finding_ids
tags
```

El resultado agregado calcula:

```text
cases_total
cases_passed
cases_failed
pass_rate
false_positives
false_negatives
missing_expected_findings
```

## 4. Comandos de uso

```powershell
python -m devpilot_core eval run --json
python -m devpilot_core eval run --json --write-report
python -m devpilot_core eval run --case-id frontmatter-missing-doc-id --json
python -m pytest -q
```

## 5. Integración dentro de DevPilot

El Evaluation Harness se integra con:

- validadores de frontmatter y artefactos;
- `AgentRuntime` documental MVP;
- `PolicyEngine`, porque los agentes evaluados conservan sus gates;
- `ReportEngine`, para evidencia JSON/Markdown;
- `EventLogger`, para trazas JSONL;
- `LocalStore`, para historial operativo best-effort.

## 6. Criterios PASS

- `pytest -q` en PASS.
- `eval run --json` retorna `ok=true`.
- `pass_rate = 1.0` en la suite sintética vigente.
- `false_positives = 0`.
- `false_negatives = 0`.
- `missing_expected_findings = 0`.
- No hay llamadas externas ni dependencias nuevas.
- El workdir queda bajo `outputs/evals/`.

## 7. Criterios BLOCK

- Cualquier falso negativo en caso defectuoso.
- Cualquier falso positivo no justificado en caso limpio.
- Hallazgo esperado ausente.
- Fixture que intenta escapar del directorio de evaluación.
- Uso de LLM externo, API externa o red.
- Salida JSON no parseable.

## 8. Pruebas implementadas

`tests/test_eval_runner.py` agrega pruebas para:

- ejecución completa de la suite documental;
- filtro por `case_id`;
- bloqueo de `case_id` inexistente;
- CLI `eval run --json --write-report`;
- CLI con caso de secreto sintético en `PreCodeDocumentationAgent`.

## 9. Riesgos y límites

Esta es una implementación preliminar. Los fixtures son sintéticos y pequeños. No mide todavía:

- groundedness;
- utilidad semántica;
- robustez adversarial;
- precisión de modelos;
- cobertura ponderada por severidad;
- evaluación continua histórica;
- red teaming.

Debe evolucionar hacia datasets versionados, golden outputs, métricas por agente, comparación de proveedores locales/API y reportes históricos.

## 10. ADR

No se abre una nueva ADR. Sprint 13 materializa una capacidad ya prevista por MIASI y por la estrategia de calidad. No agrega dependencias externas, no cambia arquitectura de persistencia, no introduce proveedores LLM y no habilita acciones destructivas.

## 11. Estado

`FUNC-SPRINT-13` queda implementado en estado inicial. El siguiente sprint funcional es `FUNC-SPRINT-14 — Git read-only y repo inventory MVP+`.
