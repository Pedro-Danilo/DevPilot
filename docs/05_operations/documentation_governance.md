---
doc_id: "DEVPL-OPS-DOCS-GOVERNANCE-001"
title: "Documentation governance y fuentes canónicas"
status: "approved"
version: "0.1.0"
owner: "Ordóñez"
updated: "2026-06-26"
phase: "POST-FASE-H"
micro_sprint: "POST-H-009-A"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# Documentation governance y fuentes canónicas

## 1. Propósito

Este documento describe la primera versión de la gobernanza documental de DevPilot Local, implementada en `POST-H-009-A — Source registry y schema`.

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

`DocumentationSourceRegistry` valida el registry inicial. `DocumentationGovernanceReport` queda registrado para los micro-sprints posteriores que implementarán validator, sync checker y quality gate.

## 4. Comandos de verificación actuales

```powershell
python -m devpilot_core schema validate --schema-id DocumentationSourceRegistry --instance .devpilot/docs_governance/source_registry.json --json
python -m devpilot_core schema list --json
python -m pytest tests/test_documentation_source_registry_schema.py tests/test_post_h_009_documentation_governance.py -q
```

## 5. Límites de esta versión

`POST-H-009-A` es `implemented-initial`. Aún no implementa:

```text
- comando docs-governance validate;
- parser de frontmatter/status/ownership;
- detección ejecutable de drift Markdown ↔ JSON;
- governance de todos los backlogs derivados;
- subgate docs-governance en quality-gate hardening.
```

Estas capacidades se implementarán en `POST-H-009-B` a `POST-H-009-E`.

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
