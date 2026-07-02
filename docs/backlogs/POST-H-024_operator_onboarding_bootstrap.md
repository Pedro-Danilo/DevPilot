---

doc_id: "POST-H-024-BACKLOG"
id: "POST-H-024"
title: "POST-H-024 — Operator onboarding playbook y project bootstrap workflow"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
implementation_status: "in-progress"
current_micro_sprint: "POST-H-024-B"
next_micro_sprint: "POST-H-024-C"
---

# POST-H-024 — Operator onboarding playbook y project bootstrap workflow

## 1. Objetivo

Convertir el conocimiento de onboarding y guía de operador de DevPilot en un **playbook operacional y workflow verificable de bootstrap de proyectos nuevos**, de forma que un operador pueda iniciar un proyecto desde una idea, crear workspace, generar documentación pre-code, validar readiness, activar MIASI y construir el primer backlog sin depender de memoria conversacional.

Este hito es requisito de adopción antes de declarar DevPilot como `production-ready-local`.

## 2. Contexto y justificación

El onboarding post-H evidenció que DevPilot ya puede guiar el desarrollo de una aplicación nueva, por ejemplo:

```text
Sistema agent-assisted de ventas e inventario para microemprendimientos locales
```

El flujo recomendado fue:

```text
Idea → Workspace → documentos producto → requisitos → arquitectura → seguridad → calidad → MIASI → readiness → backlog → código → review → tests → release dry-run
```

Pero ese flujo aún vive como guía conversacional/informe. Debe convertirse en artefactos versionados y validables:

```text
playbook;
templates;
checklists;
comandos;
fixtures;
workflow dry-run;
reporte de bootstrap;
quality gate de onboarding.
```

## 3. Alcance

Incluye:

```text
- Operator onboarding playbook.
- Templates para proyecto nuevo.
- Bootstrap workflow local dry-run.
- Checklist de operador.
- Reporte de bootstrap.
- Fixture piloto de proyecto ejemplo.
- Tests del workflow de onboarding.
- Integración con documentation governance.
```

No incluye:

```text
- Crear una aplicación real completa.
- Generar código productivo automáticamente.
- Remote scaffolding.
- Templates con secretos.
- Conectores write.
- Plugins ejecutables.
- Deploy real.
```

## 4. Fuentes de entrada obligatorias

```text
Informe de onboarding DevPilot — Hasta POST-H-EVAL-001.docx si está disponible
docs/backlogs/post_h_prioritized_roadmap.md
docs/audits/post_h_eval_001_baseline_assessment.md
docs/02_architecture/post_h_current_architecture_map.md
docs/05_operations/runbook.md
src/devpilot_core/workspace/manager.py
src/devpilot_core/agents/runtime.py
src/devpilot_core/validators/readiness.py
src/devpilot_core/standards/registry.py
src/devpilot_core/miasi/registry.py
```

## 5. Entregables

```text
docs/05_operations/operator_onboarding_playbook.md
docs/templates/new_project/product_vision.template.md
docs/templates/new_project/mvp_scope.template.md
docs/templates/new_project/requirements_specification.template.md
docs/templates/new_project/architecture_document.template.md
docs/templates/new_project/security_threat_model.template.md
docs/templates/new_project/test_strategy.template.md
docs/templates/new_project/miasi_agent_registry.template.json
docs/templates/new_project/miasi_tool_registry.template.json
docs/templates/new_project/miasi_policy_matrix.template.json
docs/schemas/project_bootstrap_report.schema.json
src/devpilot_core/workspace/bootstrap.py
src/devpilot_core/onboarding/playbook.py
src/devpilot_core/onboarding/templates.py
tests/test_post_h_024_operator_onboarding.py
tests/test_post_h_024_project_bootstrap.py
outputs/reports/project_bootstrap_report.json       # generado, no versionable
```

Actualizar:

```text
docs/schemas/schema_catalog.json
src/devpilot_core/cli.py o cli_registry
src/devpilot_core/application/services.py
docs/05_operations/runbook.md
.devpilot/testing/test_contract_registry.json
```

## 6. Modelo de datos mínimo

```json
{
  "schema_version": "1.0",
  "bootstrap_id": "project-bootstrap-sales-micro-local",
  "project": {
    "project_id": "ventas-micro-local",
    "project_name": "Sistema agent-assisted de ventas e inventario para microemprendimientos locales",
    "project_type": "agent-assisted-sdlc"
  },
  "mode": "dry-run",
  "steps": [
    {"step_id": "workspace-plan", "status": "pass", "mutations_performed": false},
    {"step_id": "docs-template-plan", "status": "pass", "mutations_performed": false},
    {"step_id": "miasi-template-plan", "status": "pass", "mutations_performed": false},
    {"step_id": "readiness-preview", "status": "warning", "mutations_performed": false}
  ],
  "safety": {
    "network_used": false,
    "external_api_used": false,
    "remote_execution_used": false,
    "connector_write_used": false,
    "plugin_execution_used": false,
    "secrets_included": false
  }
}
```

## 7. Principios

