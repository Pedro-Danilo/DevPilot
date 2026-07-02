---
doc_id: "POST-H-024-IMPLEMENTATION-DOC"
title: "POST-H-024 — Operator onboarding playbook y project bootstrap workflow"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
implementation_status: "in-progress"
current_micro_sprint: "POST-H-024-A"
next_micro_sprint: "POST-H-024-B"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-024 — Operator onboarding playbook y project bootstrap workflow

## 1. Estado

POST-H-024 queda aprobado para implementación incremental. POST-H-024-A queda implementado como **implemented-initial / playbook-only**.

El hito busca transformar el onboarding conversacional de DevPilot en un flujo reproducible para iniciar proyectos nuevos desde una idea hasta readiness y backlog ejecutable.

## 2. Micro-sprints

### POST-H-024-A — Playbook de operador

Estado: `implemented-initial`.

Artefactos:

```text
docs/05_operations/operator_onboarding_playbook.md
docs/audits/post_h_024_a_operator_playbook_report.md
docs/post_h_024_a_manifest.json
tests/test_post_h_024_operator_onboarding.py
```

Capacidad añadida:

```text
Guía operacional aprobada para que un operador ejecute el flujo idea → workspace → docs → readiness → backlog sin depender de memoria conversacional.
```

Límite:

```text
No implementa todavía templates, bootstrap workflow, readiness preview ni quality gate de onboarding.
```

### POST-H-024-B — Templates de proyecto nuevo

Estado: `pending`.

### POST-H-024-C — Bootstrap workflow dry-run

Estado: `pending`.

### POST-H-024-D — Onboarding validation y readiness preview

Estado: `pending`.

### POST-H-024-E — Quality gate y proyecto piloto fixture

Estado: `pending`.

## 3. Reglas de seguridad heredadas

```text
local_first=true
dry_run=true
no_remote_execution_enabled=true
no_external_apis_used=true
no_connector_write_enabled=true
no_plugin_execution_enabled=true
```

POST-H-024 no debe introducir generación mágica de código ni ejecución autónoma. La automatización futura debe ser plan-first, workspace-bounded y refusal-on-overwrite por defecto.
