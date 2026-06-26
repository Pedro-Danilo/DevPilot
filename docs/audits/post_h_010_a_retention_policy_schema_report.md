---
doc_id: "POST-H-010-A-AUDIT"
id: "POST-H-010-A"
title: "POST-H-010-A — Retention policy schema y defaults locales"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
network_used: false
external_api_used: false
llm_judge_used: false
source_mutations_performed: false
---

# POST-H-010-A — Retention policy schema y defaults locales

## 1. Propósito

Iniciar `POST-H-010 — Observability retention local` con un contrato source-controlled para la retención local de observabilidad de DevPilot.

La implementación define el schema `ObservabilityRetentionPolicy`, registra el contrato en el catálogo de schemas, crea la política local `.devpilot/observability/retention_policy.json` y agrega un loader/validator semántico para defaults seguros. No ejecuta inventario, limpieza, rotación, exportación ni mutaciones runtime.

## 2. Alcance implementado

```text
- Schema JSON para política local de retención de observabilidad.
- Política local versionada con targets críticos.
- Loader y validador semántico en observability/retention.py.
- Tests de schema, carga de defaults y no-go gates.
- Promoción del backlog POST-H-010 a approved.
- Documentación runtime vs fuente versionable en backlog, README y runbook.
```

## 3. Targets gobernados

```text
- outputs/traces/events.jsonl
- outputs/traces/
- .devpilot/devpilot.db
- .devpilot/agent_sessions/
- outputs/reports/
- logical scope metrics en .devpilot/devpilot.db
```

Todos los targets son runtime, no source-of-truth, no versionables y quedan marcados con `clean_zip_excluded=true`.

## 4. PASS/BLOCK

PASS:

```text
- retention_policy.json valida contra ObservabilityRetentionPolicy.
- Todos los targets críticos están presentes.
- remote_export_enabled=false.
- default_mode=dry-run.
- raw_prompts_allowed=false.
- raw_outputs_allowed=false.
- secrets_allowed=false.
- outputs, db y agent_sessions tienen clean_zip_excluded=true.
```

BLOCK:

```text
- Se habilita export remoto.
- Se permite guardar raw prompts/raw outputs.
- Se permite secrets_allowed=true.
- Se omite .devpilot/devpilot.db o .devpilot/agent_sessions/.
- Un target runtime queda marcado como source_of_truth o versionable.
```

## 5. Seguridad

```text
local_first=true
default_mode=dry-run
remote_export_enabled=false
network_used=false
external_api_used=false
mutations_performed=false
source_mutations_performed=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 6. Limitaciones

Esta versión es `implemented-initial`. Solo fija el contrato y los defaults locales. El inventario read-only, cleanup plan dry-run, export redactado e integración con `quality-gate hardening` quedan para `POST-H-010-B/C/D/E`.
