---
doc_id: "DEVPL-OPS-DOCS-GOVERNANCE-001"
title: "Documentation governance y fuentes canónicas"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-009-C"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# Documentation governance y fuentes canónicas

## 1. Propósito

Este documento describe la primera versión ejecutable de la gobernanza documental de DevPilot Local, ampliada hasta `POST-H-009-C — Sync validator Markdown ↔ JSON`.

La meta es separar explícitamente:

```text
- fuentes canónicas humanas;
- fuentes machine-readable;
- documentos derivados;
- evidencia histórica;
- reportes runtime generados;
- reglas de sincronización ejecutables para pares Markdown ↔ JSON críticos.
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
python -m pytest tests/test_documentation_source_registry_schema.py tests/test_documentation_governance_validator.py tests/test_documentation_governance_sync.py tests/test_post_h_009_documentation_governance.py -q
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

`POST-H-009-C` agrega drift checks Markdown ↔ JSON para roadmap, decisiones, cierre y siguiente hito; el mismo comando conserva las validaciones de metadata de `POST-H-009-B`.


## 4.2. Sync validator Markdown ↔ JSON

`POST-H-009-C` ejecuta estas reglas determinísticas:

```text
- version_match para `docs/backlogs/post_h_prioritized_roadmap.md` ↔ `.devpilot/evals/post_h_eval_001_prioritized_roadmap.json`;
- milestones_match para hitos `POST-H-002..POST-H-025`, incluyendo `POST-H-024` y `POST-H-025`;
- decisions_match para `DEC-POSTH-*`, incluyendo `DEC-POSTH-008` y `DEC-POSTH-009`;
- closure_status_match entre `docs/post_h_eval_001_manifest.json` y `docs/audits/post_h_eval_001_closure_report.md`;
- next_hito_match entre `.devpilot/project_state.json` y README/runbook/changelog.
```

El reporte identifica `source_path`, `counterpart_path`, regla evaluada, totales comparados y faltantes por lado.

## 5. Límites de esta versión

`POST-H-009-C` es `implemented-initial`. Aún no implementa:

```text
- governance de todos los backlogs derivados;
- subgate docs-governance en quality-gate hardening.
```

Estas capacidades se implementarán en `POST-H-009-D` y `POST-H-009-E`.

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