```text
1. Idea-to-readiness: guiar desde idea inicial hasta readiness, no solo crear carpetas.
2. Dry-run-first: bootstrap muestra plan antes de escribir.
3. Templates as documentation: plantillas versionadas, no prompts sueltos.
4. No magic code generation: el playbook guía, no reemplaza ingeniería.
5. MIASI-ready: todo proyecto agent-assisted debe incluir registries básicos.
6. Operator-safe: comandos explícitos y criterios PASS/BLOCK.
```

## 8. Micro-sprints propuestos

### POST-H-024-A — Playbook de operador

Estado: `implemented-initial`.

Tareas:

```text
1. [x] Crear docs/05_operations/operator_onboarding_playbook.md.
2. [x] Incluir flujo idea → workspace → docs → readiness → backlog.
3. [x] Incluir ejemplo ventas/inventario microemprendimientos.
4. [x] Incluir comandos CLI reales.
5. [x] Definir errores frecuentes y criterios BLOCK.
```

PASS:

```text
PASS si un operador puede seguir el playbook sin conversación previa.
PASS si contiene local-first/dry-run/no-remote como reglas explícitas.
```

### POST-H-024-B — Templates de proyecto nuevo

Estado: `implemented-initial`.

Tareas:

```text
1. [x] Crear templates Markdown para producto, requisitos, arquitectura, seguridad y calidad.
2. [x] Crear templates JSON para MIASI registries mínimos.
3. [x] Agregar frontmatter compatible.
4. [x] Crear tests de validez de templates.
```

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
tests/test_post_h_024_project_templates.py
```

Límite: `implemented-initial / templates-only`; no implementa todavía `workspace bootstrap`, `project_bootstrap_report.json`, readiness preview ni quality gate de onboarding.

PASS:

```text
PASS si templates Markdown pasan validate-frontmatter.
PASS si templates MIASI son estructuralmente válidos.
PASS si no contienen secretos ni vendor lock-in.
```

### POST-H-024-C — Bootstrap workflow dry-run

Tareas:

```text
1. Implementar workspace/bootstrap.py.
2. Generar plan de archivos a crear.
3. Soportar --dry-run y --execute con límites.
4. Producir project_bootstrap_report.json.
5. No sobrescribir archivos existentes por defecto.
```

PASS:

```text
PASS si dry-run no muta.
PASS si execute rechaza overwrite por defecto.
PASS si reporta comandos siguientes.
```

BLOCK:

```text
BLOCK si el bootstrap escribe fuera del workspace.
BLOCK si habilita APIs externas.
BLOCK si crea secrets reales.
```

### POST-H-024-D — Onboarding validation y readiness preview

Tareas:

```text
1. Integrar validadores frontmatter/artifact/checklist/readiness.
2. Agregar readiness preview para proyecto nuevo.
3. Generar lista de pendientes por fase.
4. Integrar StandardsRegistry y MIASI validate.
```

PASS:

```text
PASS si el operador ve qué falta para readiness.
PASS si MIASI faltante se reporta como pendiente, no como success.
```

### POST-H-024-E — Quality gate y proyecto piloto fixture

Tareas:

```text
1. Crear fixture de proyecto piloto mínimo.
2. Crear tests del bootstrap contra fixture temporal.
3. Agregar subgate onboarding-bootstrap-ready.
4. Actualizar runbook y test contract registry.
```

PASS:

```text
PASS si el bootstrap genera un proyecto temporal válido en dry-run.
PASS si quality gate detecta ausencia de templates.
PASS si no se crean runtime artifacts versionables.
```

## 9. Comandos esperados

```powershell
python -m devpilot_core onboarding playbook --json
python -m devpilot_core workspace bootstrap --project-id ventas-micro-local --project-name "Sistema agent-assisted de ventas e inventario para microemprendimientos locales" --dry-run --json --write-report
python -m devpilot_core workspace bootstrap --project-id ventas-micro-local --project-name "Sistema agent-assisted de ventas e inventario para microemprendimientos locales" --execute --json
python -m pytest tests/test_post_h_024_operator_onboarding.py -q
python -m pytest tests/test_post_h_024_project_bootstrap.py -q
python -m devpilot_core quality-gate run --profile hardening --json
```

## 10. Criterios BLOCK

```text
BLOCK si el playbook requiere conocimiento no documentado.
BLOCK si templates no pasan validadores.
BLOCK si bootstrap usa red o APIs externas.
BLOCK si bootstrap escribe fuera del workspace.
BLOCK si execute sobrescribe archivos sin confirmación/política.
BLOCK si se omite MIASI en proyectos agent-assisted.
```

## 11. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Onboarding conversacional no reproducible | Alta | Playbook versionado y templates. |
| Bootstrap demasiado mágico | Alta | Plan-first y no code generation. |
| Plantillas obsoletas | Media-alta | Documentation governance en POST-H-009. |
| Sobrescritura de proyectos | Alta | Refuse overwrite by default. |
| Falsa readiness | Alta | Readiness preview y criterios BLOCK. |

## 12. Definition of Done

```text
[x] Playbook aprobado.
[x] Templates Markdown y JSON creados.
[ ] Bootstrap dry-run implementado.
[ ] Reporte bootstrap validable.
[ ] Fixture piloto cubierto por tests.
[ ] Quality gate integrado.
[ ] Runbook actualizado.
```
