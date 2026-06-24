---
title: "POST-H-004-A — Semantic model and report schema"
doc_id: "POST-H-004-A-AUDIT"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-24"
phase: "POST-FASE-H"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# POST-H-004-A — Semantic model and report schema

## Propósito

Crear la base contractual para el validador semántico ampliado Policy/MIASI sin activar todavía reglas ejecutables.

## Estado

`implemented-initial` / `schema-only`.

## Implementación

Se agregaron:

```text
src/devpilot_core/miasi/semantic_models.py
src/devpilot_core/miasi/semantic_rules.py
src/devpilot_core/miasi/semantic.py
docs/schemas/miasi_semantic_report.schema.json
tests/fixtures/miasi_semantic_report/valid_schema_only_report.json
tests/fixtures/miasi_semantic_report/invalid_mutating_report.json
tests/test_miasi_semantic_report_model.py
```

## Criterios PASS

```text
PASS si el schema `MiasiSemanticReport` está registrado.
PASS si el fixture válido valida contra schema.
PASS si el fixture con `dry_run=false` es rechazado.
PASS si un finding `block` se representa de forma machine-readable.
```

## Criterios BLOCK

```text
BLOCK si el contrato permite red, API externa o mutación de fuentes.
BLOCK si el modelo no puede representar findings `block`.
BLOCK si se habilita ejecución de agentes, tools, conectores, plugins o remote runner en este micro-sprint.
```

## Riesgos y límites

Esta entrega no valida todavía coherencia real agent/tool/policy. La validación semántica efectiva inicia en `POST-H-004-B`.
