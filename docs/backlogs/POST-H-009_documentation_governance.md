---
doc_id: "POST-H-009-BACKLOG"
id: "POST-H-009"
title: "POST-H-009 — Documentation governance y canonical sources"
status: "approved"
version: "0.3.0"
owner: "Ordóñez"
updated: "2026-06-26"
approval: "approved_by_owner"
phase: "POST-FASE-H"
priority: "P1"
roadmap_source: "docs/backlogs/post_h_prioritized_roadmap.md"
local_first: true
dry_run: true
no_runtime_features_added_by_backlog: false
no_remote_execution_enabled: true
implementation_status: "in-progress"
current_micro_sprint: "POST-H-009-C"
next_micro_sprint: "POST-H-009-D"
---

# POST-H-009 — Documentation governance y canonical sources

## 1. Objetivo

Implementar un sistema local de **gobernanza documental y fuentes canónicas** para DevPilot, de forma que documentos, manifests, roadmaps, ADRs, reports y artefactos machine-readable mantengan trazabilidad, ownership, sincronización y criterios claros de autoridad.

El objetivo es evitar drift documental y resolver una tensión actual: DevPilot tiene mucha documentación útil, pero no todo documento tiene la misma autoridad ni todos los datos deben actualizarse manualmente en varios lugares.

## 2. Contexto y justificación

El onboarding, reverse engineering y cierre post-H evidenciaron que DevPilot depende fuertemente de documentación viva:

```text
docs/audits/
docs/backlogs/
docs/adr/
docs/02_architecture/
docs/03_security/
docs/04_quality/
docs/05_operations/
docs/release/
.devpilot/evals/*.json
.devpilot/testing/test_contract_registry.json
docs/post_h_eval_001_manifest.json
```

Esto es una fortaleza, pero también un riesgo. Sin gobernanza documental, pueden aparecer inconsistencias como:

```text
- Roadmap Markdown actualizado pero JSON machine-readable desfasado.
- README apuntando a un hito anterior.
- ADRs no enlazadas desde roadmap.
- Manifest cerrado pero changelog no sincronizado.
- Risk register sin vínculo a roadmap.
- Backlogs derivados no registrados como fuente esperada.
- Informes de onboarding no incorporados a playbooks o fuentes canónicas.
```

Este hito crea un registry explícito de fuentes canónicas y documentos derivados.

## 3. Alcance

Incluye:

```text
- Documentation Source Registry.
- Clasificación source-of-truth vs derived vs generated vs historical.
- Validador de consistencia documental.
- Reglas de sincronización entre Markdown y JSON.
- Reporte de drift documental.
- Mapping docs ↔ tests ↔ roadmap ↔ ADRs.
- Integración con backlogs ejecutables y onboarding.
```

No incluye:

```text
- Reescritura completa de todos los documentos.
- LLM judge para validar calidad documental.
- Publicación externa de docs.
- CMS.
- Wiki remota.
- Generación automática masiva de documentación.
```

## 4. Fuentes de entrada obligatorias

```text
README.md
docs/backlogs/post_h_prioritized_roadmap.md
.devpilot/evals/post_h_eval_001_prioritized_roadmap.json
docs/post_h_eval_001_manifest.json
docs/audits/post_h_eval_001_closure_report.md
docs/release/CHANGELOG.md
docs/05_operations/runbook.md
docs/adr/ADR-POSTH-001-local-first-before-remote.md
docs/adr/ADR-POSTH-002-test-contract-registry-2.md
docs/adr/ADR-POSTH-003-cli-modularization.md
.devpilot/project_state.json
.devpilot/testing/test_contract_registry.json
```

## 5. Entregables

```text
src/devpilot_core/docs_governance/models.py
src/devpilot_core/docs_governance/registry.py
src/devpilot_core/docs_governance/validator.py
src/devpilot_core/docs_governance/drift.py
src/devpilot_core/docs_governance/report.py
src/devpilot_core/docs_governance/__init__.py
.devpilot/docs_governance/source_registry.json
docs/schemas/documentation_source_registry.schema.json
docs/schemas/documentation_governance_report.schema.json
docs/05_operations/documentation_governance.md
outputs/reports/documentation_governance_report.json     # generado, no versionar
outputs/reports/documentation_governance_report.md       # generado, no versionar
tests/test_post_h_009_documentation_governance.py
tests/test_documentation_source_registry_schema.py
```

## 6. Modelo de datos mínimo

