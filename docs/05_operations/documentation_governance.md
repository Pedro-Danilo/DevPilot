---
doc_id: "DEVPL-OPS-DOCS-GOVERNANCE-001"
title: "Documentation governance y fuentes canónicas"
status: "approved"
version: "0.2.0"
owner: "Ordóñez"
updated: "2026-06-26"
phase: "POST-FASE-H"
micro_sprint: "POST-H-009-B"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# Documentation governance y fuentes canónicas

## 1. Propósito

Este documento describe la primera versión ejecutable de la gobernanza documental de DevPilot Local, ampliada en `POST-H-009-B — Validator de frontmatter/status/ownership`.

La meta es separar explícitamente:

```text
- fuentes canónicas humanas;
- fuentes machine-readable;
- documentos derivados;
- evidencia histórica;
- reportes runtime generados;
- reglas de sincronización pendientes de validación ejecutable.
```

## 2. Registry canónico

El registry versionado es:

```text
.devpilot/docs_governance/source_registry.json
```

Este archivo es fuente controlada por Git. No es runtime state y no debe contener secretos. Registra documentos críticos como roadmap, manifest, closure report, ADRs, runbook, changelog, README, project_state y test contract registries.

## 3. Schemas

```text
docs/schemas/documentation_source_registry.schema.json
docs/schemas/documentation_governance_report.schema.json
```

`DocumentationSourceRegistry` valida el registry inicial. `DocumentationGovernanceReport` valida el reporte producido por `docs-governance validate --write-report`.

## 4. Comandos de verificación actuales

```powershell
python -m devpilot_core schema validate --schema-id DocumentationSourceRegistry --instance .devpilot/docs_governance/source_registry.json --json
python -m devpilot_core docs-governance validate --json
python -m devpilot_core docs-governance validate --write-report --json
python -m devpilot_core schema validate --schema-id DocumentationGovernanceReport --instance outputs/reports/documentation_governance_report.json --json
python -m pytest tests/test_documentation_source_registry_schema.py tests/test_documentation_governance_validator.py tests/test_post_h_009_documentation_governance.py -q
```

## 4.1. Validator `docs-governance validate`

`POST-H-009-B` implementa un validator determinístico que verifica:

```text
- existencia de cada path registrado;
- owner y status_required obligatorios;
- frontmatter obligatorio para documentos Markdown con status_required=approved;
- consistencia de doc_id entre registry y frontmatter;
- consistencia de status cuando el archivo expone status;
- existencia de tests requeridos para fuentes críticas/source-of-truth;
- clasificación historical sin promover evidencia histórica como autoridad actual no declarada.
```

El comando no calcula todavía drift Markdown ↔ JSON; esa capa corresponde a `POST-H-009-C`.

## 5. Límites de esta versión

`POST-H-009-B` es `implemented-initial`. Aún no implementa:

```text
- detección ejecutable de drift Markdown ↔ JSON;
- governance de todos los backlogs derivados;
- subgate docs-governance en quality-gate hardening.
```

Estas capacidades se implementarán en `POST-H-009-C` a `POST-H-009-E`.

## 6. Seguridad y operación

```text
- local_first=true;
- dry_run=true;
- no usa red ni APIs externas;
- no usa LLM judge;
- no modifica archivos en validación;
- no habilita remote execution, connector write ni plugin execution.
```

## 7. Riesgos controlados

| Riesgo | Control inicial |
|---|---|
| Drift entre roadmap MD y JSON | Pair explícito en registry. |
| Source-of-truth sin test | Regla `source_of_truth_requires_tests`. |
| README/project_state desincronizados | Regla `next_hito_match`. |
| ADRs activas sin vínculo | Regla `adr_linked`. |
| Reportes runtime versionados como documentación | Clasificación separada `generated-runtime`. |
