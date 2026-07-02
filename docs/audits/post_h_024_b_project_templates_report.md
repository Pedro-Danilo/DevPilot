---
doc_id: "POST-H-024-B-PROJECT-TEMPLATES-REPORT"
title: "POST-H-024-B — Templates de proyecto nuevo"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-024-B"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
no_remote_execution_enabled: true
no_external_apis_used: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-024-B — Templates de proyecto nuevo

## 1. Resultado

POST-H-024-B agrega una primera versión versionada y verificable de templates para proyectos nuevos. El alcance implementado cubre los entregables de documentación pre-code y registries MIASI mínimos definidos para el micro-sprint.

## 2. Artefactos creados

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
src/devpilot_core/onboarding/__init__.py
src/devpilot_core/onboarding/templates.py
tests/test_post_h_024_project_templates.py
```

## 3. Ajuste de alcance aplicado

El backlog global lista `src/devpilot_core/onboarding/templates.py` como entregable del hito. Para nivel industrial, POST-H-024-B no debe limitarse a archivos sueltos; por eso se agregó un módulo read-only de catálogo/validación de templates.

Este módulo no implementa bootstrap, no escribe workspaces, no genera código y no habilita CLI nueva. La creación efectiva de archivos de proyecto queda para POST-H-024-C.

## 4. Validaciones cubiertas

```text
- Frontmatter estricto en templates Markdown.
- Validez estructural de templates MIASI contra schemas existentes.
- Escaneo conservador contra secretos/API keys conocidas.
- Verificación de ausencia de vendor lock-in como dependencia base.
- Registro en source_registry y TCR v1/v2.
```

## 5. Límites explícitos

```text
bootstrap_workflow_available=false
project_bootstrap_report_available=false
readiness_preview_available=false
onboarding_quality_gate_available=false
network_used=false
external_api_used=false
remote_execution_enabled=false
connector_write_enabled=false
plugin_execution_enabled=false
```

## 6. Riesgos pendientes

```text
- Las plantillas son primera versión; deberán evolucionar al probarse contra proyectos piloto reales.
- Aún no existe comando `workspace bootstrap` para materializar estos templates.
- Aún no existe readiness preview automatizado sobre proyectos generados.
- La validación semántica profunda de contenido queda para POST-H-024-D/E.
```