```json
{
  "schema_version": "1.0",
  "registry_id": "devpilot-documentation-source-registry",
  "documents": [
    {
      "doc_id": "POSTH-ROADMAP-001",
      "path": "docs/backlogs/post_h_prioritized_roadmap.md",
      "classification": "source-of-truth",
      "domain": "roadmap",
      "owner": "Ordóñez",
      "status_required": "approved",
      "machine_readable_counterparts": [
        ".devpilot/evals/post_h_eval_001_prioritized_roadmap.json"
      ],
      "derived_documents": [
        "docs/backlogs/POST-H-002_maturity_dashboard_local.md"
      ],
      "required_tests": [
        "tests/test_post_h_eval_001_f_prioritized_roadmap.py"
      ],
      "sync_rules": [
        "version_match",
        "milestones_match",
        "decisions_match"
      ]
    }
  ],
  "rules": {
    "approved_docs_require_frontmatter": true,
    "source_of_truth_requires_tests": true,
    "markdown_json_pairs_require_sync": true
  }
}
```

## 7. Clasificación documental

| Clasificación | Significado | Ejemplos |
|---|---|---|
| `source-of-truth` | Documento o JSON canónico para decisiones actuales. | Roadmap, manifest, project_state, ADRs vigentes. |
| `machine-readable-source` | JSON canónico consumido por comandos/gates. | `.devpilot/evals/*.json`, registries. |
| `derived` | Documento generado o derivado de una fuente. | Backlogs ejecutables, reportes consolidados. |
| `generated-runtime` | Reporte generado por comandos. | `outputs/reports/*`. |
| `historical` | Evidencia histórica no editable salvo corrección formal. | Manifests de sprints cerrados. |
| `deprecated` | Documento obsoleto con reemplazo explícito. | Backlogs superados. |

## 8. Reglas iniciales de sincronización

```text
version_match:
  La versión del Markdown y su JSON counterpart deben coincidir cuando ambos declaran version.

milestones_match:
  Los hitos listados en roadmap Markdown deben existir en roadmap JSON.

decisions_match:
  Las decisiones DEC-POSTH-* deben existir en Markdown y JSON cuando sean machine-readable.

closure_status_match:
  Manifest, closure report, README y changelog no deben contradecir el estado de hito cerrado.

next_hito_match:
  README, project_state, changelog y roadmap deben apuntar al mismo siguiente hito cuando aplique.

adr_linked:
  Toda decisión arquitectónica activa debe estar vinculada a un ADR o a una decisión formal de roadmap.
```

## 9. Micro-sprints propuestos

### POST-H-009-A — Source registry y schema

Objetivo: crear registry documental canónico.

Tareas:

```text
1. Crear documentation_source_registry.schema.json.
2. Crear documentation_governance_report.schema.json.
3. Registrar schemas.
4. Crear .devpilot/docs_governance/source_registry.json.
5. Incluir roadmap, manifest, closure report, ADRs, runbook, changelog, project_state y test_contract_registry.
```

Criterios PASS:

```text
PASS si el registry valida contra schema.
PASS si todo source-of-truth tiene owner, status_required y required_tests.
PASS si markdown/json pairs están declarados.
```

Criterios BLOCK:

```text
BLOCK si un source-of-truth crítico queda sin test.
BLOCK si roadmap JSON no queda vinculado a roadmap Markdown.
```

### POST-H-009-B — Validator de frontmatter/status/ownership

Objetivo: validar metadata documental mínima por clasificación.

Tareas:

```text
1. Reutilizar FrontmatterValidator.
2. Validar status requerido según registry.
3. Validar owner obligatorio.
4. Validar doc_id consistente.
5. Validar existencia de tests requeridos.
```

Comando propuesto:

```powershell
python -m devpilot_core docs-governance validate --json
```

Criterios PASS:

```text
PASS si docs approved tienen frontmatter válido.
PASS si source-of-truth críticos tienen tests.
PASS si historical docs no se tratan como fuentes actuales salvo registry.
```

### POST-H-009-C — Sync validator Markdown ↔ JSON

Objetivo: detectar drift entre documentos humanos y artefactos machine-readable.

Tareas:

```text
1. Implementar reglas version_match, milestones_match, decisions_match.
2. Validar post_h_prioritized_roadmap.md vs post_h_eval_001_prioritized_roadmap.json.
3. Validar manifest/closure/changelog/project_state.
4. Emitir findings con severidad warning/block.
5. Generar reporte JSON/Markdown.
```

Criterios PASS:

```text
PASS si POST-H-024 y POST-H-025 aparecen sincronizados en roadmap MD/JSON.
PASS si DEC-POSTH-008 y DEC-POSTH-009 aparecen sincronizadas.
PASS si el reporte identifica fuente y counterpart.
```

