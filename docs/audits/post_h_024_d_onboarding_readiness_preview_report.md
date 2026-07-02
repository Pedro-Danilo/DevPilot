---
doc_id: "POST-H-024-D-ONBOARDING-READINESS-PREVIEW-REPORT"
title: "POST-H-024-D — Onboarding validation y readiness preview"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-07-02"
approval: "approved_by_owner"
phase: "POST-FASE-H"
created_by: "POST-H-024-D"
implementation_status: "implemented-initial"
preliminary: true
local_first: true
dry_run: true
read_only: true
no_external_apis_used: true
no_remote_execution_enabled: true
no_connector_write_enabled: true
no_plugin_execution_enabled: true
---

# POST-H-024-D — Onboarding validation y readiness preview

## 1. Objetivo

Implementar una vista previa reproducible de readiness para proyectos nuevos creados o planificados con POST-H-024-B/C, sin declarar falsamente que el proyecto está listo. El preview transforma el flujo conversacional de onboarding en evidencia verificable, local-first y trazable.

## 2. Alcance implementado

POST-H-024-D agrega el comando:

```powershell
python -m devpilot_core workspace readiness-preview --target-root <workspace> --json --write-report
```

El preview evalúa, de forma read-only:

```text
- existencia del workspace y .devpilot/project.yaml;
- frontmatter y artifact validator para documentos starter;
- checklist pre-code cuando exista;
- StandardsRegistry local;
- presencia y validez estructural de MIASI registries;
- MIASI semantic validator sobre el workspace objetivo;
- readiness estricto existente;
- pendientes por fase y próximos comandos.
```

## 3. Ajuste industrial aplicado

El backlog pedía integrar frontmatter/artifact/checklist/readiness, StandardsRegistry y MIASI validate. En vez de declarar readiness binario, se implementó un **preview con estado `warning` cuando hay pendientes**. Esto evita la falsa madurez: MIASI ausente, checklist pendiente o readiness incompleto se reportan como `pending`, no como `success`.

## 4. Artefactos principales

```text
src/devpilot_core/onboarding/readiness_preview.py
docs/schemas/onboarding_readiness_preview_report.schema.json
docs/post_h_024_d_manifest.json
tests/test_post_h_024_onboarding_readiness_preview.py
```

## 5. Seguridad operacional

```text
network_used=false
external_api_used=false
remote_execution_used=false
connector_write_used=false
plugin_execution_used=false
secrets_included=false
mutations_performed=false
source_mutations_performed=false
```

El único write opcional permitido es el reporte bajo `outputs/` cuando se usa `--write-report`.

## 6. Criterios PASS cubiertos

```text
PASS: el operador ve qué falta para readiness.
PASS: MIASI faltante se reporta como pendiente, no como success.
PASS: el reporte OnboardingReadinessPreviewReport valida contra schema.
PASS: el comando no ejecuta red, APIs externas, conectores write, plugins ni remote execution.
```

## 7. Límites explícitos

POST-H-024-D es `implemented-initial / readiness-preview-only`. No crea fixture piloto final, no activa subgate de quality gate y no declara `production-ready-local`. Eso queda para POST-H-024-E.
