---
doc_id: "POST-H-024-IMPLEMENTATION-DOC"
title: "POST-H-024 — Operator onboarding playbook y project bootstrap workflow"
status: "approved"
version: "0.5.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
implementation_status: "in-progress"
current_micro_sprint: "POST-H-024-D"
next_micro_sprint: "POST-H-024-E"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-024 — Operator onboarding playbook y project bootstrap workflow

## 1. Estado

POST-H-024 queda aprobado para implementación incremental. POST-H-024-A queda implementado como **implemented-initial / playbook-only**, POST-H-024-B queda implementado como **implemented-initial / templates-only**, POST-H-024-C queda implementado como **implemented-initial / bootstrap-dry-run** y POST-H-024-D queda implementado como **implemented-initial / readiness-preview-only**.

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

Estado: `implemented-initial`.

Artefactos:

```text
docs/templates/new_project/product_vision.template.md
docs/templates/new_project/mvp_scope.template.md
docs/templates/new_project/requirements_specification.template.md
docs/templates/new_project/architecture_document.template.md
docs/templates/new_project/security_threat_model.template.md
docs/templates/new_project/test_strategy.template.md
docs/templates/new_project/miasi_agent_registry.template.json
docs/templates/new_project/miasi_tool_registry.template.json
docs/templates/new_project/miasi_policy_matrix.template.json
src/devpilot_core/onboarding/templates.py
docs/audits/post_h_024_b_project_templates_report.md
docs/post_h_024_b_manifest.json
tests/test_post_h_024_project_templates.py
```

Capacidad añadida:

```text
Plantillas versionadas y verificables para convertir la idea de proyecto en documentación pre-code mínima y registries MIASI iniciales sin secrets, red, APIs externas ni vendor lock-in obligatorio.
```

Límite:

```text
No implementa todavía materialización de workspace, comando bootstrap, project_bootstrap_report, readiness preview ni quality gate de onboarding.
```

### POST-H-024-C — Bootstrap workflow dry-run

Estado: `implemented-initial`.

Artefactos:

```text
docs/schemas/project_bootstrap_report.schema.json
src/devpilot_core/workspace/bootstrap.py
src/devpilot_core/cli_commands/workspace.py
src/devpilot_core/cli.py
docs/audits/post_h_024_c_project_bootstrap_report.md
docs/post_h_024_c_manifest.json
tests/test_post_h_024_project_bootstrap.py
```

Capacidad añadida:

```text
Workflow local-first para planificar y, con --execute explícito, materializar un workspace inicial bajo target permitido. Genera plan de .devpilot/project.yaml, documentación pre-code y registries MIASI; produce ProjectBootstrapReport cuando --write-report es explícito.
```

Límite:

```text
implemented-initial / bootstrap-dry-run. No ejecuta readiness preview, no activa quality gate de onboarding, no genera código productivo, no llama modelos ni APIs externas y no sobrescribe archivos existentes.
```

### POST-H-024-D — Onboarding validation y readiness preview

Estado: `implemented-initial`.

Artefactos:

```text
docs/schemas/onboarding_readiness_preview_report.schema.json
src/devpilot_core/onboarding/readiness_preview.py
src/devpilot_core/cli_commands/workspace.py
src/devpilot_core/cli.py
docs/audits/post_h_024_d_onboarding_readiness_preview_report.md
docs/post_h_024_d_manifest.json
tests/test_post_h_024_onboarding_readiness_preview.py
```

Capacidad añadida:

```text
Preview read-only de readiness por fases para proyectos nuevos, integrando validación de frontmatter, artifact, checklist, strict readiness, StandardsRegistry y MIASI schema/validate. Los faltantes quedan como pending, no como success.
```

Límite:

```text
implemented-initial / readiness-preview-only. No crea fixture piloto, no integra todavía el quality gate onboarding-bootstrap-ready, no genera código, no llama modelos ni APIs externas y no muta source/workspace salvo reporte opcional bajo outputs/.
```

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

POST-H-024 no debe introducir generación mágica de código ni ejecución autónoma. La automatización futura debe ser plan-first, workspace-bounded y refusal-on-overwrite por defecto. POST-H-024-C conserva el alcance `bootstrap-dry-run`: el modo por defecto no escribe archivos de workspace; `--execute` está acotado al target permitido y rechaza overwrite por defecto. POST-H-024-D conserva el alcance `readiness-preview-only`: inspecciona, reporta pendientes y evita falsa readiness sin activar quality gate todavía.