Criterios BLOCK:

```text
BLOCK si roadmap MD y JSON difieren en hitos críticos.
BLOCK si un hito cerrado no coincide entre manifest y closure report.
```

### POST-H-009-D — Backlog governance y derivados del roadmap

Objetivo: gobernar los backlogs ejecutables derivados del roadmap.

Tareas:

```text
1. Registrar backlogs POST-H-002..POST-H-025 como derived/planned.
2. Validar naming convention.
3. Validar frontmatter mínimo de cada backlog.
4. Validar correspondencia backlog ↔ milestone del roadmap.
5. Reportar backlogs faltantes por fase.
```

Criterios PASS:

```text
PASS si cada backlog elaborado tiene doc_id, id, title, priority y roadmap_source.
PASS si no hay backlog para hito inexistente.
PASS si faltantes se reportan como planned, no como error si aún no elaborados.
```

### POST-H-009-E — Quality gate documental y runbook

Objetivo: integrar governance documental al proceso de desarrollo.

Tareas:

```text
1. Agregar subgate docs-governance al quality gate o comando validate all.
2. Registrar test contract.
3. Documentar proceso de actualización de docs canónicos.
4. Documentar cómo cambiar roadmap/ADR/manifest sin drift.
5. Actualizar runbook.
```

Criterios PASS:

```text
PASS si docs-governance validate pasa en baseline válido.
PASS si quality-gate hardening sigue PASS.
PASS si test-contracts validate pasa.
```

## 10. Comandos de validación final

```powershell
$env:PYTHONPATH="src"

python -m pytest tests/test_post_h_009_documentation_governance.py -q
python -m pytest tests/test_documentation_source_registry_schema.py tests/test_schema_registry.py -q
python -m devpilot_core docs-governance validate --json
python -m devpilot_core docs-governance report --write-report --json
python -m devpilot_core validate docs --json
python -m devpilot_core test-contracts validate --json
python -m devpilot_core quality-gate run --profile hardening --json
```

## 11. Riesgos

| Riesgo | Severidad | Mitigación |
|---|---:|---|
| Sobrecargar documentación con burocracia | Media | Registry mínimo y automatizado. |
| Falsos positivos por parsing Markdown | Media | Reglas canónicas simples y explícitas. |
| Duplicar verdad entre MD y JSON | Alta | Declarar source-of-truth y counterpart. |
| Romper históricos | Media | Clasificación historical; no editar sin razón. |
| Convertir docs en requisito superficial | Media | Conectar docs a tests y roadmap. |

## 12. No-go gates

```text
NO-GO si se actualiza roadmap Markdown sin JSON counterpart cuando aplica.
NO-GO si se declara hito cerrado sin manifest/closure/changelog coherentes.
NO-GO si un source-of-truth crítico queda sin test asociado.
NO-GO si se elimina evidencia histórica para reducir warnings.
NO-GO si se usa LLM para decidir PASS/BLOCK documental sin regla determinística.
```

## 13. Entregable verificable

```text
Documentation Source Registry validable.
Validator docs-governance.
Reporte de drift documental.
Governance de backlogs derivados del roadmap.
Runbook actualizado.
Tests focales PASS.
Quality gate hardening PASS.
```


## 14. Avance de implementación — POST-H-009-A

Estado: `implemented-initial`.

`POST-H-009-A — Source registry y schema` eleva este backlog a `approved` e introduce la primera fuente canónica versionada de gobernanza documental:

```text
.devpilot/docs_governance/source_registry.json
docs/schemas/documentation_source_registry.schema.json
docs/schemas/documentation_governance_report.schema.json
src/devpilot_core/docs_governance/
tests/test_documentation_source_registry_schema.py
tests/test_post_h_009_documentation_governance.py
```

Capacidades implementadas:

```text
- Clasificación inicial de documentos source-of-truth, machine-readable-source y derived.
- Registro explícito de roadmap Markdown y JSON counterpart.
- Registro de manifest, closure report, ADRs, runbook, changelog, project_state y test contract registries.
- Reglas iniciales: source_of_truth_requires_tests, markdown_json_pairs_require_sync, next_hito_match, closure_status_match y adr_linked.
- Schemas DocumentationSourceRegistry y DocumentationGovernanceReport registrados en schema_catalog.
- Contratos TCR v1/v2 para el registry canónico.
```

Límites de esta versión:

```text
- No ejecuta todavía validación CLI `docs-governance validate`.
- No calcula drift Markdown ↔ JSON.
- No integra aún subgate `docs-governance` al `quality-gate hardening`.
- No usa LLM judge ni servicios externos.
```

