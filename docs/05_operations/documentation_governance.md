---
doc_id: "DEVPL-OPS-DOCS-GOVERNANCE-001"
title: "Documentation governance y fuentes canónicas"
status: "approved"
version: "1.0.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
micro_sprint: "POST-H-009-E"
local_first: true
dry_run: true
no_remote_execution_enabled: true
---

# Documentation governance y fuentes canónicas

## 1. Propósito

Este documento describe la primera versión ejecutable de la gobernanza documental de DevPilot Local, ampliada hasta `POST-H-009-E — Quality gate documental y runbook`.

La meta es separar explícitamente:

```text
- fuentes canónicas humanas;
- fuentes machine-readable;
- documentos derivados;
- evidencia histórica;
- reportes runtime generados;
- reglas de sincronización ejecutables para pares Markdown ↔ JSON críticos;
- governance determinística de backlogs ejecutables derivados del roadmap.
```

## 2. Registry canónico

El registry versionado es:

```text
.devpilot/docs_governance/source_registry.json
```

Este archivo es fuente controlada por Git. No es runtime state y no debe contener secretos. Registra documentos críticos como roadmap, manifest, closure report, ADRs, runbook, changelog, README, project_state, test contract registries y backlogs ejecutables POST-H-002..POST-H-025 derivados del roadmap.

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
python -m pytest tests/test_documentation_source_registry_schema.py tests/test_documentation_governance_validator.py tests/test_documentation_governance_sync.py tests/test_documentation_governance_backlogs.py tests/test_post_h_009_documentation_governance.py -q
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

`POST-H-009-C` agrega drift checks Markdown ↔ JSON para roadmap, decisiones, cierre y siguiente hito; `POST-H-009-D` agrega governance de backlogs derivados del roadmap. El mismo comando conserva las validaciones de metadata de `POST-H-009-B`.


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


## 4.3. Backlog governance y derivados del roadmap

`POST-H-009-D` gobierna los backlogs ejecutables declarados en `.devpilot/evals/post_h_eval_001_prioritized_roadmap.json` bajo `executable_backlogs_to_create`. El scope actual cubre `POST-H-002..POST-H-025`.

Reglas determinísticas:

```text
- cada backlog del roadmap JSON debe estar registrado en `.devpilot/docs_governance/source_registry.json`;
- cada backlog existente debe cumplir `docs/backlogs/POST-H-###_<slug>.md`;
- cada backlog existente debe declarar frontmatter mínimo: doc_id, id, title, status, version, owner, updated, priority y roadmap_source;
- doc_id debe seguir `POST-H-###-BACKLOG`;
- id y priority deben coincidir con el roadmap machine-readable;
- roadmap_source debe apuntar a `docs/backlogs/post_h_prioritized_roadmap.md`;
- un backlog futuro faltante se reporta como `DOCUMENTATION_BACKLOG_PLANNED_MISSING` informativo, no como bloqueo.
```

La validación emite `backlog_checks` dentro de `DocumentationGovernanceReport` y expone métricas como `backlogs_expected_total`, `backlogs_registered_total`, `backlogs_checked_total`, `backlogs_planned_missing_total` y `backlog_governance_passed`.


## 4.4. Quality gate documental y proceso anti-drift

`POST-H-009-E` integra la gobernanza documental al proceso normal de desarrollo mediante el subgate `docs-governance` en los perfiles `hardening` e `industrial` del quality gate. La integración reusa `DocumentationGovernanceValidator` como fuente única de verdad y lo ejecuta con `write_report=false`.

Comando de verificación operacional:

```powershell
python -m devpilot_core quality-gate run --profile hardening --json
```

El subgate debe exponer en su summary:

```text
quality_gate_subgate=docs-governance
docs_governance_passed=true
frontmatter_status_ownership_passed=true
markdown_json_sync_passed=true
roadmap_markdown_json_sync_passed=true
backlog_governance_passed=true
blocking_findings_total=0
read_only=true
dry_run=true
network_used=false
external_api_used=false
llm_judge_used=false
source_mutations_performed=false
```

### Procedimiento para actualizar fuentes canónicas

1. Identificar la fuente de autoridad en `.devpilot/docs_governance/source_registry.json`.
2. Actualizar primero el source-of-truth humano o machine-readable correspondiente.
3. Si existe counterpart Markdown/JSON, actualizar ambos en la misma unidad de cambio.
4. Ejecutar `docs-governance validate --json` antes de tocar README, runbook o changelog.
5. Actualizar `README.md`, `docs/05_operations/runbook.md`, `docs/release/CHANGELOG.md` y `.devpilot/project_state.json` solo después de confirmar el nuevo estado.
6. Ejecutar `quality-gate run --profile hardening --json` como checkpoint de cierre.
7. Generar reporte con `docs-governance report --write-report --json` únicamente cuando se requiera evidencia versionable o audit pack; los reportes runtime bajo `outputs/` no se versionan.

### Cómo cambiar roadmap sin drift

```text
1. Editar docs/backlogs/post_h_prioritized_roadmap.md.
2. Editar .devpilot/evals/post_h_eval_001_prioritized_roadmap.json.
3. Confirmar version_match, milestones_match y decisions_match.
4. Si se agrega hito POST-H nuevo, crear/actualizar backlog ejecutable o registrarlo como planned.
5. Ejecutar docs-governance validate y quality-gate hardening.
```

### Cómo cambiar ADRs sin drift

```text
1. Crear o actualizar docs/adr/ADR-POSTH-###-*.md con frontmatter approved/draft explícito.
2. Registrar el ADR en source_registry si se convierte en decisión activa.
3. Vincular la decisión desde roadmap o backlog cuando aplique.
4. Ejecutar docs-governance validate y test-contracts validate-v2.
```

### Cómo cambiar manifest/closure/changelog sin drift

```text
1. Actualizar manifest JSON del hito o micro-sprint.
2. Actualizar closure/audit report si el estado cambia a closed.
3. Actualizar README, runbook, changelog y project_state en la misma unidad de cambio.
4. Validar schema del manifest y ejecutar docs-governance validate.
5. Confirmar quality-gate hardening PASS.
```

## 5. Límites de esta versión

`POST-H-009-E` deja el hito `POST-H-009` en estado `closed` como implementación inicial. Límites explícitos:

```text
- no evalúa suficiencia editorial o semántica profunda mediante LLM judge;
- no publica documentación externa ni implementa CMS/wiki remota;
- no corrige automáticamente drift; bloquea o informa para que el cambio sea corregido por el owner;
- no habilita red, APIs externas, remote execution, connector write ni plugin execution;
- no declara DevPilot production-ready; esa declaración queda para POST-H-025.
```

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