Estas capacidades quedan para `POST-H-009-B`, `POST-H-009-C`, `POST-H-009-D` y `POST-H-009-E`.


## 15. Avance de implementación — POST-H-009-B

Estado: `implemented-initial`.

`POST-H-009-B — Validator de frontmatter/status/ownership` agrega el primer validator ejecutable de gobernanza documental:

```text
python -m devpilot_core docs-governance validate --json
python -m devpilot_core docs-governance validate --write-report --json
```

Artefactos implementados:

```text
src/devpilot_core/docs_governance/validator.py
src/devpilot_core/docs_governance/report.py
tests/test_documentation_governance_validator.py
docs/audits/post_h_009_b_documentation_governance_validator_report.md
docs/post_h_009_b_manifest.json
```

Capacidades implementadas:

```text
- Valida existencia de fuentes declaradas en `.devpilot/docs_governance/source_registry.json`.
- Valida owner y status_required obligatorios por documento registrado.
- Reutiliza el parser/validator de frontmatter para documentos Markdown approved.
- Valida doc_id de frontmatter contra doc_id del registry.
- Valida status de frontmatter o JSON cuando el documento expone status.
- Valida required_tests existentes para documentos críticos/source-of-truth.
- Genera `DocumentationGovernanceReport` JSON/Markdown bajo `outputs/reports` solo con `--write-report`.
- Registra contrato TCR v1/v2 para el validator.
```

Inconsistencia heredada corregida:

```text
- El backlog POST-H-009 estaba approved pero no declaraba `approval` en frontmatter. Se agregó `approval: "approved_by_owner"` tanto en `docs/backlogs/POST-H-009_documentation_governance.md` como en su espejo `docs/POST-H-009_documentation_governance.md` para evitar warning documental.
```

Límites de esta versión:

```text
- No implementa todavía drift Markdown ↔ JSON; queda para POST-H-009-C.
- No gobierna aún todos los backlogs derivados del roadmap; queda para POST-H-009-D.
- No integra aún subgate `docs-governance` al `quality-gate hardening`; queda para POST-H-009-E.
- No usa LLM judge, red, APIs externas ni mutaciones de fuentes.
```

Estas capacidades quedan para `POST-H-009-C`, `POST-H-009-D` y `POST-H-009-E`.

## 16. Avance de implementación — POST-H-009-C

Estado: `implemented-initial`.

`POST-H-009-C — Sync validator Markdown ↔ JSON` amplía el validator ejecutable de gobernanza documental para detectar drift entre documentación humana y fuentes machine-readable críticas:

```text
python -m devpilot_core docs-governance validate --json
python -m devpilot_core docs-governance report --write-report --json
```

Artefactos implementados:

```text
src/devpilot_core/docs_governance/drift.py
tests/test_documentation_governance_sync.py
docs/audits/post_h_009_c_documentation_sync_validator_report.md
docs/post_h_009_c_manifest.json
```

Capacidades implementadas:

```text
- Regla version_match para roadmap Markdown ↔ JSON.
- Regla milestones_match para hitos POST-H-002..POST-H-025.
- Validación explícita de POST-H-024 y POST-H-025 en roadmap MD/JSON.
- Regla decisions_match para DEC-POSTH-* con validación explícita de DEC-POSTH-008 y DEC-POSTH-009.
- Regla closure_status_match entre manifest POST-H-EVAL-001 y closure report.
- Regla next_hito_match entre project_state y README/runbook/changelog.
- Reporte DocumentationGovernanceReport extendido con sync_checks.
- Comando alias docs-governance report para generar evidencia JSON/Markdown.
- Contrato TCR v1/v2 para DocumentationSyncValidator.
```

Criterios PASS cubiertos:

```text
PASS si markdown_json_sync_passed=true.
PASS si roadmap_markdown_json_sync_passed=true.
PASS si POST-H-024 y POST-H-025 aparecen sincronizados en roadmap MD/JSON.
PASS si DEC-POSTH-008 y DEC-POSTH-009 aparecen sincronizadas.
PASS si el reporte identifica source_path y counterpart_path por regla evaluada.
```

Límites de esta versión:

```text
- No gobierna aún todos los backlogs derivados del roadmap; queda para POST-H-009-D.
- No integra aún subgate docs-governance al quality-gate hardening; queda para POST-H-009-E.
- No usa LLM judge, red, APIs externas ni mutaciones de fuentes.
```

Estas capacidades quedan para `POST-H-009-D` y `POST-H-009-E`.

